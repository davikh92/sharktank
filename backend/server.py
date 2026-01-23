from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime, timezone
import random

from models import (
    UserRegister, UserLogin, TokenResponse, UserResponse,
    SessionCreate, SessionResponse, SessionStatus, SharkState,
    UserMessageSubmit, OrchestratorResponse,
    MessageResponse, EventResponse, ReportResponse,
    EventType, SessionSharkResponse, SessionPhase,
    FounderActionRequest, Offer, OfferStatus, PitchEvaluation
)
from auth import hash_password, verify_password, create_access_token, get_current_user
from shark_archetypes import get_all_archetypes, get_archetype_by_name
from orchestrator import Orchestrator
from report_generator import ReportGenerator
from pitch_evaluator import PitchEvaluator, PitchScore

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI(title="Investor Panel Simulator")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# ============= AUTH ENDPOINTS =============

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserRegister):
    # Verificar se usuário já existe
    existing_user = await db.users.find_one({"email": user_data.email}, {"_id": 0})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email já cadastrado")
    
    # Criar usuário
    user_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    user_doc = {
        "id": user_id,
        "email": user_data.email,
        "password_hash": hash_password(user_data.password),
        "created_at": created_at
    }
    
    await db.users.insert_one(user_doc)
    
    # Criar token
    token = create_access_token({"user_id": user_id, "email": user_data.email})
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(id=user_id, email=user_data.email, created_at=created_at)
    )

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    # Buscar usuário
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Verificar senha
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Credenciais inválidas")
    
    # Criar token
    token = create_access_token({"user_id": user['id'], "email": user['email']})
    
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse(id=user['id'], email=user['email'], created_at=user['created_at'])
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    user = await db.users.find_one({"id": current_user['user_id']}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return UserResponse(id=user['id'], email=user['email'], created_at=user['created_at'])

# ============= SHARK ARCHETYPES =============

@api_router.get("/sharks")
async def get_sharks():
    return {"sharks": get_all_archetypes()}

# ============= SESSION ENDPOINTS =============

@api_router.post("/sessions", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: dict = Depends(get_current_user)
):
    session_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()
    
    # === AVALIAR O PITCH (IDEIA vs APRESENTAÇÃO) ===
    pitch_evaluator = PitchEvaluator()
    pitch_score = pitch_evaluator.evaluate(session_data.pitch.model_dump())
    
    # Criar objeto de avaliação para persistir
    pitch_evaluation = PitchEvaluation(
        originalidade=pitch_score.originalidade,
        potencial_mercado=pitch_score.potencial_mercado,
        diferencial_defensavel=pitch_score.diferencial_defensavel,
        clareza_problema=pitch_score.clareza_problema,
        modelo_negocio=pitch_score.modelo_negocio,
        idea_score=pitch_score.idea_score,
        idea_tier=pitch_score.idea_tier,
        offer_probability_multiplier=pitch_evaluator.get_offer_probability_multiplier(pitch_score)
    )
    
    # Selecionar painel de sharks
    all_archetypes = get_all_archetypes()
    
    if session_data.panel_selection:
        # Usuário escolheu sharks específicos
        selected_archetypes = []
        for name in session_data.panel_selection:
            arch = get_archetype_by_name(name)
            if arch:
                selected_archetypes.append(arch)
        
        if len(selected_archetypes) != 4:
            raise HTTPException(status_code=400, detail="Deve selecionar exatamente 4 sharks")
    else:
        # Random (todos os 4)
        selected_archetypes = all_archetypes
    
    # Criar sessão com avaliação do pitch
    session_doc = {
        "id": session_id,
        "user_id": current_user['user_id'],
        "pitch": session_data.pitch.model_dump(),
        "pitch_evaluation": pitch_evaluation.model_dump(),  # NOVO
        "panel_selection": session_data.panel_selection,
        "reading_hints_enabled": session_data.reading_hints_enabled,
        "status": SessionStatus.PENDING,
        "created_at": created_at
    }
    
    await db.sessions.insert_one(session_doc)
    
    # Criar sharks da sessão COM interesse inicial baseado na IDEIA
    sharks_response = []
    for archetype in selected_archetypes:
        shark_id = str(uuid.uuid4())
        
        # Calcular interesse inicial baseado na IDEIA
        initial_interest = pitch_evaluator.get_shark_initial_interest(pitch_score, archetype['id'])
        initial_interest = max(20, min(80, initial_interest))  # Limitar entre 20-80
        
        # Determinar ceticismo inicial
        skepticism = pitch_evaluator.get_skepticism_level(pitch_score, 50)  # 50 = apresentação neutra inicial
        
        # Criar estado inicial com scores da IDEIA
        initial_state = SharkState(
            interest=initial_interest,
            confianca_ideia=pitch_score.idea_score,
            confianca_apresentacao=50.0,  # Começa neutro, muda com respostas
            initial_interest=initial_interest,
            skepticism=skepticism,
            confianca=pitch_score.idea_score  # Confiança geral começa igual à ideia
        )
        
        shark_doc = {
            "shark_id": shark_id,
            "session_id": session_id,
            "archetype_id": archetype['id'],
            "archetype_name": archetype['name'],
            "state": initial_state.model_dump(),
            "is_out": False
        }
        
        await db.session_sharks.insert_one(shark_doc)
        
        sharks_response.append(SessionSharkResponse(
            shark_id=shark_id,
            archetype_name=archetype['name'],
            state=initial_state
        ))
    
    # Criar evento SESSION_STARTED
    await db.events.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "event_type": EventType.SESSION_STARTED,
        "actor": "SYSTEM",
        "timestamp": created_at,
        "data": {
            "pitch_evaluation": pitch_evaluation.model_dump()
        }
    })
    
    # Criar evento PITCH_SUBMITTED
    await db.events.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "event_type": EventType.PITCH_SUBMITTED,
        "actor": "USER",
        "timestamp": created_at,
        "data": session_data.pitch.model_dump()
    })
    
    return SessionResponse(
        id=session_id,
        user_id=current_user['user_id'],
        pitch=session_data.pitch,
        panel_selection=session_data.panel_selection,
        reading_hints_enabled=session_data.reading_hints_enabled,
        status=SessionStatus.PENDING,
        created_at=created_at,
        sharks=sharks_response
    )

