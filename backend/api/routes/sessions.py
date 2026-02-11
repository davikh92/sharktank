from datetime import datetime, timezone
import random
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException

from auth import get_current_user
from dependencies import get_database
from models import (
    EventResponse,
    EventType,
    FounderActionRequest,
    MessageResponse,
    Offer,
    OfferStatus,
    OrchestratorResponse,
    PitchData,
    PitchEvaluation,
    SessionCreate,
    SessionResponse,
    SessionSharkResponse,
    SessionStatus,
    SharkState,
    UserMessageSubmit,
)
from orchestrator import Orchestrator
from pitch_evaluator import PitchEvaluator
from services.session_access_service import SessionAccessService
from shark_archetypes import get_all_archetypes, get_archetype_by_name

router = APIRouter(tags=['sessions'])


@router.post('/sessions', response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    session_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).isoformat()

    pitch_evaluator = PitchEvaluator()
    pitch_score = pitch_evaluator.evaluate(session_data.pitch.model_dump())
    pitch_evaluation = PitchEvaluation(
        originalidade=pitch_score.originalidade,
        potencial_mercado=pitch_score.potencial_mercado,
        diferencial_defensavel=pitch_score.diferencial_defensavel,
        clareza_problema=pitch_score.clareza_problema,
        modelo_negocio=pitch_score.modelo_negocio,
        idea_score=pitch_score.idea_score,
        idea_tier=pitch_score.idea_tier,
        offer_probability_multiplier=pitch_evaluator.get_offer_probability_multiplier(pitch_score),
    )

    all_archetypes = get_all_archetypes()
    if session_data.panel_selection:
        selected_archetypes = []
        for name in session_data.panel_selection:
            arch = get_archetype_by_name(name)
            if arch:
                selected_archetypes.append(arch)
        if len(selected_archetypes) != 4:
            raise HTTPException(status_code=400, detail='Deve selecionar exatamente 4 sharks')
    else:
        selected_archetypes = all_archetypes

    session_doc = {
        'id': session_id,
        'user_id': current_user['user_id'],
        'pitch': session_data.pitch.model_dump(),
        'pitch_evaluation': pitch_evaluation.model_dump(),
        'panel_selection': session_data.panel_selection,
        'reading_hints_enabled': session_data.reading_hints_enabled,
        'status': SessionStatus.PENDING,
        'created_at': created_at,
    }
    await db.sessions.insert_one(session_doc)

    sharks_response = []
    for archetype in selected_archetypes:
        shark_id = str(uuid.uuid4())
        initial_interest = pitch_evaluator.get_shark_initial_interest(pitch_score, archetype['id'])
        initial_interest = max(20, min(80, initial_interest))
        skepticism = pitch_evaluator.get_skepticism_level(pitch_score, 50)
        initial_state = SharkState(
            interest=initial_interest,
            confianca_ideia=pitch_score.idea_score,
            confianca_apresentacao=50.0,
            initial_interest=initial_interest,
            skepticism=skepticism,
            confianca=pitch_score.idea_score,
        )

        shark_doc = {
            'shark_id': shark_id,
            'session_id': session_id,
            'archetype_id': archetype['id'],
            'archetype_name': archetype['name'],
            'state': initial_state.model_dump(),
            'is_out': False,
        }
        await db.session_sharks.insert_one(shark_doc)
        sharks_response.append(
            SessionSharkResponse(
                shark_id=shark_id,
                archetype_name=archetype['name'],
                state=initial_state,
            )
        )

    await db.events.insert_one(
        {
            'id': str(uuid.uuid4()),
            'session_id': session_id,
            'event_type': EventType.SESSION_STARTED,
            'actor': 'SYSTEM',
            'timestamp': created_at,
            'data': {'pitch_evaluation': pitch_evaluation.model_dump()},
        }
    )
    await db.events.insert_one(
        {
            'id': str(uuid.uuid4()),
            'session_id': session_id,
            'event_type': EventType.PITCH_SUBMITTED,
            'actor': 'USER',
            'timestamp': created_at,
            'data': session_data.pitch.model_dump(),
        }
    )

    return SessionResponse(
        id=session_id,
        user_id=current_user['user_id'],
        pitch=session_data.pitch,
        panel_selection=session_data.panel_selection,
        reading_hints_enabled=session_data.reading_hints_enabled,
        status=SessionStatus.PENDING,
        created_at=created_at,
        sharks=sharks_response,
    )


