from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
import uuid
from models import (
    EventType, MessageType, SessionStatus, SharkState,
    MessageResponse, EventResponse, OrchestratorResponse
)
from shark_archetypes import get_archetype_by_id
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
    def __init__(self, shark_id: str, archetype_data: Dict[str, Any], session_context: str):
        self.shark_id = shark_id
        self.archetype = archetype_data
        self.state = SharkState()
        self.session_context = session_context
        self.conversation_memory: List[str] = []
        
        # Nova camada: memória ponderada
        self.response_memory = ResponseMemory()
        
        # Nova camada: confiança implícita (0-100)
        self.confianca = 50.0
        
        # Nova camada: fadiga temporal (0-100)
        self.fadiga = 0.0
        
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
        
        # CAMADA 1: Desgaste natural (sempre)
        desgaste = 3.0
        if self.archetype['id'] == 'operador':
            desgaste = 4.0  # Menos paciente
        elif self.archetype['id'] == 'financeiro':
            desgaste = 3.5
        
        self.state.patience -= desgaste
        self.fadiga += (turn_count * 0.5)  # Fadiga cresce com tempo
        
        # CAMADA 2: Memória ponderada
        self.response_memory.decay_weights()  # Decai histórico
        
        quality = self._evaluate_response_quality(answer, answer_analysis)
        self.response_memory.add_response(quality, answer_analysis)
        
        pattern_score = self.response_memory.get_pattern_score()
        recent_trend = self.response_memory.get_recent_trend(3)
        
        # CAMADA 3: Confiança implícita
        # Confiança aumenta com coerência, cai com contradição
        if quality == 1:
            self.confianca += 3.0
        elif quality == -1:
            self.confianca -= 5.0
        
        # Contradições impactam muito
        if self._detect_contradiction(answer):
            self.confianca -= 15.0
        
        # Padrão consistente constrói confiança
        if pattern_score > 2.0:
            self.confianca += 2.0
        elif pattern_score < -2.0:
            self.confianca -= 3.0
        
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
        
        # Ajustar decisão latente baseado em saúde composta
        self._update_latent_decision()
            
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
        """Decide se o shark deve sair (com multiplicador progressivo)"""
        if self.state.is_out:
            return False
        
        # Primeiros 3-4 turnos: proteção - saída é rara
        if turn_count <= 4:
            if self.state.latent_decision == "OUT":
                return random.random() < 0.15  # Apenas 15% mesmo com decisão OUT
            return False
        
        # Decisão OUT: deve sair
        if self.state.latent_decision == "OUT":
            return True
        
        # Decisão LEANING_OUT: probabilidade base
        base_probability = 0.40
        
        # A partir do turno 10: multiplicador progressivo baseado no estado
        if turn_count >= 10:
            # Calcular "saúde" do shark (0-100)
            health_score = (self.state.interest + self.state.patience) / 2
            
            # Multiplicador: quanto pior o estado, maior a chance
            if health_score < 20:
                multiplier = 3.0  # Saúde crítica
            elif health_score < 35:
                multiplier = 2.0  # Saúde baixa
            elif health_score < 50:
                multiplier = 1.5  # Saúde média-baixa
            else:
                multiplier = 1.0  # Saúde OK
            
            # Aumenta multiplicador progressivamente após turno 15
            if turn_count >= 15:
                multiplier *= 1.3
            if turn_count >= 18:
                multiplier *= 1.5
            
            base_probability *= multiplier
        
        if self.state.latent_decision == "LEANING_OUT":
            return random.random() < base_probability
        
        # Chance mínima se estado muito ruim
        if self.state.interest < 20 or self.state.patience < 15:
            return random.random() < 0.25
        
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
    def __init__(self, db, session_id: str, pitch_data: Dict[str, Any], sharks_data: List[Dict[str, Any]]):
        self.db = db
        self.session_id = session_id
        self.pitch_data = pitch_data
        self.turn_count = 0
        self.phase = "exploration"  # exploration, tension, closing
        
        # Criar agentes dos sharks
        self.sharks: List[SharkAgent] = []
        session_context = f"Pitch: {pitch_data.get('titulo', '')}. Problema: {pitch_data.get('problema', '')}. Solução: {pitch_data.get('solucao', '')}."
        
        for shark_data in sharks_data:
            archetype = get_archetype_by_id(shark_data['archetype_id'])
            if archetype:
                agent = SharkAgent(shark_data['shark_id'], archetype, session_context)
                self.sharks.append(agent)
    
    def analyze_answer_quality(self, answer: str) -> Dict[str, Any]:
        """Análise simples da qualidade da resposta"""
        words = answer.split()
        
        # Detecta evasividade (respostas muito longas ou muito curtas)
        is_evasive = len(words) > 100 or len(words) < 5
        
        # Detecta números
        has_numbers = any(char.isdigit() for char in answer)
        
        # Resposta direta (entre 10-60 palavras)
        is_direct = 10 <= len(words) <= 60
        
        # Visão (palavras relacionadas a futuro/escala)
        vision_words = ['futuro', 'escala', 'crescimento', 'bilhão', 'milhão', 'global', 'mundial', 'expansão']
        has_vision = any(word in answer.lower() for word in vision_words)
        
        return {
            'is_evasive': is_evasive,
            'has_numbers': has_numbers,
            'is_direct': is_direct,
            'has_vision': has_vision,
            'word_count': len(words)
        }
    
    async def process_user_answer(self, answer: str) -> OrchestratorResponse:
        """Processa a resposta do usuário e decide o próximo evento"""
        self.turn_count += 1
        
        messages: List[MessageResponse] = []
        events: List[EventResponse] = []
        
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
        
        # 4. Atualizar estado de todos os sharks
        for shark in self.sharks:
            if not shark.state.is_out:
                shark.update_state_from_answer(answer, answer_quality)
        
        # 5. Decidir próximo evento
        active_sharks = [s for s in self.sharks if not s.state.is_out]
        
        # Limite máximo de turnos (20-25 turnos)
        if self.turn_count >= 20:
            # Adicionar mensagem de encerramento
            closing_msg = await self._save_message(
                "SYSTEM",
                "A sessão chegou ao tempo limite. Os investidores estão fazendo suas considerações finais.",
                MessageType.COMMENT
            )
            messages.append(closing_msg)
            # Forçar encerramento após 20 turnos
            return await self._end_session(messages, events)
        
        if not active_sharks:
            # Todos saíram - encerrar sessão
            return await self._end_session(messages, events)
        
        # 6. Escolher shark para responder
        responding_shark = random.choice(active_sharks)
        
        # 7. Decidir tipo de resposta
        # Chance de interrupção
        if responding_shark.should_interrupt(self.turn_count) and self.turn_count > 2:
            interrupt_msg, interrupt_event = await self._generate_interruption(responding_shark)
            messages.append(interrupt_msg)
            events.append(interrupt_event)
        
        # Chance de shark sair
        if responding_shark.should_go_out(self.turn_count):
            out_msg, out_event = await self._generate_out(responding_shark)
            messages.append(out_msg)
            events.append(out_event)
            
            # Verificar se ainda há sharks ativos
            active_sharks = [s for s in self.sharks if not s.state.is_out]
            if not active_sharks:
                return await self._end_session(messages, events)
            
            # Próximo shark responde
            responding_shark = random.choice(active_sharks)
        
        # Chance de silêncio de outro shark
        if random.random() < 0.20:
            silent_shark = random.choice([s for s in active_sharks if s.shark_id != responding_shark.shark_id])
            if silent_shark and silent_shark.should_go_silent():
                silent_event = await self._save_event(
                    EventType.SHARK_SILENT,
                    silent_shark.archetype['name'],
                    {"reason": "Perda de interesse ou reflexão"}
                )
                events.append(silent_event)
                silent_shark.state.silent_turns += 1
        
        # 8. Gerar próxima pergunta
        question_msg, question_event = await self._generate_question(responding_shark, answer)
        messages.append(question_msg)
        events.append(question_event)
        
        # 9. Atualizar fase se necessário
        if self.turn_count > 8:
            self.phase = "tension"
        if self.turn_count > 15:
            self.phase = "closing"
        
        # 10. Reading hint (se habilitado)
        reading_hint = None
        if self.turn_count % 3 == 0:  # A cada 3 turnos
            reading_hint = self._generate_reading_hint()
        
        return OrchestratorResponse(
            messages=messages,
            events=events,
            session_status=SessionStatus.IN_PROGRESS,
            can_user_respond=True,
            reading_hint=reading_hint
        )
    
    async def _generate_question(self, shark: SharkAgent, previous_answer: str) -> tuple:
        """Gera uma pergunta do shark"""
        context = f"O usuário respondeu: '{previous_answer}'. Faça uma pergunta relevante e incisiva sobre o pitch."
        
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
    
    async def _end_session(self, messages: List[MessageResponse], events: List[EventResponse]) -> OrchestratorResponse:
        """Encerra a sessão"""
        end_event = await self._save_event(EventType.SESSION_ENDED, "SYSTEM", {"turn_count": self.turn_count})
        events.append(end_event)
        
        # Atualizar status da sessão
        await self.db.sessions.update_one(
            {"id": self.session_id},
            {"$set": {"status": SessionStatus.COMPLETED}}
        )
        
        return OrchestratorResponse(
            messages=messages,
            events=events,
            session_status=SessionStatus.COMPLETED,
            can_user_respond=False,
            reading_hint=None
        )
    
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