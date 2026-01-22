from typing import Dict, Any, List
from datetime import datetime, timezone
import uuid
from models import EventType, MessageType, ReportResponse

class ReportGenerator:
    def __init__(self, db, session_id: str):
        self.db = db
        self.session_id = session_id
    
    async def generate_report(self) -> ReportResponse:
        """Gera relatório factual da sessão"""
        # Buscar dados da sessão
        session = await self.db.sessions.find_one({"id": self.session_id}, {"_id": 0})
        messages = await self.db.messages.find({"session_id": self.session_id}, {"_id": 0}).to_list(1000)
        events = await self.db.events.find({"session_id": self.session_id}, {"_id": 0}).to_list(1000)
        sharks = await self.db.session_sharks.find({"session_id": self.session_id}, {"_id": 0}).to_list(10)
        
        # 1. Síntese (1 frase neutra)
        sintese = self._generate_sintese(sharks, events)
        
        # 2. Linha do tempo
        linha_tempo = self._generate_linha_tempo(events, messages)
        
        # 3. Leitura por shark
        leitura_sharks = self._generate_leitura_sharks(sharks, events, messages)
        
        # 4. Sinais de mesa
        sinais_mesa = self._generate_sinais_mesa(events)
        
        # 5. Padrões do apresentador
        padroes = self._generate_padroes_apresentador(events, messages)
        
        # 6. Pontos de sustentação
        pontos_sustentacao = self._generate_pontos_sustentacao(sharks)
        
        # 7. Veredito
        veredito = self._generate_veredito(sharks)
        
        # 8. Momento de virada (quando a mesa virou)
        momento_virada = self._identify_turning_point(events, sharks)
        
        # Salvar relatório
        report_id = str(uuid.uuid4())
        generated_at = datetime.now(timezone.utc).isoformat()
        
        report_doc = {
            "id": report_id,
            "session_id": self.session_id,
            "sintese": sintese,
            "linha_tempo": linha_tempo,
            "leitura_sharks": leitura_sharks,
            "sinais_mesa": sinais_mesa,
            "padroes_apresentador": padroes,
            "pontos_sustentacao": pontos_sustentacao,
            "veredito": veredito,
            "momento_virada": momento_virada,
            "generated_at": generated_at
        }
        
        await self.db.reports.insert_one(report_doc)
        
        # Criar evento de geração
        await self.db.events.insert_one({
            "id": str(uuid.uuid4()),
            "session_id": self.session_id,
            "event_type": EventType.REPORT_GENERATED,
            "actor": "SYSTEM",
            "timestamp": generated_at,
            "data": {"report_id": report_id}
        })
        
        return ReportResponse(**report_doc)
    
    def _generate_sintese(self, sharks: List[Dict], events: List[Dict]) -> str:
        """Gera síntese de 1 frase"""
        sharks_out = len([s for s in sharks if s.get('is_out', False)])
        sharks_active = len(sharks) - sharks_out
        
        if sharks_active == 0:
            return "A sessão encerrou sem nenhum investidor mantendo interesse."
        elif sharks_out == 0:
            return "Todos os investidores mantiveram interesse até o final da sessão."
        else:
            return f"{sharks_out} de {len(sharks)} investidores saíram durante a sessão."
    
    def _generate_linha_tempo(self, events: List[Dict], messages: List[Dict]) -> List[Dict[str, str]]:
        """Gera linha do tempo com eventos principais"""
        linha = []
        
        for i, event in enumerate(events[:30]):  # Limitar a 30 eventos principais
            timestamp = event.get('timestamp', '')
            event_type = event.get('event_type', '')
            actor = event.get('actor', '')
            data = event.get('data', {})
            
            # Formatar timestamp para minutos
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                minutes = i // 2  # Aproximação simples
                time_str = f"Min {minutes}"
            except:
                time_str = f"Turno {i+1}"
            
            # Descrever evento
            if event_type == EventType.QUESTION_ASKED:
                descricao = f"{actor} fez uma pergunta"
            elif event_type == EventType.ANSWER_EVASIVE:
                descricao = f"Resposta evasiva detectada"
            elif event_type == EventType.PITCH_INTERRUPTED:
                descricao = f"{actor} interrompeu"
            elif event_type == EventType.SHARK_OUT:
                descricao = f"{actor} saiu"
                motivo = data.get('reason', '')
                if motivo:
                    descricao += f" - {motivo}"
            elif event_type == EventType.SHARK_SILENT:
                descricao = f"{actor} permaneceu em silêncio"
            else:
                descricao = event_type
            
            linha.append({
                "momento": time_str,
                "evento": descricao,
                "ator": actor
            })
        
        return linha
    
    def _generate_leitura_sharks(self, sharks: List[Dict], events: List[Dict], messages: List[Dict]) -> List[Dict[str, Any]]:
        """Gera leitura individual de cada shark"""
        leitura = []
        
        for shark in sharks:
            archetype_name = shark.get('archetype_name', '')
            state = shark.get('state', {})
            is_out = shark.get('is_out', False)
            
            # Buscar eventos relacionados a esse shark
            shark_events = [e for e in events if e.get('actor') == archetype_name]
            out_event = next((e for e in shark_events if e.get('event_type') == EventType.SHARK_OUT), None)
            
            # Buscar perguntas feitas
            questions = [m for m in messages if m.get('speaker') == archetype_name and m.get('message_type') == MessageType.QUESTION]
            
            leitura_shark = {
                "shark": archetype_name,
                "o_que_buscava": self._get_shark_thesis(archetype_name),
                "o_que_encontrou": self._analyze_shark_perception(state, is_out),
                "perguntas_feitas": len(questions),
                "resultado": "Saiu" if is_out else "Permaneceu interessado",
                "momento_saida": out_event.get('timestamp', '') if out_event else None,
                "interesse_final": state.get('interest', 0),
                "paciencia_final": state.get('patience', 0)
            }
            
            leitura.append(leitura_shark)
        
        return leitura
    
    def _get_shark_thesis(self, archetype_name: str) -> str:
        """Retorna a tese do shark"""
        teses = {
            "O Operador": "Execução clara e time forte",
            "O Financeiro": "Números sólidos e retorno previsível",
            "O Cético": "Diferencial real e barreira de entrada",
            "O Visionário": "Mercado grande e potencial de escala"
        }
        return teses.get(archetype_name, "Valor sustentável")
    
    def _analyze_shark_perception(self, state: Dict, is_out: bool) -> str:
        """Analisa a percepção do shark durante a sessão"""
        if is_out:
            interest = state.get('interest', 50)
            patience = state.get('patience', 50)
            
            if interest < 20:
                return "Falta de aderência à tese"
            elif patience < 20:
                return "Respostas insatisfatórias"
            else:
                return "Risco não mensurável"
        else:
            return "Interesse mantido"
    
    def _generate_sinais_mesa(self, events: List[Dict]) -> List[str]:
        """Gera lista de sinais não verbais observados"""
        sinais = []
        
        # Contar tipos de eventos
        interruptions = len([e for e in events if e.get('event_type') == EventType.PITCH_INTERRUPTED])
        silences = len([e for e in events if e.get('event_type') == EventType.SHARK_SILENT])
        outs = len([e for e in events if e.get('event_type') == EventType.SHARK_OUT])
        evasive_answers = len([e for e in events if e.get('event_type') == EventType.ANSWER_EVASIVE])
        
        if interruptions > 2:
            sinais.append(f"Múltiplas interrupções ({interruptions}x) indicam desconforto com a direção da conversa")
        if silences > 2:
            sinais.append(f"Silêncios prolongados ({silences}x) sugerem perda gradual de interesse")
        if outs > 0:
            sinais.append(f"Saídas formais ({outs}x) demonstram limite de tolerância atingido")
        if evasive_answers > 1:
            sinais.append(f"Respostas evasivas ({evasive_answers}x) reduziram confiança")
        
        if not sinais:
            sinais.append("Sessão transcorreu sem sinais críticos de tensão")
        
        return sinais
    
    def _generate_padroes_apresentador(self, events: List[Dict], messages: List[Dict]) -> List[str]:
        """Identifica padrões recorrentes no apresentador"""
        padroes = []
        
        # Analisar respostas do usuário
        user_messages = [m for m in messages if m.get('speaker') == 'USER']
        
        if user_messages:
            # Calcular média de palavras
            total_words = sum(len(m.get('content', '').split()) for m in user_messages)
            avg_words = total_words / len(user_messages) if user_messages else 0
            
            if avg_words > 80:
                padroes.append("Respostas longas demais (média de {:.0f} palavras)".format(avg_words))
            elif avg_words < 10:
                padroes.append("Respostas muito curtas (média de {:.0f} palavras)".format(avg_words))
        
        # Verificar respostas evasivas
        evasive_count = len([e for e in events if e.get('event_type') == EventType.ANSWER_EVASIVE])
        if evasive_count > 2:
            padroes.append("Tendência a desviar de perguntas difíceis")
        
        if not padroes:
            padroes.append("Comunicação direta e objetiva")
        
        return padroes
    
    def _generate_pontos_sustentacao(self, sharks: List[Dict]) -> List[str]:
        """Identifica o que sustentou interesse"""
        pontos = []
        
        active_sharks = [s for s in sharks if not s.get('is_out', False)]
        
        for shark in active_sharks:
            archetype_name = shark.get('archetype_name', '')
            state = shark.get('state', {})
            interest = state.get('interest', 0)
            
            if interest > 60:
                pontos.append(f"{archetype_name} manteve interesse elevado (interesse: {interest:.0f}/100)")
        
        if not pontos:
            pontos.append("Nenhum ponto de sustentação crítico identificado")
        
        return pontos
    
    def _generate_veredito(self, sharks: List[Dict]) -> str:
        """Gera veredito final neutro"""
        sharks_out = len([s for s in sharks if s.get('is_out', False)])
        sharks_active = len(sharks) - sharks_out
        
        if sharks_active == 0:
            return "Nenhum investimento foi mantido até o final."
        elif sharks_active == len(sharks):
            return f"Todos os {len(sharks)} investidores mantiveram interesse até o final da sessão."
        else:
            return f"{sharks_active} de {len(sharks)} investidores mantiveram interesse até o final."