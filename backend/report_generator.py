"""
Report Generator - Relatório como Replay

Gera um relatório completo da sessão com:
1. Linha da negociação (timeline de ofertas)
2. Quem ofertou primeiro / retirou
3. Leitura dos sharks (o que cada um pensou)
4. Pergunta provocativa final
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
import uuid
import random
from models import EventType, MessageType, ReportResponse

class ReportGenerator:
    def __init__(self, db, session_id: str):
        self.db = db
        self.session_id = session_id
    
    async def generate_report(self) -> ReportResponse:
        """Gera relatório completo como replay da sessão"""
        # Buscar dados da sessão
        session = await self.db.sessions.find_one({"id": self.session_id}, {"_id": 0})
        messages = await self.db.messages.find({"session_id": self.session_id}, {"_id": 0}).to_list(1000)
        events = await self.db.events.find({"session_id": self.session_id}, {"_id": 0}).to_list(1000)
        sharks = await self.db.session_sharks.find({"session_id": self.session_id}, {"_id": 0}).to_list(10)
        offers = await self.db.offers.find({"session_id": self.session_id}, {"_id": 0}).to_list(50)
        
        # Dados da sessão
        pitch_evaluation = session.get('pitch_evaluation', {})
        deals_closed = session.get('deals_closed', [])
        ending_type = session.get('ending_type', 'NO_DEAL')
        
        # 1. Síntese (estilo programa)
        sintese = self._generate_sintese(sharks, events, deals_closed, ending_type)
        
        # 2. Linha da negociação (timeline de ofertas)
        linha_tempo = self._generate_linha_negociacao(events, messages, offers)
        
        # 3. Leitura por shark (o que cada um pensou)
        leitura_sharks = self._generate_leitura_sharks(sharks, events, messages, offers, pitch_evaluation)
        
        # 4. Sinais de mesa
        sinais_mesa = self._generate_sinais_mesa(events)
        
        # 5. Padrões do apresentador
        padroes = self._generate_padroes_apresentador(events, messages)
        
        # 6. Pontos de sustentação
        pontos_sustentacao = self._generate_pontos_sustentacao(sharks, deals_closed)
        
        # 7. Veredito
        veredito = self._generate_veredito(sharks, deals_closed, ending_type)
        
        # 8. Momento de virada
        momento_virada = self._identify_turning_point(events, sharks, offers)
        
        # 9. NOVO: Pergunta provocativa final
        pergunta_provocativa = self._generate_pergunta_provocativa(events, offers, deals_closed, ending_type)
        
        # 10. NOVO: Avaliação da ideia vs apresentação
        avaliacao_idea = self._generate_avaliacao_idea(pitch_evaluation, sharks)
        
        # 11. NOVO: Micro-sinais não verbais
        micro_sinais = self._generate_micro_sinais(events, sharks, messages)
        
        # 12. NOVO: Autópsia da sessão (análise profunda)
        autopsia = self._generate_autopsia(events, sharks, messages, offers, deals_closed, ending_type)
        
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
            "pergunta_provocativa": pergunta_provocativa,
            "avaliacao_idea": avaliacao_idea,
            "micro_sinais": micro_sinais,
            "autopsia": autopsia,
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
    
    def _generate_sintese(self, sharks: List[Dict], events: List[Dict], deals: List[Dict], ending_type: str) -> str:
        """Gera síntese estilo programa de TV"""
        if deals:
            if len(deals) == 1:
                deal = deals[0]
                return f"Depois de uma negociação intensa, um acordo foi fechado. {deal.get('shark_name', 'Um investidor')} investiu {deal.get('valor', '')} por {deal.get('equity', '')}."
            else:
                sharks_names = ", ".join([d.get('shark_name', '') for d in deals])
                return f"Uma disputa acirrada terminou com múltiplos acordos. {sharks_names} decidiram investir."
        
        sharks_out = len([s for s in sharks if s.get('is_out', False)])
        offer_events = [e for e in events if e.get('event_type') == EventType.SHARK_OFFER]
        
        if ending_type == 'TABLE_BROKEN':
            return f"Houve interesse. Houve {len(offer_events)} oferta(s) na mesa. Mas as decisões custaram caro. A mesa quebrou."
        elif sharks_out == len(sharks):
            if offer_events:
                return f"Mesmo com {len(offer_events)} oferta(s) feita(s), o acordo não se concretizou. Todos os investidores saíram."
            return "A sessão encerrou sem nenhum investidor mantendo interesse. O painel ouviu, questionou, e saiu."
        elif sharks_out > 0:
            return f"{sharks_out} de {len(sharks)} investidores saíram durante a sessão. O interesse não foi unânime."
        else:
            return "Todos os investidores mantiveram interesse, mas nenhum deal foi fechado."
    
    def _generate_linha_negociacao(self, events: List[Dict], messages: List[Dict], offers: List[Dict]) -> List[Dict[str, str]]:
        """Gera linha do tempo focada em NEGOCIAÇÃO (ofertas, rejeições, deals)"""
        linha = []
        turno = 0
        
        for event in events:
            event_type = event.get('event_type', '')
            actor = event.get('actor', '')
            data = event.get('data', {})
            
            # Eventos de negociação
            if event_type == EventType.SHARK_OFFER:
                turno += 1
                linha.append({
                    "turno": turno,
                    "tipo": "OFERTA",
                    "ator": actor,
                    "descricao": f"{actor} fez uma oferta: {data.get('valor', '')} por {data.get('equity', '')}"
                })
            elif event_type == EventType.SHARK_OFFER_WITHDRAWN:
                linha.append({
                    "turno": turno,
                    "tipo": "RETIRADA",
                    "ator": actor,
                    "descricao": f"{actor} retirou a oferta. Motivo: {data.get('reason', 'Não especificado')}"
                })
            elif event_type == EventType.SHARK_OFFER_IMPROVED:
                linha.append({
                    "turno": turno,
                    "tipo": "MELHORIA",
                    "ator": actor,
                    "descricao": f"{actor} melhorou a oferta para {data.get('new_equity', '')}"
                })
            elif event_type == EventType.FOUNDER_ACCEPTED:
                linha.append({
                    "turno": turno,
                    "tipo": "ACEITE",
                    "ator": "FOUNDER",
                    "descricao": f"Founder aceitou oferta de {actor}"
                })
            elif event_type == EventType.FOUNDER_REJECTED:
                linha.append({
                    "turno": turno,
                    "tipo": "REJEICAO",
                    "ator": "FOUNDER",
                    "descricao": f"Founder rejeitou oferta de {data.get('shark', actor)}"
                })
            elif event_type == EventType.FOUNDER_COUNTERED:
                linha.append({
                    "turno": turno,
                    "tipo": "CONTRA",
                    "ator": "FOUNDER",
                    "descricao": f"Founder contra-ofertou: {data.get('counter_valor', '')} por {data.get('counter_equity', '')}"
                })
            elif event_type == EventType.DEAL_CLOSED:
                linha.append({
                    "turno": turno,
                    "tipo": "DEAL",
                    "ator": actor,
                    "descricao": f"DEAL FECHADO com {actor}! {data.get('valor', '')} por {data.get('equity', '')}"
                })
            elif event_type == EventType.SHARK_OUT:
                linha.append({
                    "turno": turno,
                    "tipo": "SAIDA",
                    "ator": actor,
                    "descricao": f"{actor} saiu da mesa"
                })
            elif event_type == EventType.SHARK_CONFLICT:
                linha.append({
                    "turno": turno,
                    "tipo": "CONFLITO",
                    "ator": actor,
                    "descricao": f"{actor} comentou sobre oferta de {data.get('target_shark', '')}"
                })
        
        # Se não houve eventos de negociação, mostrar eventos gerais
        if not linha:
            turno = 0
            for i, event in enumerate(events[:20]):
                event_type = event.get('event_type', '')
                actor = event.get('actor', '')
                
                if event_type == EventType.QUESTION_ASKED:
                    turno += 1
                    linha.append({
                        "turno": turno,
                        "tipo": "PERGUNTA",
                        "ator": actor,
                        "descricao": f"{actor} fez uma pergunta"
                    })
                elif event_type == EventType.SHARK_OUT:
                    linha.append({
                        "turno": turno,
                        "tipo": "SAIDA",
                        "ator": actor,
                        "descricao": f"{actor} saiu"
                    })
        
        return linha
    
    def _generate_leitura_sharks(self, sharks: List[Dict], events: List[Dict], messages: List[Dict], offers: List[Dict], pitch_evaluation: Dict) -> List[Dict[str, Any]]:
        """Gera leitura individual de cada shark - o que PENSARAM"""
        leitura = []
        
        for shark in sharks:
            archetype_name = shark.get('archetype_name', '')
            state = shark.get('state', {})
            is_out = shark.get('is_out', False)
            
            # Buscar ofertas desse shark
            shark_offers = [o for o in offers if o.get('shark_name') == archetype_name]
            made_offer = len(shark_offers) > 0
            offer_withdrawn = any(o.get('status') == 'WITHDRAWN' for o in shark_offers)
            offer_accepted = any(o.get('status') == 'ACCEPTED' for o in shark_offers)
            
            # Gerar "pensamentos" do shark
            pensamentos = self._generate_shark_thoughts(
                archetype_name, 
                state, 
                is_out, 
                made_offer, 
                offer_withdrawn,
                offer_accepted,
                pitch_evaluation
            )
            
            # Buscar perguntas feitas
            questions = [m for m in messages if m.get('speaker') == archetype_name and m.get('message_type') == MessageType.QUESTION]
            
            leitura_shark = {
                "shark": archetype_name,
                "o_que_buscava": self._get_shark_thesis(archetype_name),
                "o_que_pensou": pensamentos,
                "fez_oferta": made_offer,
                "oferta_retirada": offer_withdrawn,
                "fechou_deal": offer_accepted,
                "resultado": self._get_shark_result(is_out, made_offer, offer_accepted, offer_withdrawn),
                "interesse_final": state.get('interest', 0),
                "confianca_ideia": state.get('confianca_ideia', 50),
                "confianca_apresentacao": state.get('confianca_apresentacao', 50)
            }
            
            leitura.append(leitura_shark)
        
        return leitura
    
    def _generate_shark_thoughts(self, name: str, state: Dict, is_out: bool, made_offer: bool, withdrawn: bool, accepted: bool, pitch_eval: Dict) -> str:
        """Gera os 'pensamentos' do shark durante a sessão"""
        interest = state.get('interest', 50)
        confianca_ideia = state.get('confianca_ideia', 50)
        confianca_apresentacao = state.get('confianca_apresentacao', 50)
        
        # Diferença entre ideia e apresentação
        idea_vs_presentation = confianca_ideia - confianca_apresentacao
        
        if accepted:
            return f"Vi potencial real aqui. O negócio faz sentido para o meu perfil e consegui entrar em termos que funcionam."
        
        if withdrawn:
            return f"Fiz uma oferta, mas o founder hesitou demais. Quando a oportunidade passa, ela não volta."
        
        if made_offer and not accepted:
            return f"Eu estava disposto a investir, mas não chegamos a um acordo. Às vezes o timing não é o certo."
        
        if is_out:
            if interest < 30:
                return f"Desde o início, não vi aderência à minha tese. O pitch não me convenceu do diferencial."
            elif idea_vs_presentation > 15:
                return f"A ideia tinha potencial, mas a apresentação não me deu confiança de que a execução seria boa."
            elif idea_vs_presentation < -15:
                return f"Apresentou bem, mas a ideia em si não me pareceu defensável. Faltou diferencial real."
            else:
                return f"Não encontrei o que buscava. O risco não justificava o potencial que vi."
        
        # Permaneceu mas não ofertou
        if interest > 70:
            return f"Vi potencial, mas ainda não estava convencido o suficiente para fazer uma oferta. Quase lá."
        elif interest > 50:
            return f"Interessante, mas faltaram alguns elementos para eu me sentir confortável em investir."
        else:
            return f"Acompanhei a sessão, mas o negócio não era para mim."
    
    def _get_shark_result(self, is_out: bool, made_offer: bool, accepted: bool, withdrawn: bool) -> str:
        """Retorna o resultado final do shark"""
        if accepted:
            return "DEAL FECHADO"
        if withdrawn:
            return "Oferta Retirada"
        if made_offer:
            return "Ofertou, não fechou"
        if is_out:
            return "Saiu"
        return "Permaneceu interessado"
    
    def _get_shark_thesis(self, archetype_name: str) -> str:
        """Retorna a tese do shark"""
        teses = {
            "O Operador": "Execução clara, time competente, e plano de crescimento realista",
            "O Financeiro": "Unit economics sólidos, margem saudável, e caminho para lucratividade",
            "O Cético": "Diferencial defensável, barreira de entrada, e proteção contra concorrência",
            "O Visionário": "Mercado grande, potencial de escala, e timing certo"
        }
        return teses.get(archetype_name, "Valor sustentável e potencial de retorno")
    
    def _generate_sinais_mesa(self, events: List[Dict]) -> List[str]:
        """Gera lista de sinais da mesa"""
        sinais = []
        
        interruptions = len([e for e in events if e.get('event_type') == EventType.PITCH_INTERRUPTED])
        silences = len([e for e in events if e.get('event_type') == EventType.SHARK_SILENT])
        outs = len([e for e in events if e.get('event_type') == EventType.SHARK_OUT])
        evasive_answers = len([e for e in events if e.get('event_type') == EventType.ANSWER_EVASIVE])
        offers = len([e for e in events if e.get('event_type') == EventType.SHARK_OFFER])
        conflicts = len([e for e in events if e.get('event_type') == EventType.SHARK_CONFLICT])
        
        if offers > 1:
            sinais.append(f"{offers} ofertas geraram competição entre os sharks")
        if conflicts > 0:
            sinais.append(f"Houve tensão entre os investidores ({conflicts} conflito(s))")
        if interruptions > 2:
            sinais.append(f"Múltiplas interrupções ({interruptions}x) indicam impaciência")
        if evasive_answers > 1:
            sinais.append(f"Respostas evasivas ({evasive_answers}x) reduziram confiança da mesa")
        if outs > 2:
            sinais.append(f"Saídas em cascata ({outs}x) sugerem problema sistêmico")
        
        if not sinais:
            sinais.append("Sessão transcorreu com dinâmica normal de questionamento")
        
        return sinais
    
    def _generate_padroes_apresentador(self, events: List[Dict], messages: List[Dict]) -> List[str]:
        """Identifica padrões recorrentes no apresentador"""
        padroes = []
        user_messages = [m for m in messages if m.get('speaker') == 'USER']
        
        if user_messages:
            total_words = sum(len(m.get('content', '').split()) for m in user_messages)
            avg_words = total_words / len(user_messages) if user_messages else 0
            
            if avg_words > 100:
                padroes.append("Respostas muito longas - pode indicar nervosismo ou falta de foco")
            elif avg_words < 15:
                padroes.append("Respostas curtas demais - pode parecer evasivo ou despreparado")
            else:
                padroes.append("Comunicação com tamanho adequado")
        
        evasive_count = len([e for e in events if e.get('event_type') == EventType.ANSWER_EVASIVE])
        if evasive_count > 2:
            padroes.append("Tendência a evitar perguntas difíceis")
        
        return padroes
    
    def _generate_pontos_sustentacao(self, sharks: List[Dict], deals: List[Dict]) -> List[str]:
        """Identifica o que sustentou interesse"""
        pontos = []
        
        if deals:
            pontos.append(f"Negociação bem sucedida com {len(deals)} investidor(es)")
        
        for shark in sharks:
            if not shark.get('is_out', False):
                state = shark.get('state', {})
                if state.get('interest', 0) > 70:
                    pontos.append(f"{shark.get('archetype_name')} manteve alto interesse ({state.get('interest', 0):.0f}/100)")
        
        if not pontos:
            pontos.append("Nenhum ponto de sustentação significativo identificado")
        
        return pontos
    
    def _generate_veredito(self, sharks: List[Dict], deals: List[Dict], ending_type: str) -> str:
        """Gera veredito final"""
        if deals:
            return f"Sessão encerrada com {len(deals)} acordo(s) fechado(s)."
        
        if ending_type == 'TABLE_BROKEN':
            return "Mesa quebrada. Houve interesse, mas as decisões do founder custaram caro."
        
        sharks_out = len([s for s in sharks if s.get('is_out', False)])
        if sharks_out == len(sharks):
            return "Nenhum investidor manteve interesse até o final."
        
        return f"{len(sharks) - sharks_out} de {len(sharks)} investidores mantiveram interesse."
    
    def _identify_turning_point(self, events: List[Dict], sharks: List[Dict], offers: List[Dict]) -> Dict[str, Any]:
        """Identifica quando a mesa virou"""
        first_offer = next((e for e in events if e.get('event_type') == EventType.SHARK_OFFER), None)
        first_out = next((e for e in events if e.get('event_type') == EventType.SHARK_OUT), None)
        first_withdrawal = next((e for e in events if e.get('event_type') == EventType.SHARK_OFFER_WITHDRAWN), None)
        deal_event = next((e for e in events if e.get('event_type') == EventType.DEAL_CLOSED), None)
        
        resultado = {
            "houve_virada": False,
            "descricao": "A sessão seguiu sem grandes viradas.",
            "momento_chave": None
        }
        
        if deal_event:
            resultado["houve_virada"] = True
            resultado["momento_chave"] = "DEAL"
            resultado["descricao"] = f"A virada veio quando {deal_event.get('actor')} fechou o acordo."
        elif first_withdrawal:
            resultado["houve_virada"] = True
            resultado["momento_chave"] = "RETIRADA"
            resultado["descricao"] = f"A mesa virou quando {first_withdrawal.get('actor')} retirou a oferta. A hesitação custou caro."
        elif first_out and first_offer:
            resultado["houve_virada"] = True
            resultado["momento_chave"] = "SAIDA_APOS_OFERTA"
            resultado["descricao"] = f"Houve oferta de {first_offer.get('actor')}, mas {first_out.get('actor')} saiu antes de um acordo."
        elif first_out:
            resultado["houve_virada"] = True
            resultado["momento_chave"] = "PRIMEIRA_SAIDA"
            resultado["descricao"] = f"A primeira saída de {first_out.get('actor')} mudou a dinâmica da mesa."
        
        return resultado
    
    def _generate_pergunta_provocativa(self, events: List[Dict], offers: List[Dict], deals: List[Dict], ending_type: str) -> str:
        """Gera pergunta provocativa final que convida a rejogar"""
        offer_events = [e for e in events if e.get('event_type') == EventType.SHARK_OFFER]
        withdrawal_events = [e for e in events if e.get('event_type') == EventType.SHARK_OFFER_WITHDRAWN]
        reject_events = [e for e in events if e.get('event_type') == EventType.FOUNDER_REJECTED]
        
        if deals:
            return "Se você tivesse negociado mais, conseguiria termos melhores... ou perderia tudo?"
        
        if ending_type == 'TABLE_BROKEN':
            if offer_events:
                first_offer = offer_events[0]
                return f"Se você tivesse aceitado a primeira oferta de {first_offer.get('actor')}, como essa história teria terminado?"
            return "Quanto tempo é tempo demais para decidir quando há dinheiro na mesa?"
        
        if withdrawal_events:
            return "Às vezes a melhor oferta é a que você deixou passar. O que você faria diferente?"
        
        if reject_events:
            return "Você recusou por estratégia ou por orgulho? Só você sabe a resposta."
        
        if offer_events:
            return "Houve interesse. Houve oferta. O que faltou para fechar?"
        
        # Nenhuma oferta
        perguntas = [
            "O problema foi o pitch, a ideia, ou o momento?",
            "Se você pudesse voltar ao início, o que diria diferente?",
            "Às vezes o 'não' de hoje é o 'ainda não' de amanhã. O que precisa mudar?",
            "A pergunta que fica: você convenceu de menos... ou pediu demais?"
        ]
        return random.choice(perguntas)
    
    def _generate_avaliacao_idea(self, pitch_evaluation: Dict, sharks: List[Dict]) -> Dict[str, Any]:
        """Gera avaliação comparativa entre ideia e apresentação"""
        idea_score = pitch_evaluation.get('idea_score', 50)
        idea_tier = pitch_evaluation.get('idea_tier', 'MEDIANA')
        
        # Calcular média de confiança de apresentação dos sharks
        total_apresentacao = 0
        count = 0
        for shark in sharks:
            state = shark.get('state', {})
            if 'confianca_apresentacao' in state:
                total_apresentacao += state['confianca_apresentacao']
                count += 1
        
        apresentacao_score = total_apresentacao / count if count > 0 else 50
        
        # Análise
        if idea_score > apresentacao_score + 15:
            analise = "A ideia é mais forte que a apresentação. Há potencial escondido."
            recomendacao = "Trabalhe a comunicação e prepare-se melhor para as perguntas difíceis."
        elif apresentacao_score > idea_score + 15:
            analise = "A apresentação foi melhor que a ideia. Os sharks perceberam."
            recomendacao = "Fortaleça os fundamentos do negócio: diferencial, mercado, modelo."
        else:
            analise = "Ideia e apresentação estão alinhadas."
            recomendacao = "Continue refinando ambos os aspectos proporcionalmente."
        
        return {
            "idea_score": round(idea_score, 1),
            "idea_tier": idea_tier,
            "apresentacao_score": round(apresentacao_score, 1),
            "analise": analise,
            "recomendacao": recomendacao,
            "componentes": {
                "originalidade": pitch_evaluation.get('originalidade', 50),
                "potencial_mercado": pitch_evaluation.get('potencial_mercado', 50),
                "diferencial_defensavel": pitch_evaluation.get('diferencial_defensavel', 50),
                "clareza_problema": pitch_evaluation.get('clareza_problema', 50),
                "modelo_negocio": pitch_evaluation.get('modelo_negocio', 50)
            }
        }
