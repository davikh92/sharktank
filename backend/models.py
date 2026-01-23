from pydantic import BaseModel, Field, EmailStr, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

class EventType(str, Enum):
    SESSION_STARTED = "SESSION_STARTED"
    PITCH_SUBMITTED = "PITCH_SUBMITTED"
    QUESTION_ASKED = "QUESTION_ASKED"
    ANSWER_RECEIVED = "ANSWER_RECEIVED"
    ANSWER_EVASIVE = "ANSWER_EVASIVE"
    PITCH_INTERRUPTED = "PITCH_INTERRUPTED"
    SHARK_SILENT = "SHARK_SILENT"
    SHARK_COMMENT_LATERAL = "SHARK_COMMENT_LATERAL"
    SHARK_OUT = "SHARK_OUT"
    SHARK_OFFER = "SHARK_OFFER"
    SHARK_OFFER_WITHDRAWN = "SHARK_OFFER_WITHDRAWN"
    SHARK_OFFER_IMPROVED = "SHARK_OFFER_IMPROVED"
    SHARK_CONFLICT = "SHARK_CONFLICT"
    FOUNDER_ACCEPTED = "FOUNDER_ACCEPTED"
    FOUNDER_REJECTED = "FOUNDER_REJECTED"
    FOUNDER_COUNTERED = "FOUNDER_COUNTERED"
    FOUNDER_WAITED = "FOUNDER_WAITED"
    DEAL_CLOSED = "DEAL_CLOSED"
    NEGOTIATION_STARTED = "NEGOTIATION_STARTED"
    NEGOTIATION_ENDED = "NEGOTIATION_ENDED"
    SESSION_ENDED = "SESSION_ENDED"
    REPORT_GENERATED = "REPORT_GENERATED"

class SessionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

# === NOVOS ENUMS PARA NEGOCIAÇÃO ===

class SessionPhase(str, Enum):
    PITCHING = "PITCHING"              # Perguntas normais
    NEGOTIATION_WINDOW = "NEGOTIATION_WINDOW"  # Oferta na mesa, founder decide
    CLOSING = "CLOSING"                # Encerramento

class OfferType(str, Enum):
    ALIGNED = "ALIGNED"      # Próximo do pedido (500k/10% → 500k/12%)
    AGGRESSIVE = "AGGRESSIVE"  # Mesmo valor, mais equity (500k/25%)
    CREATIVE = "CREATIVE"    # Valor diferente (300k/15% ou 700k/25%)

class OfferStatus(str, Enum):
    ACTIVE = "ACTIVE"
    WITHDRAWN = "WITHDRAWN"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    COUNTERED = "COUNTERED"

class FounderAction(str, Enum):
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"
    COUNTER = "COUNTER"
    WAIT = "WAIT"

class EndingType(str, Enum):
    DEAL_CLOSED = "DEAL_CLOSED"        # 🎉 Acordo fechado
    DEAL_BITTER = "DEAL_BITTER"        # ⚖️ Acordo amargo
    NO_DEAL = "NO_DEAL"                # ❌ Sem investimento
    TABLE_BROKEN = "TABLE_BROKEN"      # 🔥 Mesa quebrada (tinha oferta, perdeu)

class MessageType(str, Enum):
    PITCH = "PITCH"
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    COMMENT = "COMMENT"
    INTERRUPTION = "INTERRUPTION"
    OUT_ANNOUNCEMENT = "OUT_ANNOUNCEMENT"
    OFFER = "OFFER"
    OFFER_PRESSURE = "OFFER_PRESSURE"      # Shark pressionando por resposta
    OFFER_WITHDRAWN = "OFFER_WITHDRAWN"    # Shark retirando oferta
    COUNTER_OFFER = "COUNTER_OFFER"        # Founder fez contra-proposta
    SHARK_REACTION = "SHARK_REACTION"      # Reação a ação do founder
    SHARK_CONFLICT = "SHARK_CONFLICT"      # Sharks comentando ofertas entre si
    DEAL_ANNOUNCEMENT = "DEAL_ANNOUNCEMENT"  # Anúncio de acordo
    NARRATION = "NARRATION"                # Narração cinematográfica

