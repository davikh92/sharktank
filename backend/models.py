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

# === NOVOS ESTADOS GRANULARES DOS SHARKS ===
class SharkDisplayState(str, Enum):
    ACTIVE = "ACTIVE"                   # ● Neutro, aguardando
    INTERESTED = "INTERESTED"           # 👀 Interesse alto (> 70)
    SKEPTICAL = "SKEPTICAL"             # 🤨 Ceticismo (interesse < 40)
    WAITING_RESPONSE = "WAITING_RESPONSE"  # ⏳ Fez pergunta, aguarda resposta
    OFFER_MADE = "OFFER_MADE"           # 💰 Fez oferta ativa
    NEGOTIATING = "NEGOTIATING"         # 🤝 Em negociação
    LOSING_PATIENCE = "LOSING_PATIENCE" # ⚠️ Perdendo paciência
    LAST_CHANCE = "LAST_CHANCE"         # ⏱️ Última chance (Recovery Window)
    OUT = "OUT"                         # ✗ Saiu

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
    latent_decision: str = "ACTIVE"  # ACTIVE, INTERESTED, LEANING_OUT, OUT
    is_out: bool = False
    silent_turns: int = 0
    confianca: float = 50.0  # Confiança geral (legado)
    fadiga: float = 0.0      # Fadiga temporal
    response_memory_history: List[Dict[str, Any]] = []  # Histórico de respostas ponderadas
    conversation_memory: List[str] = []  # Histórico de conversa
    # === CAMPOS PARA NEGOCIAÇÃO ===
    has_active_offer: bool = False
    offer_id: Optional[str] = None
    # === CAMPOS PARA AVALIAÇÃO IDEIA vs APRESENTAÇÃO ===
    confianca_ideia: float = 50.0      # Baseado no pitch em si (piso)
    confianca_apresentacao: float = 50.0  # Baseado nas respostas
    initial_interest: float = 50.0     # Interesse inicial baseado na ideia
    saw_potential: bool = False        # Se "viu além" de apresentação ruim
    skepticism: str = "CONFIANTE"      # CONFIANTE, DESCONFIADO, CURIOSO
    shark_state_phase: str = "ACTIVE"  # ACTIVE, INTERESTED, OFFER_MADE, WAITING_RESPONSE, NEGOTIATING, DEAL_CLOSED, OUT
    # === ESTADOS GRANULARES E RECOVERY WINDOW ===
    display_state: str = "ACTIVE"       # Estado visual para UI
    in_recovery_window: bool = False    # Se está em janela de recuperação
    recovery_turns_remaining: int = 0   # Turnos restantes de recovery
    last_chance_given: bool = False     # Se já deu "última chance" (Operador)
    frustration_shown: bool = False     # Se já sinalizou frustração antes de sair

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

class PitchEvaluation(BaseModel):
    """Avaliação da ideia do pitch (separado da apresentação)"""
    originalidade: float = 50.0
    potencial_mercado: float = 50.0
    diferencial_defensavel: float = 50.0
    clareza_problema: float = 50.0
    modelo_negocio: float = 50.0
    idea_score: float = 50.0
    idea_tier: str = "MEDIANA"  # RUIM, FRACA, MEDIANA, FORTE, EXCEPCIONAL
    offer_probability_multiplier: float = 0.6

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
    # === NOVOS CAMPOS PARA NEGOCIAÇÃO ===
    session_phase: SessionPhase = SessionPhase.PITCHING
    active_offers: List[Offer] = []
    awaiting_founder_action: bool = False  # True quando há oferta ativa esperando decisão
    ending: Optional[Dict[str, Any]] = None  # Info do final cinematográfico

class ReportSection(BaseModel):
    titulo: str
    conteudo: Any

# === MODELO DE LEITURA DO SHARK NO RELATÓRIO ===
class SharkLeitura(BaseModel):
    """Leitura individual de um shark no relatório"""
    shark: str
    o_que_buscava: str
    o_que_pensou: str
    fez_oferta: bool = False
    oferta_retirada: bool = False
    fechou_deal: bool = False
    resultado: str
    interesse_final: float = 50.0
    confianca_ideia: float = 50.0
    confianca_apresentacao: float = 50.0

# === MODELO DE EVENTO NA LINHA DO TEMPO ===
class TimelineEvent(BaseModel):
    """Evento na linha do tempo da negociação"""
    turno: int
    tipo: str
    ator: str
    descricao: str

# === MODELO DE MOMENTO DE VIRADA ===
class MomentoVirada(BaseModel):
    """Momento de virada da sessão"""
    houve_virada: bool = False
    descricao: str = "A sessão seguiu sem grandes viradas."
    momento_chave: Optional[str] = None

# === MODELO DE AVALIAÇÃO IDEIA VS APRESENTAÇÃO ===
class AvaliacaoIdeia(BaseModel):
    """Avaliação comparativa entre ideia e apresentação"""
    idea_score: float = 50.0
    idea_tier: str = "MEDIANA"
    apresentacao_score: float = 50.0
    analise: str = ""
    recomendacao: str = ""
    componentes: Dict[str, float] = {}

# === MODELO DE AUTÓPSIA (ANÁLISE PROFUNDA) ===
class AutopsiaAnalise(BaseModel):
    """Análise profunda no estilo 'autópsia' da sessão"""
    momento_irreversivel: Optional[str] = None  # "Qual foi o momento irreversível?"
    primeiro_shark_perdido: Optional[str] = None  # "Qual shark você perdeu primeiro — e por quê?"
    pergunta_nao_respondida: Optional[str] = None  # "O que você nunca respondeu de verdade?"
    onde_perdeu_tracao: Optional[str] = None  # Onde perdeu força
    onde_ganhou_respeito: Optional[str] = None  # Onde ganhou credibilidade
    risco_desnecessario: Optional[str] = None  # Decisão arriscada desnecessária
    decisao_que_matou: Optional[str] = None  # Qual decisão "matou" o jogo (se aplicável)

# === MODELO DE MICRO-SINAL NÃO VERBAL ===
class MicroSinal(BaseModel):
    """Micro-sinal não verbal observado durante a sessão"""
    turno: int
    shark: str
    sinal: str  # Ex: "olhou o relógio", "anotou algo", "sorriso contido"
    traducao_psicologica: str  # Ex: "Perdi interesse", "Isso importa"

class ReportResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    session_id: str
    sintese: str
    linha_tempo: List[Dict[str, Any]]  # TimelineEvent como dict
    leitura_sharks: List[Dict[str, Any]]  # SharkLeitura como dict
    sinais_mesa: List[str]
    padroes_apresentador: List[str]
    pontos_sustentacao: List[str]
    veredito: str
    momento_virada: Optional[Dict[str, Any]] = None  # MomentoVirada como dict
    # === NOVOS CAMPOS DO "RELATÓRIO COMO REPLAY" ===
    pergunta_provocativa: Optional[str] = None
    avaliacao_idea: Optional[Dict[str, Any]] = None  # AvaliacaoIdeia como dict
    # === NOVOS CAMPOS DA "AUTÓPSIA" ===
    autopsia: Optional[Dict[str, Any]] = None  # AutopsiaAnalise como dict
    micro_sinais: Optional[List[Dict[str, Any]]] = None  # Lista de MicroSinal
    generated_at: str