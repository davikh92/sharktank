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
    SESSION_ENDED = "SESSION_ENDED"
    REPORT_GENERATED = "REPORT_GENERATED"

class SessionStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"

class MessageType(str, Enum):
    PITCH = "PITCH"
    QUESTION = "QUESTION"
    ANSWER = "ANSWER"
    COMMENT = "COMMENT"
    INTERRUPTION = "INTERRUPTION"
    OUT_ANNOUNCEMENT = "OUT_ANNOUNCEMENT"
    OFFER = "OFFER"

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