class UserRegister(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    created_at: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class PitchData(BaseModel):
    titulo: str
    problema: str
    solucao: str
    mercado: str
    modelo_negocio: str
    tracao: str
    pedido_valor: Optional[str] = None
    pedido_equity: Optional[str] = None

class SessionCreate(BaseModel):
    pitch: PitchData
    panel_selection: Optional[List[str]] = None  # None = random, or list of 4 shark names
    reading_hints_enabled: bool = False

class SharkState(BaseModel):
    interest: float = 50.0  # 0-100
    patience: float = 100.0  # 0-100
    trust_founder: float = 50.0  # 0-100
    risk_appetite: float = 50.0  # 0-100
    latent_decision: str = "ACTIVE"  # ACTIVE, LEANING_OUT, OUT
    is_out: bool = False
    silent_turns: int = 0
    confianca: float = 50.0  # Confiança implícita
    fadiga: float = 0.0      # Fadiga temporal
    response_memory_history: List[Dict[str, Any]] = []  # Histórico de respostas ponderadas
    conversation_memory: List[str] = []  # Histórico de conversa
    # === NOVOS CAMPOS PARA NEGOCIAÇÃO ===
    has_active_offer: bool = False
    offer_id: Optional[str] = None

# === MODELOS DE OFERTA ===

class Offer(BaseModel):
    """Representa uma oferta de um shark"""
    id: str
    shark_id: str
    shark_name: str
    session_id: str
    offer_type: OfferType
    valor: str           # Ex: "R$ 500.000"
    equity: str          # Ex: "15%"
    conditions: Optional[str] = None  # Condições especiais
    status: OfferStatus = OfferStatus.ACTIVE
    turns_remaining: int = 2  # Validade em turnos (1-3)
    created_at_turn: int
    withdrawn_at_turn: Optional[int] = None

class CounterOffer(BaseModel):
    """Contra-proposta do founder"""
    offer_id: str  # ID da oferta original
    valor: str
    equity: str
    message: Optional[str] = None

class FounderActionRequest(BaseModel):
    """Ação do founder em resposta a uma oferta"""
    action: FounderAction
    offer_id: str  # ID da oferta alvo
    counter_offer: Optional[CounterOffer] = None  # Se action == COUNTER

class NegotiationState(BaseModel):
    """Estado da janela de negociação"""
    is_active: bool = False
    active_offers: List[Offer] = []
    deals_closed: List[Dict[str, Any]] = []
    turns_in_negotiation: int = 0
    ending_type: Optional[EndingType] = None

class SessionSharkResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    shark_id: str
    archetype_name: str
    state: SharkState

class MessageResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    session_id: str
    speaker: str  # "USER" or shark archetype name
    content: str
    message_type: MessageType
    timestamp: str

class EventResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    session_id: str
    event_type: EventType
    actor: str
    timestamp: str
    data: Dict[str, Any]

class SessionResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    user_id: str
    pitch: PitchData
    panel_selection: Optional[List[str]]
    reading_hints_enabled: bool
    status: SessionStatus
    created_at: str
    sharks: List[SessionSharkResponse]

class UserMessageSubmit(BaseModel):
    content: str

class OrchestratorResponse(BaseModel):
    messages: List[MessageResponse]
    events: List[EventResponse]
    session_status: SessionStatus
    can_user_respond: bool
    reading_hint: Optional[str] = None

class ReportSection(BaseModel):
    titulo: str
    conteudo: Any

class ReportResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    session_id: str
    sintese: str
    linha_tempo: List[Dict[str, str]]
    leitura_sharks: List[Dict[str, Any]]
    sinais_mesa: List[str]
    padroes_apresentador: List[str]
    pontos_sustentacao: List[str]
    veredito: str
    momento_virada: Optional[Dict[str, Any]] = None
    generated_at: str