@router.get('/sessions', response_model=List[SessionResponse])
async def list_sessions(current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    sessions = await db.sessions.find({'user_id': current_user['user_id']}, {'_id': 0}).sort('created_at', -1).to_list(100)
    result = []
    for session in sessions:
        sharks = await db.session_sharks.find({'session_id': session['id']}, {'_id': 0}).to_list(10)
        sharks_response = [
            SessionSharkResponse(
                shark_id=s['shark_id'],
                archetype_name=s['archetype_name'],
                state=SharkState(**s['state']),
            )
            for s in sharks
        ]
        result.append(
            SessionResponse(
                id=session['id'],
                user_id=session['user_id'],
                pitch=PitchData(**session['pitch']),
                panel_selection=session.get('panel_selection'),
                reading_hints_enabled=session.get('reading_hints_enabled', False),
                status=session['status'],
                created_at=session['created_at'],
                sharks=sharks_response,
            )
        )
    return result


@router.get('/sessions/{session_id}', response_model=SessionResponse)
async def get_session(session_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    session_access = SessionAccessService(db)
    session = await session_access.get_owned_session_or_404(session_id, current_user['user_id'])

    sharks = await db.session_sharks.find({'session_id': session_id}, {'_id': 0}).to_list(10)
    sharks_response = [
        SessionSharkResponse(
            shark_id=s['shark_id'],
            archetype_name=s['archetype_name'],
            state=SharkState(**s['state']),
        )
        for s in sharks
    ]

    return SessionResponse(
        id=session['id'],
        user_id=session['user_id'],
        pitch=PitchData(**session['pitch']),
        panel_selection=session.get('panel_selection'),
        reading_hints_enabled=session.get('reading_hints_enabled', False),
        status=session['status'],
        created_at=session['created_at'],
        sharks=sharks_response,
    )


@router.post('/sessions/{session_id}/start', response_model=OrchestratorResponse)
async def start_session(session_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    session_access = SessionAccessService(db)
    session = await session_access.get_owned_session_or_404(session_id, current_user['user_id'])

    await db.sessions.update_one(
        {'id': session_id},
        {'$set': {'status': SessionStatus.IN_PROGRESS, 'turn_count': 0, 'phase': 'exploration'}},
    )

    sharks = await db.session_sharks.find({'session_id': session_id}, {'_id': 0}).to_list(10)
    orchestrator = Orchestrator(db, session_id, session_id, session['pitch'], sharks, initial_turn_count=0, initial_phase='exploration')

    first_shark = random.choice(orchestrator.sharks)
    from orchestrator import MessageType

    context = f"Você está começando a avaliação do pitch: {session['pitch']['titulo']}. Faça uma pergunta inicial incisiva."
    first_question = await first_shark.generate_speech('QUESTION', context)

    message_id = str(uuid.uuid4())
    timestamp = datetime.now(timezone.utc).isoformat()
    message_doc = {
        'id': message_id,
        'session_id': session_id,
        'speaker': first_shark.archetype['name'],
        'content': first_question,
        'message_type': MessageType.QUESTION,
        'timestamp': timestamp,
    }
    await db.messages.insert_one(message_doc)
    await db.events.insert_one(
        {
            'id': str(uuid.uuid4()),
            'session_id': session_id,
            'event_type': EventType.QUESTION_ASKED,
            'actor': first_shark.archetype['name'],
            'timestamp': timestamp,
            'data': {'question': first_question},
        }
    )

    return OrchestratorResponse(
        messages=[MessageResponse(**message_doc)],
        events=[],
        session_status=SessionStatus.IN_PROGRESS,
        can_user_respond=True,
        reading_hint=None,
    )


@router.post('/sessions/{session_id}/respond', response_model=OrchestratorResponse)
async def respond_to_session(
    session_id: str,
    user_message: UserMessageSubmit,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    session_access = SessionAccessService(db)
    session = await session_access.get_owned_session_or_404(session_id, current_user['user_id'])
    if session['status'] != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail='Sessão não está em andamento')

    sharks = await db.session_sharks.find({'session_id': session_id}, {'_id': 0}).to_list(10)

    orchestrator = Orchestrator(
        db,
        session_id,
        session['pitch'],
        sharks,
        initial_turn_count=session.get('turn_count', 0),
        initial_phase=session.get('phase', 'exploration'),
        initial_session_phase=session.get('session_phase', 'PITCHING'),
        initial_negotiation_state=session.get('negotiation_state', None),
        pitch_evaluation=session.get('pitch_evaluation', None),
    )

    response = await orchestrator.process_user_answer(user_message.content)
    await db.sessions.update_one(
        {'id': session_id},
        {'$set': {'turn_count': orchestrator.turn_count, 'phase': orchestrator.phase, 'session_phase': orchestrator.session_phase.value}},
    )
    return response


@router.post('/sessions/{session_id}/founder-action', response_model=OrchestratorResponse)
async def process_founder_action(
    session_id: str,
    action_request: FounderActionRequest,
    current_user: dict = Depends(get_current_user),
    db=Depends(get_database),
):
    session_access = SessionAccessService(db)
    session = await session_access.get_owned_session_or_404(session_id, current_user['user_id'])
    if session['status'] != SessionStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail='Sessão não está em andamento')

    sharks = await db.session_sharks.find({'session_id': session_id}, {'_id': 0}).to_list(10)
    orchestrator = Orchestrator(
        db,
        session_id,
        session['pitch'],
        sharks,
        initial_turn_count=session.get('turn_count', 0),
        initial_phase=session.get('phase', 'exploration'),
        initial_session_phase=session.get('session_phase', 'PITCHING'),
        initial_negotiation_state=session.get('negotiation_state', None),
        pitch_evaluation=session.get('pitch_evaluation', None),
    )

    try:
        response = await orchestrator.process_founder_action(action_request)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error))

    await db.sessions.update_one(
        {'id': session_id},
        {'$set': {'turn_count': orchestrator.turn_count, 'phase': orchestrator.phase, 'session_phase': orchestrator.session_phase.value}},
    )
    return response


