import random
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
import uuid
from models import (
    EventType, MessageType, SessionStatus, SharkState,
    MessageResponse, EventResponse, OrchestratorResponse,
    SessionPhase, Offer, OfferType, OfferStatus, FounderAction,
    EndingType, NegotiationState, CounterOffer, FounderActionRequest
)
from shark_archetypes import get_archetype_by_id
from negotiation_manager import NegotiationManager
import os
from dotenv import load_dotenv
from emergentintegrations.llm.chat import LlmChat, UserMessage
import asyncio

load_dotenv()

EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

class ResponseMemory:
    """Memória ponderada de respostas"""
    def __init__(self):
        self.history: List[Dict[str, Any]] = []
    
    def add_response(self, quality: int, details: Dict[str, Any]):
        """Adiciona resposta com peso inicial 1.0"""
        self.history.append({
            'quality': quality,  # -1, 0, +1
            'peso': 1.0,
            'details': details
        })
    
    def decay_weights(self):
        """Aplica decaimento suave em todos os pesos"""
        for item in self.history:
            item['peso'] *= 0.85
    
    def get_pattern_score(self) -> float:
        """Calcula score de padrão ponderado"""
        if not self.history:
            return 0.0
        return sum(item['quality'] * item['peso'] for item in self.history)
    
    def get_recent_trend(self, n: int = 3) -> float:
        """Pega tendência das últimas N respostas"""
        recent = self.history[-n:] if len(self.history) >= n else self.history
        if not recent:
            return 0.0
        return sum(item['quality'] for item in recent) / len(recent)