@api_router.get("/sessions", response_model=List[SessionResponse])
async def list_sessions(current_user: dict = Depends(get_current_user)):
    sessions = await db.sessions.find(
        {"user_id": current_user['user_id']},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    result = []
    for session in sessions:
        sharks = await db.session_sharks.find(
            {"session_id": session['id']},
            {"_id": 0}
        ).to_list(10)
        
        sharks_response = [
            SessionSharkResponse(
                shark_id=s['shark_id'],
                archetype_name=s['archetype_name'],
                state=SharkState(**s['state'])
            )
            for s in sharks
        ]
        
        from models import PitchData
        result.append(SessionResponse(
            id=session['id'],
            user_id=session['user_id'],
            pitch=PitchData(**session['pitch']),
            panel_selection=session.get('panel_selection'),
            reading_hints_enabled=session.get('reading_hints_enabled', False),
            status=session['status'],
            created_at=session['created_at'],
            sharks=sharks_response
        ))
    
    return result

@api_router.get("/sessions/{session_id}", response_model=SessionResponse)
async def get_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    sharks = await db.session_sharks.find(
        {"session_id": session_id},
        {"_id": 0}
    ).to_list(10)
    
    sharks_response = [
        SessionSharkResponse(
            shark_id=s['shark_id'],
            archetype_name=s['archetype_name'],
            state=SharkState(**s['state'])
        )
        for s in sharks
    ]
    
    from models import PitchData
    return SessionResponse(
        id=session['id'],
        user_id=session['user_id'],
        pitch=PitchData(**session['pitch']),
        panel_selection=session.get('panel_selection'),
        reading_hints_enabled=session.get('reading_hints_enabled', False),
        status=session['status'],
        created_at=session['created_at'],
        sharks=sharks_response
    )

# ============= CONVERSATION / ORCHESTRATOR =============

@api_router.post("/sessions/{session_id}/start", response_model=OrchestratorResponse)
async def start_session(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    # Atualizar status para IN_PROGRESS e inicializar turn_count e phase
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "status": SessionStatus.IN_PROGRESS,
            "turn_count": 0,
            "phase": "exploration"
        }}
    )
    
    # Buscar sharks
    sharks = await db.session_sharks.find({"session_id": session_id}, {"_id": 0}).to_list(10)
    
    # Criar orquestrador
    orchestrator = Orchestrator(
        db, 
        session_id, 
        session['pitch'], 
        sharks,
        initial_turn_count=0,
        initial_phase="exploration"
    )
    
    # Gerar primeira pergunta de um shark aleatório
    first_shark = random.choice(orchestrator.sharks)
    
    from orchestrator import MessageType
    context = f"Você está começando a avaliação do pitch: {session['pitch']['titulo']}. Faça uma pergunta inicial incisiva."
    first_question = await first_shark.generate_speech("QUESTION", context)
    
    # Salvar primeira mensagem
    message_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    
    message_doc = {
        "id": message_id,
        "session_id": session_id,
        "speaker": first_shark.archetype['name'],
        "content": first_question,
        "message_type": MessageType.QUESTION,
        "timestamp": timestamp
    }
    
    await db.messages.insert_one(message_doc)
    
    # Criar evento
    await db.events.insert_one({
        "id": str(uuid.uuid4()),
        "session_id": session_id,
        "event_type": EventType.QUESTION_ASKED,
        "actor": first_shark.archetype['name'],
        "timestamp": timestamp,
        "data": {"question": first_question}
    })
    
    return OrchestratorResponse(
        messages=[MessageResponse(**message_doc)],
        events=[],
        session_status=SessionStatus.IN_PROGRESS,
        can_user_respond=True,
        reading_hint=None
    )