@router.get('/sessions/{session_id}/offers', response_model=List[Offer])
async def get_session_offers(session_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    session_access = SessionAccessService(db)
    await session_access.get_owned_session_or_404(session_id, current_user['user_id'])
    offers = await db.offers.find({'session_id': session_id, 'status': OfferStatus.ACTIVE}, {'_id': 0}).to_list(10)
    return [Offer(**offer) for offer in offers]


@router.get('/sessions/{session_id}/messages', response_model=List[MessageResponse])
async def get_session_messages(session_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    session_access = SessionAccessService(db)
    await session_access.get_owned_session_or_404(session_id, current_user['user_id'])
    messages = await db.messages.find({'session_id': session_id}, {'_id': 0}).sort('timestamp', 1).to_list(1000)
    return [MessageResponse(**message) for message in messages]


@router.get('/sessions/{session_id}/events', response_model=List[EventResponse])
async def get_session_events(session_id: str, current_user: dict = Depends(get_current_user), db=Depends(get_database)):
    session_access = SessionAccessService(db)
    await session_access.get_owned_session_or_404(session_id, current_user['user_id'])
    events = await db.events.find({'session_id': session_id}, {'_id': 0}).sort('timestamp', 1).to_list(1000)
    return [EventResponse(**event) for event in events]