class SharkAgent:
    def __init__(self, shark_id: str, archetype_data: Dict[str, Any], session_context: str, initial_state: Optional[SharkState] = None):
        self.shark_id = shark_id
        self.archetype = archetype_data
        self.state = initial_state if initial_state else SharkState()
        self.session_context = session_context
        
        # CARREGAR memória de conversa do state persistido
        self.conversation_memory: List[str] = self.state.conversation_memory.copy() if self.state.conversation_memory else []
        
        # Nova camada: memória ponderada - CARREGAR do state persistido
        self.response_memory = ResponseMemory()
        if self.state.response_memory_history:
            self.response_memory.history = self.state.response_memory_history.copy()
        
        # Usar valores do state se fornecido
        self.confianca = self.state.confianca
        self.fadiga = self.state.fadiga
        
    def _evaluate_response_quality(self, answer: str, answer_analysis: Dict[str, Any]) -> int:
        """
        Avalia qualidade do conteúdo (não forma)
        Retorna: -1 (fraco), 0 (neutro), +1 (bom)
        """
        score = 0
        
        # Análise por arquétipo
        if self.archetype['id'] == 'financeiro':
            if answer_analysis.get('has_numbers'):
                score += 1
            if answer_analysis.get('is_evasive'):
                score -= 1
                
        elif self.archetype['id'] == 'operador':
            if answer_analysis.get('is_direct'):
                score += 1
            if answer_analysis.get('is_evasive'):
                score -= 1
                
        elif self.archetype['id'] == 'cetico':
            if answer_analysis.get('has_differentiation', False):
                score += 1
            if answer_analysis.get('is_generic', True):
                score -= 1
                
        elif self.archetype['id'] == 'visionario':
            if answer_analysis.get('has_vision'):
                score += 1
        
        # Normalizar para -1, 0, +1
        if score >= 1:
            return 1
        elif score <= -1:
            return -1
        return 0
    
    def _detect_contradiction(self, current_answer: str) -> bool:
        """Detecta contradições com respostas anteriores"""
        # Simplificado: em produção usaria embedding similarity
        if len(self.conversation_memory) < 2:
            return False
        
        # Heurística simples: palavras conflitantes
        conflict_pairs = [
            (['sim', 'temos'], ['não', 'ainda']),
            (['já', 'implementado'], ['vamos', 'pretendemos']),
        ]
        
        current_lower = current_answer.lower()
        for prev in self.conversation_memory[-3:]:
            prev_lower = prev.lower()
            for positive, negative in conflict_pairs:
                has_positive_prev = any(word in prev_lower for word in positive)
                has_negative_current = any(word in current_lower for word in negative)
                if has_positive_prev and has_negative_current:
                    return True
        
        return False
    
    def _detect_critical_event(self, answer: str, answer_analysis: Dict[str, Any]) -> Optional[str]:
        """
        Detecta eventos críticos que mudam trajetória
        Retorna tipo do evento ou None
        """
        # Pedido claro e bem defendido
        if 'pedido' in answer.lower() and answer_analysis.get('has_numbers'):
            return 'PEDIDO_FORTE'
        
        # Insight único ou diferenciado
        keywords_insight = ['inovação', 'único', 'exclusivo', 'patenteado', 'propriedade']
        if any(kw in answer.lower() for kw in keywords_insight):
            return 'INSIGHT_UNICO'
        
        # Contradição grave
        if self._detect_contradiction(answer):
            return 'CONTRADICAO_GRAVE'
        
        # Clareza excepcional
        if (answer_analysis.get('is_direct') and 
            answer_analysis.get('has_numbers') and 
            not answer_analysis.get('is_evasive')):
            return 'PITCH_CLEAR'
        
        return None
    
    def update_state_from_answer(self, answer: str, answer_analysis: Dict[str, Any], turn_count: int):
        """
        Atualiza estado usando modelo híbrido
        Não reage ao último turno - reage à história que está se formando
        """
        # Salvar na memória de conversa
        self.conversation_memory.append(answer)
        
        # CAMADA 1: Desgaste natural - BALANCEADO (+15-20%)
        desgaste = 6.0  # Era 5.0
        if self.archetype['id'] == 'operador':
            desgaste = 8.0  # Era 7.0
        elif self.archetype['id'] == 'financeiro':
            desgaste = 7.0  # Era 6.0
        elif self.archetype['id'] == 'cetico':
            desgaste = 7.5  # Era 6.5
        
        self.state.patience -= desgaste
        self.fadiga += (turn_count * 1.2)  # Era 1.0
        
        # CAMADA 2: Memória ponderada
        self.response_memory.decay_weights()
        
        quality = self._evaluate_response_quality(answer, answer_analysis)
        self.response_memory.add_response(quality, answer_analysis)
        
        pattern_score = self.response_memory.get_pattern_score()
        recent_trend = self.response_memory.get_recent_trend(3)
        
        # CAMADA 3: Confiança implícita - MAIS AGRESSIVA
        if quality == 1:
            self.confianca += 2.0  # Diminuído de 3.0
        elif quality == -1:
            self.confianca -= 8.0  # Aumentado de 5.0
        
        # Contradições devastam
        if self._detect_contradiction(answer):
            self.confianca -= 25.0  # Aumentado de 15.0
        
        # Padrão consistente
        if pattern_score > 2.0:
            self.confianca += 1.5  # Diminuído de 2.0
        elif pattern_score < -2.0:
            self.confianca -= 5.0  # Aumentado de 3.0
        
        # CAMADA 4: Eventos críticos (não aditivos)
        critical_event = self._detect_critical_event(answer, answer_analysis)
        
        if critical_event == 'PEDIDO_FORTE':
            self.state.interest += 15
            self.confianca += 20
        elif critical_event == 'INSIGHT_UNICO':
            self.state.interest += 10
            self.confianca += 10
        elif critical_event == 'CONTRADICAO_GRAVE':
            self.confianca -= 40
            self.state.patience -= 25
        elif critical_event == 'PITCH_CLEAR':
            self.state.interest += 8
            self.confianca += 12
        
        # CAMADA 5: Impacto modulado pela confiança
        # Alta confiança perdoa forma ruim, baixa amplifica erros
        confidence_multiplier = 1 - (self.confianca / 120.0)  # 0.0 a 0.83
        
        # Penalidades moduladas
        if answer_analysis.get('is_evasive'):
            penalty = 15 * (1 + confidence_multiplier)
            self.state.patience -= penalty
        
        # Tendência recente negativa é preocupante
        if recent_trend < -0.5:
            self.state.interest -= (10 * (1 + confidence_multiplier))
        elif recent_trend > 0.5:
            self.state.interest += (5 * (1 - confidence_multiplier))
        
        # Limites
        self.state.interest = max(0, min(100, self.state.interest))
        self.state.patience = max(0, min(100, self.state.patience))
        self.confianca = max(0, min(100, self.confianca))
        
        # Sincronizar com state (incluindo memória para persistência)
        self.state.confianca = self.confianca
        self.state.fadiga = self.fadiga
        self.state.response_memory_history = self.response_memory.history.copy()
        self.state.conversation_memory = self.conversation_memory.copy()
        
        # Ajustar decisão latente baseado em saúde composta
        self._update_latent_decision()
            
    def _update_latent_decision(self):
        """Atualiza decisão latente baseado em saúde composta"""
        health = self._calculate_health()
        
        # THRESHOLDS BALANCEADOS
        if health < 30:  # Era 35
            self.state.latent_decision = "OUT"
        elif health < 58:  # Era 55 - ajuste leve
            self.state.latent_decision = "LEANING_OUT"
        else:
            self.state.latent_decision = "ACTIVE"
    
    def _calculate_health(self) -> float:
        """
        Calcula saúde composta do shark
        Não é só pontos - é interesse + paciência + confiança - fadiga
        """
        health = (
            self.state.interest * 0.4 +
            self.state.patience * 0.3 +
            self.confianca * 0.3
        ) - (self.fadiga * 0.2)
        
        return max(0, min(100, health))
    
    def should_interrupt(self, turn_count: int) -> bool:
        """Decide se o shark deve interromper"""
        if self.state.is_out:
            return False
            
        # Cético interrompe mais
        if self.archetype['id'] == 'cetico':
            return random.random() < 0.25
        # Operador interrompe se perder paciência
        elif self.archetype['id'] == 'operador' and self.state.patience < 60:
            return random.random() < 0.20
            
        return random.random() < 0.10
        
    def should_go_silent(self) -> bool:
        """Decide se o shark fica em silêncio"""
        if self.state.is_out:
            return True
        if self.state.interest < 30:
            return random.random() < 0.30
        return random.random() < 0.15
        
    def should_go_out(self, turn_count: int) -> bool:
        """
        Decide se o shark deve sair
        NUNCA 100% (exceto paciência crítica ou contradição grave)
        """
        if self.state.is_out:
            return False
        
        # PROTEÇÃO: Shark com interesse muito alto NÃO sai por exaustão
        # Interesse > 80 = muito interessado, não vai desistir fácil
        if self.state.interest >= 80 and self.confianca >= 50:
            # Só sai se paciência for CRÍTICA (< 5)
            if self.state.patience < 5:
                return random.random() < 0.30  # Mesmo assim só 30%
            return False
        
        # Primeiros 4 turnos: proteção
        if turn_count <= 4:
            if self.state.latent_decision == "OUT":
                return random.random() < 0.15
            return False
        
        # DETERMINÍSTICO: Apenas em casos EXTREMOS
        # 1. Paciência crítica (< 5) E interesse baixo
        if self.state.patience < 5 and self.state.interest < 60:
            return True
        
        # 2. Contradição grave detectada recentemente
        if self.confianca < 15 and self.state.latent_decision == "OUT":
            return random.random() < 0.95  # 95%, não 100%
        
        # Calcular saúde composta
        health = self._calculate_health()
        
        # Decisão OUT: alta probabilidade mas não garantida
        if self.state.latent_decision == "OUT":
            # 90-95% dependendo da saúde
            prob = 0.90 if health > 15 else 0.95
            return random.random() < prob
        
        # LEANING_OUT: probabilidade cresce com tempo
        if self.state.latent_decision == "LEANING_OUT":
            # PROTEÇÃO ADICIONAL: interesse alto reduz chance
            if self.state.interest >= 70:
                return random.random() < 0.10  # Só 10% de sair
            
            # Base depende de saúde
            if health < 20:
                base_prob = 0.65
            elif health < 35:
                base_prob = 0.50
            else:
                base_prob = 0.35
            
            # Pattern score influencia
            pattern_score = self.response_memory.get_pattern_score()
            if pattern_score < -2.0:
                base_prob *= 1.4
            elif pattern_score > 2.0:
                base_prob *= 0.7
            
            # Multiplicador temporal (após turno 10)
            if turn_count >= 10:
                time_mult = 1.3
                if turn_count >= 14:
                    time_mult = 1.6
                base_prob *= time_mult
            
            # Nunca 100%
            base_prob = min(0.92, base_prob)
            return random.random() < base_prob
        
        return False

    async def generate_speech(self, intent: str, context: str) -> str:
        """Gera a fala do shark usando LLM"""
        try:
            chat = LlmChat(
                api_key=EMERGENT_LLM_KEY,
                session_id=f"shark_{self.shark_id}_{uuid.uuid4().hex[:8]}",
                system_message=self.archetype['personalidade_prompt']
            ).with_model("openai", "gpt-5.2")
            
            prompt = f"""{context}

Intenção: {intent}

Gere uma fala CURTA (máximo 2-3 frases) como {self.archetype['name']}. 
Seja direto, sem rodeios. Use o estilo: {self.archetype['estilo']}.
Não seja prolixo. Seja incisivo."""
            
            user_message = UserMessage(text=prompt)
            response = await chat.send_message(user_message)
            
            return response.strip()
        except Exception as e:
            print(f"Erro ao gerar fala do shark: {e}")
            # Fallback
            return random.choice(self.archetype['perguntas_tipicas'])