@api_router.post("/sessions/{session_id}/respond", response_model=OrchestratorResponse)
async def respond_to_session(
    session_id: str,
    user_message: UserMessageSubmit,
    current_user: dict = Depends(get_current_user)
):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    if session['status'] != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Sessão não está em andamento")
    
    # Buscar sharks
    sharks = await db.session_sharks.find({"session_id": session_id}, {"_id": 0}).to_list(10)
    
    # Carregar estado persistido da sessão
    current_turn_count = session.get('turn_count', 0)
    current_phase = session.get('phase', 'exploration')
    current_session_phase = session.get('session_phase', 'PITCHING')
    negotiation_state = session.get('negotiation_state', None)
    pitch_evaluation = session.get('pitch_evaluation', None)  # NOVO
    
    # Criar orquestrador COM estado existente
    orchestrator = Orchestrator(
        db, 
        session_id, 
        session['pitch'], 
        sharks,
        initial_turn_count=current_turn_count,
        initial_phase=current_phase,
        initial_session_phase=current_session_phase,
        initial_negotiation_state=negotiation_state,
        pitch_evaluation=pitch_evaluation  # NOVO
    )
    
    # Processar resposta
    response = await orchestrator.process_user_answer(user_message.content)
    
    # Persistir estado atualizado na sessão
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "turn_count": orchestrator.turn_count,
            "phase": orchestrator.phase,
            "session_phase": orchestrator.session_phase.value
        }}
    )
    
    return response

# ============= FOUNDER ACTION ENDPOINT (NEGOCIAÇÃO) =============

@api_router.post("/sessions/{session_id}/founder-action", response_model=OrchestratorResponse)
async def process_founder_action(
    session_id: str,
    action_request: FounderActionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Processa a ação do founder em resposta a uma oferta"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    if session['status'] != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Sessão não está em andamento")
    
    # Buscar sharks
    sharks = await db.session_sharks.find({"session_id": session_id}, {"_id": 0}).to_list(10)
    
    # Carregar estado persistido
    current_turn_count = session.get('turn_count', 0)
    current_phase = session.get('phase', 'exploration')
    current_session_phase = session.get('session_phase', 'PITCHING')
    negotiation_state = session.get('negotiation_state', None)
    pitch_evaluation = session.get('pitch_evaluation', None)  # NOVO
    
    # Criar orquestrador
    orchestrator = Orchestrator(
        db, 
        session_id, 
        session['pitch'], 
        sharks,
        initial_turn_count=current_turn_count,
        initial_phase=current_phase,
        initial_session_phase=current_session_phase,
        initial_negotiation_state=negotiation_state,
        pitch_evaluation=pitch_evaluation  # NOVO
    )
    
    # Processar ação do founder
    try:
        response = await orchestrator.process_founder_action(action_request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    # Persistir estado atualizado
    await db.sessions.update_one(
        {"id": session_id},
        {"$set": {
            "turn_count": orchestrator.turn_count,
            "phase": orchestrator.phase,
            "session_phase": orchestrator.session_phase.value
        }}
    )
    
    return response

# ============= OFFERS ENDPOINT =============

@api_router.get("/sessions/{session_id}/offers", response_model=List[Offer])
async def get_session_offers(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Retorna ofertas ativas da sessão"""
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    offers = await db.offers.find(
        {"session_id": session_id, "status": OfferStatus.ACTIVE},
        {"_id": 0}
    ).to_list(10)
    
    return [Offer(**o) for o in offers]

@api_router.get("/sessions/{session_id}/messages", response_model=List[MessageResponse])
async def get_session_messages(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    messages = await db.messages.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    return [MessageResponse(**m) for m in messages]

@api_router.get("/sessions/{session_id}/events", response_model=List[EventResponse])
async def get_session_events(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    events = await db.events.find(
        {"session_id": session_id},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)
    
    return [EventResponse(**e) for e in events]

# ============= REPORTS =============

@api_router.post("/sessions/{session_id}/report", response_model=ReportResponse)
async def generate_report(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    if session['status'] != SessionStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Sessão ainda não foi concluída")
    
    # Verificar se já existe relatório
    existing_report = await db.reports.find_one({"session_id": session_id}, {"_id": 0})
    if existing_report:
        return ReportResponse(**existing_report)
    
    # Gerar novo relatório
    generator = ReportGenerator(db, session_id)
    report = await generator.generate_report()
    
    return report

@api_router.get("/sessions/{session_id}/report", response_model=ReportResponse)
async def get_report(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session = await db.sessions.find_one({"id": session_id}, {"_id": 0})
    if not session:
        raise HTTPException(status_code=404, detail="Sessão não encontrada")
    
    if session['user_id'] != current_user['user_id']:
        raise HTTPException(status_code=403, detail="Acesso negado")
    
    report = await db.reports.find_one({"session_id": session_id}, {"_id": 0})
    if not report:
        raise HTTPException(status_code=404, detail="Relatório não encontrado")
    
    return ReportResponse(**report)

# ============= ROOT ENDPOINT =============

@api_router.get("/")
async def root():
    return {"message": "Investor Panel Simulator API"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()