class Orchestrator:
    def __init__(
        self, 
        db, 
        session_id: str, 
        pitch_data: Dict[str, Any], 
        sharks_data: List[Dict[str, Any]],
        initial_turn_count: int = 0,
        initial_phase: str = "exploration",
        initial_session_phase: str = "PITCHING",
        initial_negotiation_state: Optional[Dict] = None,
        pitch_evaluation: Optional[Dict] = None  # NOVO
    ):
        self.db = db
        self.session_id = session_id
        self.pitch_data = pitch_data
        self.turn_count = initial_turn_count  # CARREGA do banco, não começa do zero
        self.phase = initial_phase  # CARREGA do banco
        
        # === AVALIAÇÃO DO PITCH (IDEIA vs APRESENTAÇÃO) ===
        self.pitch_evaluation = pitch_evaluation or {}
        self.offer_probability_multiplier = self.pitch_evaluation.get('offer_probability_multiplier', 0.6)
        self.idea_tier = self.pitch_evaluation.get('idea_tier', 'MEDIANA')
        
        # === SISTEMA DE NEGOCIAÇÃO ===
        self.session_phase = SessionPhase(initial_session_phase) if initial_session_phase else SessionPhase.PITCHING
        self.negotiation_manager = NegotiationManager(db, session_id, pitch_data)
        
        # Estado de negociação
        if initial_negotiation_state:
            self.negotiation_state = NegotiationState(**initial_negotiation_state)
        else:
            self.negotiation_state = NegotiationState()
        
        # Ofertas ativas (carregadas do banco)
        self.active_offers: List[Offer] = []
        
        # Deals fechados
        self.deals_closed: List[Dict] = []
        
        # Contadores para final
        self.total_offers_made = 0
        self.total_offers_withdrawn = 0
        
        # Criar agentes dos sharks
        self.sharks: List[SharkAgent] = []
        session_context = f"Pitch: {pitch_data.get('titulo', '')}. Problema: {pitch_data.get('problema', '')}. Solução: {pitch_data.get('solucao', '')}."
        
        for shark_data in sharks_data:
            archetype = get_archetype_by_id(shark_data['archetype_id'])
            if archetype:
                # Carregar estado existente se houver
                initial_state = None
                if 'state' in shark_data:
                    initial_state = SharkState(**shark_data['state'])
                
                agent = SharkAgent(shark_data['shark_id'], archetype, session_context, initial_state)
                self.sharks.append(agent)
    
    async def load_active_offers(self):
        """Carrega ofertas ativas do banco"""
        offers_data = await self.db.offers.find(
            {"session_id": self.session_id, "status": "ACTIVE"},
            {"_id": 0}
        ).to_list(10)
        
        self.active_offers = [Offer(**o) for o in offers_data]
    
    async def save_offer(self, offer: Offer):
        """Salva oferta no banco"""
        await self.db.offers.update_one(
            {"id": offer.id},
            {"$set": offer.model_dump()},
            upsert=True
        )
    
    def analyze_answer_quality(self, answer: str) -> Dict[str, Any]:
        """Análise aprimorada da qualidade da resposta"""
        words = answer.split()
        answer_lower = answer.lower()
        
        # Detecta evasividade (respostas muito longas ou muito curtas)
        is_evasive = len(words) > 100 or len(words) < 5
        
        # Detecta números
        has_numbers = any(char.isdigit() for char in answer)
        
        # Resposta direta (entre 10-60 palavras)
        is_direct = 10 <= len(words) <= 60
        
        # Visão (palavras relacionadas a futuro/escala)
        vision_words = ['futuro', 'escala', 'crescimento', 'bilhão', 'milhão', 'global', 'mundial', 'expansão']
        has_vision = any(word in answer_lower for word in vision_words)
        
        # Diferenciação (palavras que indicam diferencial)
        diff_words = ['único', 'exclusivo', 'diferente', 'inovador', 'pioneiro', 'patenteado', 'proprietário']
        has_differentiation = any(word in answer_lower for word in diff_words)
        
        # Genericidade (buzzwords vazios)
        generic_words = ['disruptivo', 'revolucionário', 'transformador', 'game changer']
        is_generic = any(word in answer_lower for word in generic_words) and not has_differentiation
        
        return {
            'is_evasive': is_evasive,
            'has_numbers': has_numbers,
            'is_direct': is_direct,
            'has_vision': has_vision,
            'has_differentiation': has_differentiation,
            'is_generic': is_generic,
            'word_count': len(words)
        }
    
    async def process_user_answer(self, answer: str) -> OrchestratorResponse:
        """Processa a resposta do usuário e decide o próximo evento"""
        self.turn_count += 1
        
        messages: List[MessageResponse] = []
        events: List[EventResponse] = []
        
        # Carregar ofertas ativas do banco
        await self.load_active_offers()
        
        # 1. Salvar resposta do usuário
        user_message = await self._save_message("USER", answer, MessageType.ANSWER)
        messages.append(user_message)
        
        # 2. Criar evento ANSWER_RECEIVED
        answer_event = await self._save_event(EventType.ANSWER_RECEIVED, "USER", {"content": answer})
        events.append(answer_event)
        
        # 3. Analisar qualidade da resposta
        answer_quality = self.analyze_answer_quality(answer)
        
        if answer_quality['is_evasive']:
            evasive_event = await self._save_event(EventType.ANSWER_EVASIVE, "USER", answer_quality)
            events.append(evasive_event)
        
        # 4. Atualizar estado de todos os sharks (MODELO HÍBRIDO)
        for shark in self.sharks:
            if not shark.state.is_out:
                shark.update_state_from_answer(answer, answer_quality, self.turn_count)
                
                # PERSISTIR ESTADO NO BANCO
                await self.db.session_sharks.update_one(
                    {"session_id": self.session_id, "archetype_name": shark.archetype['name']},
                    {"$set": {"state": shark.state.model_dump()}}
                )
        
        # 5. Atualizar validade das ofertas ativas
        expired_offers = await self._update_offers_validity(messages, events)
        
        # 6. Decidir próximo evento
        active_sharks = [s for s in self.sharks if not s.state.is_out]
        
        # LIMITE CRÍTICO: 18 turnos
        if self.turn_count >= 18:
            return await self._end_session_with_negotiation(messages, events)
        
        if not active_sharks:
            return await self._end_session_with_negotiation(messages, events)
        
        # 7. VERIFICAR SAÍDAS AUTOMÁTICAS
        for shark in active_sharks[:]:
            if shark.should_go_out(self.turn_count):
                # Se shark tinha oferta ativa, retirar antes de sair
                await self._withdraw_offer_if_exists(shark, messages, events)
                out_msg, out_event = await self._generate_out(shark)
                messages.append(out_msg)
                events.append(out_event)
        
        # Atualizar lista de sharks ativos
        active_sharks = [s for s in self.sharks if not s.state.is_out]
        
        if not active_sharks:
            return await self._end_session_with_negotiation(messages, events)
        
        # 8. LÓGICA DE OFERTAS - NOVO SISTEMA
        # Verificar se deve gerar nova oferta
        if self.session_phase == SessionPhase.PITCHING and self.turn_count >= 6:
            new_offer = await self._try_generate_offer(active_sharks, messages, events)
            
            if new_offer:
                # Entrar em modo NEGOTIATION_WINDOW
                self.session_phase = SessionPhase.NEGOTIATION_WINDOW
                await self._save_event(EventType.NEGOTIATION_STARTED, "SYSTEM", {
                    "offer_id": new_offer.id,
                    "shark": new_offer.shark_name
                })
        
        # 9. Se em NEGOTIATION_WINDOW, adicionar pressão
        if self.session_phase == SessionPhase.NEGOTIATION_WINDOW and self.active_offers:
            await self._add_offer_pressure(messages, events)
        
        # 10. Escolher shark para responder (se não houver oferta pendente)
        responding_shark = random.choice(active_sharks)
        
        # 11. Chance de interrupção
        if responding_shark.should_interrupt(self.turn_count) and self.turn_count > 2:
            interrupt_msg, interrupt_event = await self._generate_interruption(responding_shark)
            messages.append(interrupt_msg)
            events.append(interrupt_event)
        
        # 12. Gerar próxima pergunta
        question_msg, question_event = await self._generate_question(responding_shark, answer)
        messages.append(question_msg)
        events.append(question_event)
        
        # 13. Atualizar fase
        if self.turn_count > 8:
            self.phase = "tension"
        if self.turn_count > 15:
            self.phase = "closing"
        
        # 14. Reading hint
        reading_hint = None
        if self.turn_count % 3 == 0:
            reading_hint = self._generate_reading_hint()
        
        return OrchestratorResponse(
            messages=messages,
            events=events,
            session_status=SessionStatus.IN_PROGRESS,
            can_user_respond=True,
            reading_hint=reading_hint,
            session_phase=self.session_phase,
            active_offers=self.active_offers,
            awaiting_founder_action=len(self.active_offers) > 0
        )
    
    async def process_founder_action(self, action_request: FounderActionRequest) -> OrchestratorResponse:
        """Processa a ação do founder em resposta a uma oferta"""
        messages: List[MessageResponse] = []
        events: List[EventResponse] = []
        
        # Carregar ofertas ativas
        await self.load_active_offers()
        
        # Encontrar a oferta alvo
        target_offer = None
        for offer in self.active_offers:
            if offer.id == action_request.offer_id:
                target_offer = offer
                break
        
        if not target_offer:
            raise ValueError("Oferta não encontrada")
        
        # Encontrar o shark da oferta
        offering_shark = None
        for shark in self.sharks:
            if shark.shark_id == target_offer.shark_id:
                offering_shark = shark
                break
        
        if action_request.action == FounderAction.ACCEPT:
            return await self._handle_accept(target_offer, offering_shark, messages, events)
        
        elif action_request.action == FounderAction.REJECT:
            return await self._handle_reject(target_offer, offering_shark, messages, events)
        
        elif action_request.action == FounderAction.COUNTER:
            return await self._handle_counter(
                target_offer, 
                offering_shark, 
                action_request.counter_offer,
                messages, 
                events
            )
        
        elif action_request.action == FounderAction.WAIT:
            return await self._handle_wait(target_offer, offering_shark, messages, events)
        
        raise ValueError(f"Ação desconhecida: {action_request.action}")
    
    # === HANDLERS DE AÇÕES DO FOUNDER ===
    
    async def _handle_accept(
        self, 
        offer: Offer, 
        shark: SharkAgent,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ) -> OrchestratorResponse:
        """Processa aceitação de oferta"""
        # Atualizar oferta
        offer.status = OfferStatus.ACCEPTED
        await self.save_offer(offer)
        
        # Gerar reação do shark
        reaction = self.negotiation_manager.generate_accept_reaction(offer)
        msg = await self._save_message(shark.archetype['name'], reaction, MessageType.DEAL_ANNOUNCEMENT)
        messages.append(msg)
        
        # Evento de deal fechado
        deal_event = await self._save_event(EventType.DEAL_CLOSED, shark.archetype['name'], {
            "offer_id": offer.id,
            "valor": offer.valor,
            "equity": offer.equity,
            "offer_type": offer.offer_type
        })
        events.append(deal_event)
        
        # Registrar deal
        self.deals_closed.append({
            "shark_name": shark.archetype['name'],
            "valor": offer.valor,
            "equity": offer.equity
        })
        
        # Encerrar sessão com final cinematográfico
        return await self._end_session_with_negotiation(messages, events, deal_just_closed=True)
    
    async def _handle_reject(
        self,
        offer: Offer,
        shark: SharkAgent,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ) -> OrchestratorResponse:
        """Processa rejeição de oferta"""
        # Decidir se shark vai ficar ou sair
        will_stay = shark.state.interest > 70 and random.random() < 0.4
        
        # Atualizar oferta
        offer.status = OfferStatus.REJECTED
        await self.save_offer(offer)
        
        # Evento de rejeição
        reject_event = await self._save_event(EventType.FOUNDER_REJECTED, "FOUNDER", {
            "offer_id": offer.id,
            "shark": shark.archetype['name']
        })
        events.append(reject_event)
        
        # Gerar reação do shark
        reaction = self.negotiation_manager.generate_reject_reaction(shark.archetype['id'], will_stay)
        msg = await self._save_message(shark.archetype['name'], reaction, MessageType.SHARK_REACTION)
        messages.append(msg)
        
        # Se shark não vai ficar, sair
        if not will_stay:
            shark.state.is_out = True
            await self.db.session_sharks.update_one(
                {"session_id": self.session_id, "archetype_name": shark.archetype['name']},
                {"$set": {"state": shark.state.model_dump(), "is_out": True}}
            )
            out_event = await self._save_event(EventType.SHARK_OUT, shark.archetype['name'], {
                "reason": "Oferta rejeitada"
            })
            events.append(out_event)
        else:
            # Shark fica mas perde paciência
            shark.state.patience -= 15
            shark.confianca -= 10
        
        # Remover da lista de ofertas ativas
        self.active_offers = [o for o in self.active_offers if o.id != offer.id]
        
        # Verificar se ainda há ofertas ativas
        if not self.active_offers:
            self.session_phase = SessionPhase.PITCHING
        
        # Outros sharks podem reagir
        await self._other_sharks_react_to_rejection(shark, messages, events)
        
        return OrchestratorResponse(
            messages=messages,
            events=events,
            session_status=SessionStatus.IN_PROGRESS,
            can_user_respond=True,
            session_phase=self.session_phase,
            active_offers=self.active_offers,
            awaiting_founder_action=len(self.active_offers) > 0
        )
    
    async def _handle_counter(
        self,
        offer: Offer,
        shark: SharkAgent,
        counter: CounterOffer,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ) -> OrchestratorResponse:
        """Processa contra-proposta do founder"""
        # Evento de contra-proposta
        counter_event = await self._save_event(EventType.FOUNDER_COUNTERED, "FOUNDER", {
            "offer_id": offer.id,
            "counter_valor": counter.valor,
            "counter_equity": counter.equity,
            "message": counter.message
        })
        events.append(counter_event)
        
        # Mensagem do founder
        founder_msg = f"Eu tenho uma contra-proposta: {counter.valor} por {counter.equity}."
        if counter.message:
            founder_msg += f" {counter.message}"
        msg = await self._save_message("FOUNDER", founder_msg, MessageType.COUNTER_OFFER)
        messages.append(msg)
        
        # === AVALIAR AGRESSIVIDADE DA CONTRA-PROPOSTA ===
        try:
            original_equity = self.negotiation_manager._parse_equity(offer.equity)
            counter_equity = self.negotiation_manager._parse_equity(counter.equity)
            equity_diff = original_equity - counter_equity
            
            # Se pede muito menos equity (>5% diferença) = agressivo
            if equity_diff > 5:
                # Dano de confiança proporcional à agressividade
                confidence_damage = min(20, equity_diff * 2)
                shark.confianca -= confidence_damage
                shark.state.confianca_apresentacao -= confidence_damage
                
                # Shark fica irritado
                if equity_diff > 10:
                    # Muito agressivo - chance de sair
                    shark.state.patience -= 15
        except:
            pass
        
        # Shark avalia contra-proposta
        accepted = self.negotiation_manager.evaluate_counter_offer(
            offer, counter, shark.state.interest, shark.confianca
        )
        
        # Gerar reação
        reaction = self.negotiation_manager.generate_counter_reaction(accepted, offer, counter)
        reaction_msg = await self._save_message(shark.archetype['name'], reaction, MessageType.SHARK_REACTION)
        messages.append(reaction_msg)
        
        if accepted:
            # Atualizar oferta com novos valores
            offer.valor = counter.valor
            offer.equity = counter.equity
            offer.status = OfferStatus.ACCEPTED
            await self.save_offer(offer)
            
            # Deal fechado
            deal_event = await self._save_event(EventType.DEAL_CLOSED, shark.archetype['name'], {
                "offer_id": offer.id,
                "valor": counter.valor,
                "equity": counter.equity,
                "was_counter": True
            })
            events.append(deal_event)
            
            self.deals_closed.append({
                "shark_name": shark.archetype['name'],
                "valor": counter.valor,
                "equity": counter.equity
            })
            
            return await self._end_session_with_negotiation(messages, events, deal_just_closed=True)
        else:
            # Shark mantém ou rejeita
            # Oferta original ainda está na mesa
            offer.turns_remaining = max(1, offer.turns_remaining - 1)
            await self.save_offer(offer)
            
            return OrchestratorResponse(
                messages=messages,
                events=events,
                session_status=SessionStatus.IN_PROGRESS,
                can_user_respond=True,
                session_phase=self.session_phase,
                active_offers=self.active_offers,
                awaiting_founder_action=True
            )
    
    async def _handle_wait(
        self,
        offer: Offer,
        shark: SharkAgent,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ) -> OrchestratorResponse:
        """Processa quando founder escolhe esperar"""
        # Evento
        wait_event = await self._save_event(EventType.FOUNDER_WAITED, "FOUNDER", {
            "offer_id": offer.id
        })
        events.append(wait_event)
        
        # Shark reage
        reaction = self.negotiation_manager.generate_wait_reaction(shark.archetype['id'])
        msg = await self._save_message(shark.archetype['name'], reaction, MessageType.SHARK_REACTION)
        messages.append(msg)
        
        # Aumentar fadiga de todos os sharks
        for s in self.sharks:
            if not s.state.is_out:
                s.state.patience -= 8
                s.fadiga += 5
        
        # Decrementar validade de todas as ofertas
        for o in self.active_offers:
            o.turns_remaining -= 1
            await self.save_offer(o)
        
        # Verificar se outras sharks querem fazer oferta
        active_sharks = [s for s in self.sharks if not s.state.is_out and s.shark_id != shark.shark_id]
        await self._try_generate_offer(active_sharks, messages, events)
        
        # Conflito entre sharks
        if len(self.active_offers) > 1:
            await self._generate_shark_conflict(messages, events)
        
        return OrchestratorResponse(
            messages=messages,
            events=events,
            session_status=SessionStatus.IN_PROGRESS,
            can_user_respond=True,
            session_phase=self.session_phase,
            active_offers=self.active_offers,
            awaiting_founder_action=len(self.active_offers) > 0
        )
    
    # === MÉTODOS AUXILIARES DE NEGOCIAÇÃO ===
    
    async def _try_generate_offer(
        self, 
        active_sharks: List[SharkAgent],
        messages: List[MessageResponse],
        events: List[EventResponse]
    ) -> Optional[Offer]:
        """
        Tenta gerar uma nova oferta se condições forem atendidas.
        
        CALIBRAGEM: Ofertas são RARAS
        - 0 ofertas: Normal (maioria dos pitches)
        - 1 oferta: Bom pitch
        - 2 ofertas: Muito bom (raro)
        - 3+ ofertas: Excepcional (< 5% dos casos)
        """
        # Limitar número máximo de ofertas baseado na ideia
        max_offers_by_tier = {
            "RUIM": 0,
            "FRACA": 1,
            "MEDIANA": 1,
            "FORTE": 2,
            "EXCEPCIONAL": 3
        }
        max_offers = max_offers_by_tier.get(self.idea_tier, 1)
        
        if len(self.active_offers) + self.total_offers_made >= max_offers:
            return None  # Já atingiu o limite
        
        # Sharks que já têm oferta ativa não fazem outra
        sharks_with_offers = {o.shark_id for o in self.active_offers}
        
        # Usar confiança da IDEIA como threshold (não só apresentação)
        eligible_sharks = [
            s for s in active_sharks 
            if s.shark_id not in sharks_with_offers
            and s.state.interest >= 75 
            and s.state.confianca_ideia >= 40  # NOVO: baseado na ideia
        ]
        
        if not eligible_sharks:
            return None
        
        for shark in eligible_sharks:
            # Probabilidade BASE muito mais baixa
            base_prob = 0.03  # 3% base (era 8%)
            
            if shark.state.interest >= 90:
                base_prob = 0.06  # 6% (era 15%)
            if shark.state.interest >= 100:
                base_prob = 0.10  # 10% (era 25%)
            
            # MULTIPLICADOR DA IDEIA (crucial!)
            base_prob *= self.offer_probability_multiplier
            
            # Multiplicador temporal
            if self.turn_count >= 10:
                base_prob *= 1.3
            if self.turn_count >= 14:
                base_prob *= 1.5
            
            # Se shark "viu potencial" em ideia boa mal apresentada
            if shark.state.saw_potential:
                base_prob *= 1.5
            
            # Se shark está DESCONFIADO (apresentação boa, ideia fraca)
            if shark.state.skepticism == "DESCONFIADO":
                base_prob *= 0.3  # Muito menos provável
            
            if random.random() < base_prob:
                # Criar oferta
                offer = self.negotiation_manager.create_offer(
                    shark_id=shark.shark_id,
                    shark_name=shark.archetype['name'],
                    shark_archetype=shark.archetype['id'],
                    interest=shark.state.interest,
                    confianca=shark.confianca,
                    patience=shark.state.patience,
                    turn_count=self.turn_count
                )
                
                # Salvar no banco
                await self.save_offer(offer)
                self.active_offers.append(offer)
                self.total_offers_made += 1
                
                # Atualizar estado do shark
                shark.state.has_active_offer = True
                shark.state.offer_id = offer.id
                
                # Gerar fala
                speech = self.negotiation_manager.generate_offer_speech(offer, shark.archetype['id'])
                msg = await self._save_message(shark.archetype['name'], speech, MessageType.OFFER)
                messages.append(msg)
                
                # Evento
                offer_event = await self._save_event(EventType.SHARK_OFFER, shark.archetype['name'], {
                    "offer_id": offer.id,
                    "offer_type": offer.offer_type,
                    "valor": offer.valor,
                    "equity": offer.equity,
                    "turns_remaining": offer.turns_remaining
                })
                events.append(offer_event)
                
                return offer
        
        return None
    
    async def _update_offers_validity(
        self,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ) -> List[Offer]:
        """Atualiza validade das ofertas e retira as expiradas"""
        expired = []
        
        for offer in self.active_offers[:]:
            offer.turns_remaining -= 1
            
            if offer.turns_remaining <= 0:
                # Oferta expirou
                offer.status = OfferStatus.WITHDRAWN
                offer.withdrawn_at_turn = self.turn_count
                await self.save_offer(offer)
                
                # Encontrar shark
                shark = next((s for s in self.sharks if s.shark_id == offer.shark_id), None)
                if shark:
                    speech = self.negotiation_manager.generate_withdrawal_speech(shark.archetype['id'])
                    msg = await self._save_message(shark.archetype['name'], speech, MessageType.OFFER_WITHDRAWN)
                    messages.append(msg)
                    
                    # Atualizar estado
                    shark.state.has_active_offer = False
                    shark.state.offer_id = None
                
                # Evento
                withdraw_event = await self._save_event(EventType.SHARK_OFFER_WITHDRAWN, offer.shark_name, {
                    "offer_id": offer.id,
                    "reason": "Tempo esgotado"
                })
                events.append(withdraw_event)
                
                expired.append(offer)
                self.active_offers.remove(offer)
                self.total_offers_withdrawn += 1
            else:
                await self.save_offer(offer)
        
        # Se não há mais ofertas, voltar para PITCHING
        if not self.active_offers and self.session_phase == SessionPhase.NEGOTIATION_WINDOW:
            self.session_phase = SessionPhase.PITCHING
        
        return expired
    
    async def _add_offer_pressure(
        self,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ):
        """Adiciona pressão de sharks com ofertas ativas"""
        for offer in self.active_offers:
            if offer.turns_remaining <= 2 and random.random() < 0.5:
                shark = next((s for s in self.sharks if s.shark_id == offer.shark_id), None)
                if shark:
                    speech = self.negotiation_manager.generate_pressure_speech(offer, offer.turns_remaining)
                    msg = await self._save_message(shark.archetype['name'], speech, MessageType.OFFER_PRESSURE)
                    messages.append(msg)
    
    async def _withdraw_offer_if_exists(
        self,
        shark: SharkAgent,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ):
        """Retira oferta de um shark que está saindo"""
        for offer in self.active_offers[:]:
            if offer.shark_id == shark.shark_id:
                offer.status = OfferStatus.WITHDRAWN
                await self.save_offer(offer)
                self.active_offers.remove(offer)
                self.total_offers_withdrawn += 1
                
                withdraw_event = await self._save_event(EventType.SHARK_OFFER_WITHDRAWN, shark.archetype['name'], {
                    "offer_id": offer.id,
                    "reason": "Shark saiu"
                })
                events.append(withdraw_event)
    
    async def _other_sharks_react_to_rejection(
        self,
        rejected_shark: SharkAgent,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ):
        """Outros sharks reagem à rejeição"""
        active_sharks = [s for s in self.sharks if not s.state.is_out and s.shark_id != rejected_shark.shark_id]
        
        # 30% de chance de outro shark comentar
        if active_sharks and random.random() < 0.3:
            commenting_shark = random.choice(active_sharks)
            comments = [
                f"Você recusou porque acredita no valor ou porque não sabe onde está o limite?",
                f"Interessante. Não é assim que eu jogaria, mas ok.",
                f"Bom, isso muda a dinâmica da mesa."
            ]
            speech = random.choice(comments)
            msg = await self._save_message(commenting_shark.archetype['name'], speech, MessageType.SHARK_REACTION)
            messages.append(msg)
    
    async def _generate_shark_conflict(
        self,
        messages: List[MessageResponse],
        events: List[EventResponse]
    ):
        """Gera conflito entre sharks quando há múltiplas ofertas"""
        if len(self.active_offers) < 2:
            return
        
        # 40% de chance de conflito
        if random.random() < 0.4:
            offer1 = self.active_offers[0]
            offer2 = self.active_offers[1]
            
            shark1 = next((s for s in self.sharks if s.shark_id == offer1.shark_id), None)
            shark2 = next((s for s in self.sharks if s.shark_id == offer2.shark_id), None)
            
            if shark1 and shark2:
                speech = self.negotiation_manager.generate_shark_conflict(
                    shark1.archetype['name'],
                    shark2.archetype['name'],
                    offer2
                )
                msg = await self._save_message(shark1.archetype['name'], speech, MessageType.SHARK_CONFLICT)
                messages.append(msg)
                
                conflict_event = await self._save_event(EventType.SHARK_CONFLICT, shark1.archetype['name'], {
                    "target_shark": shark2.archetype['name'],
                    "target_offer_id": offer2.id
                })
                events.append(conflict_event)
    
    async def _end_session_with_negotiation(
        self,
        messages: List[MessageResponse],
        events: List[EventResponse],
        deal_just_closed: bool = False
    ) -> OrchestratorResponse:
        """Encerra a sessão com final cinematográfico"""
        # Determinar tipo de final
        try:
            original_equity = self.negotiation_manager._parse_equity(self.pitch_data.get('pedido_equity', '10%'))
        except:
            original_equity = 10
        
        ending_type = self.negotiation_manager.determine_ending_type(
            self.deals_closed,
            self.total_offers_made,
            self.total_offers_withdrawn,
            original_equity
        )
        
        # Gerar narração
        narration = self.negotiation_manager.generate_ending_narration(
            ending_type,
            self.deals_closed,
            self.total_offers_made
        )
        
        # Mensagem de narração
        narration_msg = await self._save_message("NARRADOR", narration, MessageType.NARRATION)
        messages.append(narration_msg)
        
        # Evento de fim
        end_event = await self._save_event(EventType.SESSION_ENDED, "SYSTEM", {
            "turn_count": self.turn_count,
            "ending_type": ending_type,
            "deals_closed": len(self.deals_closed),
            "offers_made": self.total_offers_made,
            "offers_withdrawn": self.total_offers_withdrawn
        })
        events.append(end_event)
        
        # Atualizar sessão no banco
        await self.db.sessions.update_one(
            {"id": self.session_id},
            {"$set": {
                "status": SessionStatus.COMPLETED,
                "ending_type": ending_type,
                "deals_closed": self.deals_closed,
                "total_offers_made": self.total_offers_made
            }}
        )
        
        return OrchestratorResponse(
            messages=messages,
            events=events,
            session_status=SessionStatus.COMPLETED,
            can_user_respond=False,
            session_phase=SessionPhase.CLOSING,
            active_offers=[],
            awaiting_founder_action=False,
            ending={
                "type": ending_type,
                "narration": narration,
                "deals": self.deals_closed
            }
        )
    
    async def _generate_question(self, shark: SharkAgent, previous_answer: str) -> tuple:
        """Gera uma pergunta do shark usando histórico completo"""
        # Construir contexto com últimas 3-4 interações
        recent_context = "\n".join(shark.conversation_memory[-4:]) if len(shark.conversation_memory) > 0 else ""
        
        # Detectar se resposta foi evasiva/genérica
        answer_quality = self.analyze_answer_quality(previous_answer)
        is_generic = answer_quality.get('is_generic', False) or answer_quality.get('is_evasive', False)
        
        # PERGUNTAS DE CORTE para pitch genérico
        if is_generic and self.turn_count > 4:
            context = f"""Histórico recente:
{recent_context}

A resposta foi GENÉRICA ou EVASIVA: '{previous_answer}'

Faça uma PERGUNTA DE CORTE (binary question):
- "Quem paga? Hoje. Agora."
- "Quanto custa adquirir 1 cliente? Número."
- "Qual sua margem? Porcentagem."

Seja BRUTAL e DIRETO. Exija números ou fatos concretos.
Máximo 1-2 frases curtas."""
        else:
            context = f"""Histórico recente da conversa:
{recent_context}

Última resposta: '{previous_answer}'

Faça uma pergunta incisiva relacionada ao pitch OU ao histórico.
Seja direto e sem rodeios. Use o estilo: {shark.archetype['estilo']}."""
        
        speech = await shark.generate_speech("QUESTION", context)
        
        message = await self._save_message(shark.archetype['name'], speech, MessageType.QUESTION)
        event = await self._save_event(EventType.QUESTION_ASKED, shark.archetype['name'], {"question": speech})
        
        return message, event
    
    async def _generate_interruption(self, shark: SharkAgent) -> tuple:
        """Gera uma interrupção do shark"""
        context = "Você está interrompendo o empreendedor porque não está satisfeito com a direção da conversa."
        
        speech = await shark.generate_speech("INTERRUPT", context)
        
        message = await self._save_message(shark.archetype['name'], speech, MessageType.INTERRUPTION)
        event = await self._save_event(EventType.PITCH_INTERRUPTED, shark.archetype['name'], {"reason": "Insatisfação"})
        
        return message, event
    
    async def _generate_out(self, shark: SharkAgent) -> tuple:
        """Gera a saída de um shark"""
        shark.state.is_out = True
        
        context = "Você está saindo do investimento. Seja direto e explique brevemente por quê."
        speech = await shark.generate_speech("OUT", context)
        
        message = await self._save_message(shark.archetype['name'], speech, MessageType.OUT_ANNOUNCEMENT)
        event = await self._save_event(EventType.SHARK_OUT, shark.archetype['name'], {
            "reason": "Perda de interesse",
            "final_interest": shark.state.interest,
            "final_patience": shark.state.patience
        })
        
        # Atualizar no banco
        await self.db.session_sharks.update_one(
            {"session_id": self.session_id, "archetype_name": shark.archetype['name']},
            {"$set": {"state": shark.state.model_dump(), "is_out": True}}
        )
        
        return message, event
    
    def _generate_reading_hint(self) -> Optional[str]:
        """Gera dica de leitura de mesa"""
        active_sharks = [s for s in self.sharks if not s.state.is_out]
        if not active_sharks:
            return None
            
        shark = random.choice(active_sharks)
        
        if shark.state.interest < 30:
            return f"{shark.archetype['name']} parece entediado."
        elif shark.state.patience < 40:
            return f"{shark.archetype['name']} demonstra impaciência."
        elif shark.state.interest > 70:
            return f"{shark.archetype['name']} está mais atento."
        
        return None
    
    async def _save_message(self, speaker: str, content: str, message_type: MessageType) -> MessageResponse:
        """Salva uma mensagem no banco"""
        message_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        message_doc = {
            "id": message_id,
            "session_id": self.session_id,
            "speaker": speaker,
            "content": content,
            "message_type": message_type,
            "timestamp": timestamp
        }
        
        await self.db.messages.insert_one(message_doc)
        
        return MessageResponse(**message_doc)
    
    async def _save_event(self, event_type: EventType, actor: str, data: Dict[str, Any]) -> EventResponse:
        """Salva um evento no banco"""
        event_id = str(uuid.uuid4())
        timestamp = datetime.now(timezone.utc).isoformat()
        
        event_doc = {
            "id": event_id,
            "session_id": self.session_id,
            "event_type": event_type,
            "actor": actor,
            "timestamp": timestamp,
            "data": data
        }
        
        await self.db.events.insert_one(event_doc)
        
        return EventResponse(**event_doc)