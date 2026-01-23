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
        
        # 13. NOVO: "O QUE ACONTECERIA SE..." - Simulação contrafactual
        contrafactual = self._generate_contrafactual(events, sharks, messages, offers, deals_closed, ending_type)
        
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
            "contrafactual": contrafactual,
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
        """Gera os 'pensamentos' do shark durante a sessão - COM VARIAÇÕES POR ARQUÉTIPO"""
        interest = state.get('interest', 50)
        confianca_ideia = state.get('confianca_ideia', 50)
        confianca_apresentacao = state.get('confianca_apresentacao', 50)
        
        # Diferença entre ideia e apresentação
        idea_vs_presentation = confianca_ideia - confianca_apresentacao
        
        # Frases específicas por arquétipo
        archetype_phrases = {
            "O Operador": {
                "accepted": [
                    "Vi um time que sabe executar. O plano é realista e sei onde posso agregar.",
                    "Gostei da clareza operacional. Dá pra construir algo grande aqui.",
                    "Organização, processos, visão de escala. É o tipo de deal que eu busco."
                ],
                "withdrawn": [
                    "Ofereci minha experiência, mas a hesitação mostrou que não estavam prontos.",
                    "Quem demora demais pra decidir vai demorar demais pra executar.",
                    "Fiz minha oferta. A janela fechou. Vida que segue."
                ],
                "offer_not_accepted": [
                    "Estava disposto a entrar, mas não chegamos a um acordo. Execução requer decisão.",
                    "O deal fazia sentido, mas não rolou. Às vezes a química não bate.",
                    "Ofereci. Não fechou. Talvez em outro momento."
                ],
                "out_low_interest": [
                    "Não vi clareza de execução. Quem vai fazer isso acontecer?",
                    "Faltou mostrar quem é o dono da operação. Ideias sem dono não escalam.",
                    "O pitch foi bonito, mas não vi plano de como chegar lá."
                ],
                "out_idea_vs_presentation": [
                    "A ideia tem mérito, mas não confio que esse time entrega.",
                    "Potencial existe, mas a execução parecia desorganizada.",
                    "Gostei do conceito, mas não vi maturidade operacional."
                ],
                "out_presentation_vs_idea": [
                    "Apresentou bem, mas o modelo de operação não fecha.",
                    "Soube vender, mas não soube explicar como vai operar.",
                    "Eloquência não compensa falta de plano concreto."
                ],
                "out_neutral": [
                    "O risco operacional não compensava o retorno.",
                    "Vi complexidade demais pro estágio atual.",
                    "Não era o tipo de operação que eu consigo ajudar."
                ],
                "stayed_high_interest": [
                    "Quase ofertei. Faltou um número que me desse confiança.",
                    "Vi potencial de execução, mas precisava de mais dados.",
                    "Gostei do que vi, mas não o suficiente pra assinar o cheque."
                ],
                "stayed_medium_interest": [
                    "Interessante, mas não era o perfil de operação que busco.",
                    "Acompanhei com atenção, mas faltou o click.",
                    "Vi mérito, mas não vi fit com meu perfil de investimento."
                ],
                "stayed_low_interest": [
                    "Não era pra mim desde o início. Mas dei uma chance.",
                    "Escutei por educação. Não era meu jogo.",
                    "Fora do meu escopo de atuação."
                ]
            },
            "O Financeiro": {
                "accepted": [
                    "Os números fecham. Margem saudável, unit economics claros. Entrei.",
                    "CAC, LTV, payback — tudo fazia sentido. Deal justo.",
                    "Vi um caminho pra lucratividade. É raro, e por isso investi."
                ],
                "withdrawn": [
                    "Ofereci porque os números pareciam bons. A indecisão me fez repensar.",
                    "Hesitação na mesa é sinal de hesitação na gestão financeira.",
                    "Retirei porque quem não decide rápido geralmente queima caixa rápido."
                ],
                "offer_not_accepted": [
                    "O valuation não batia com minha análise. Não forço deal.",
                    "Estava interessado, mas o preço pedido não justificava o risco.",
                    "Quase fechamos, mas a conta não fechou."
                ],
                "out_low_interest": [
                    "Os números não tinham fundamento. Unit economics inexistentes.",
                    "Não vi caminho pra margem. Sem margem, sem deal.",
                    "Faltou responder sobre CAC, LTV, churn. Básico."
                ],
                "out_idea_vs_presentation": [
                    "A ideia pode ter mercado, mas a apresentação financeira foi fraca.",
                    "Potencial existe, mas não demonstraram que sabem fazer dinheiro.",
                    "Gostei do conceito. Não gostei de como apresentaram os números."
                ],
                "out_presentation_vs_idea": [
                    "Apresentação polida, mas os fundamentos financeiros eram fracos.",
                    "Slides bonitos não compensam unit economics ruins.",
                    "Vendeu bem uma ideia que não se paga."
                ],
                "out_neutral": [
                    "O retorno esperado não justificava o risco do estágio.",
                    "Matematicamente, não fazia sentido pro meu portfólio.",
                    "Prefiro passar a entrar em algo que não fecha a conta."
                ],
                "stayed_high_interest": [
                    "Os números estavam quase lá. Faltou um trimestre de dados.",
                    "Vi potencial de margem, mas precisava de mais tração comprovada.",
                    "Quase ofertei. O valuation me fez recuar."
                ],
                "stayed_medium_interest": [
                    "Números razoáveis, mas não excepcionais. Fiquei na observação.",
                    "Interessante financeiramente, mas sem urgência de investir.",
                    "Vi mérito, mas o retorno ajustado ao risco não me convenceu."
                ],
                "stayed_low_interest": [
                    "Não era o tipo de deal financeiro que busco.",
                    "Os números não me animaram em nenhum momento.",
                    "Fora do perfil de risco/retorno que aceito."
                ]
            },
            "O Cético": {
                "accepted": [
                    "Provaram que o diferencial era real. Não é comum, por isso entrei.",
                    "Conseguiram responder minhas dúvidas mais difíceis. Raro.",
                    "Vi barreira de entrada defensável. É o que procuro."
                ],
                "withdrawn": [
                    "Ofereci, mas a hesitação confirmou minhas dúvidas iniciais.",
                    "Quem não decide na pressão não vai sobreviver na competição.",
                    "Minha oferta tinha prazo. Prazo passou. Simples."
                ],
                "offer_not_accepted": [
                    "Estava disposto a apostar, mas não conseguimos alinhar.",
                    "Fiz uma oferta justa pelo risco. Não aceitaram. Paciência.",
                    "Deal não fechou, mas não me arrependo de ter tentado."
                ],
                "out_low_interest": [
                    "Não vi diferencial. Qualquer um pode copiar isso amanhã.",
                    "Sem barreira de entrada, é questão de tempo até a concorrência esmagar.",
                    "O mercado já tem três soluções iguais. Por que mais uma?"
                ],
                "out_idea_vs_presentation": [
                    "A ideia pode ser boa, mas não me convenceram de que é defensável.",
                    "Potencial existe, mas a apresentação aumentou minhas dúvidas.",
                    "Gostei do conceito, mas não vi como vão se proteger."
                ],
                "out_presentation_vs_idea": [
                    "Apresentação competente, mas a ideia tem flancos demais.",
                    "Soube vender, mas não soube defender. Vulnerável.",
                    "Eloquente, mas sem substância defensável."
                ],
                "out_neutral": [
                    "Muitas incertezas, poucas respostas convincentes.",
                    "Prefiro negócios onde vejo moat claro.",
                    "O risco de ser copiado era maior que o potencial de retorno."
                ],
                "stayed_high_interest": [
                    "Quase me convenceram. Uma resposta melhor e eu teria ofertado.",
                    "Vi algo, mas minhas dúvidas não foram totalmente sanadas.",
                    "Interessante, mas não o suficiente pra vencer meu ceticismo."
                ],
                "stayed_medium_interest": [
                    "Algumas respostas boas, outras nem tanto. Fiquei no muro.",
                    "Vi pontos fortes e fracos. No balanço, não me convenceu.",
                    "Interessante, mas cheio de 'ses' e 'talvez'."
                ],
                "stayed_low_interest": [
                    "Confirmou minhas suspeitas iniciais. Não era pra mim.",
                    "Minhas dúvidas só aumentaram durante a sessão.",
                    "Cada resposta gerava mais perguntas."
                ]
            },
            "O Visionário": {
                "accepted": [
                    "Vi o futuro nessa ideia. Timing certo, mercado grande. Entrei.",
                    "É disruptivo. É ousado. É exatamente o que eu busco.",
                    "Poucos enxergam o que eu vi aqui. Por isso investi."
                ],
                "withdrawn": [
                    "A visão era grande, mas a hesitação mostrou falta de convicção.",
                    "Visionários não hesitam quando o momento chega.",
                    "Ofereci por ver potencial. Retirei por ver medo."
                ],
                "offer_not_accepted": [
                    "Apostei na visão, mas não chegamos a um acordo. Talvez não era o momento.",
                    "Estava disposto a sonhar junto, mas não rolou a conexão.",
                    "Deal grande demais pro founder atual, talvez."
                ],
                "out_low_interest": [
                    "Não vi ousadia. Era mais do mesmo com roupa nova.",
                    "Faltou ambição. Pensar pequeno não me interessa.",
                    "O mercado que miravam era pequeno demais pro meu apetite."
                ],
                "out_idea_vs_presentation": [
                    "A ideia tinha escala, mas não vi paixão na apresentação.",
                    "O conceito era grande, mas o founder parecia pequeno.",
                    "Visão interessante, entrega duvidosa."
                ],
                "out_presentation_vs_idea": [
                    "Apresentou com brilho, mas a ideia era comum.",
                    "Carisma não compensa falta de inovação real.",
                    "Vendeu bem uma ideia que já vi cem vezes."
                ],
                "out_neutral": [
                    "Não senti a faísca. Preciso acreditar pra investir.",
                    "Faltou me fazer sonhar com o que poderia ser.",
                    "O timing não pareceu certo. Talvez cedo demais, talvez tarde."
                ],
                "stayed_high_interest": [
                    "Quase me apaixonei pela ideia. Faltou um empurrão.",
                    "Vi potencial de escala, mas precisava de mais convicção do founder.",
                    "Gostei muito, mas não o suficiente pra assinar o cheque."
                ],
                "stayed_medium_interest": [
                    "Interessante, mas não revolucionário. Fiquei observando.",
                    "Vi mérito, mas não vi a disrupção que busco.",
                    "Bom, mas não excepcional. E eu busco excepcional."
                ],
                "stayed_low_interest": [
                    "Não era o tipo de visão que me anima.",
                    "Muito incremental pro meu gosto.",
                    "Prefiro apostar em moonshots. Isso não era um."
                ]
            }
        }
        
        # Selecionar frases baseado no arquétipo
        phrases = archetype_phrases.get(name, archetype_phrases["O Operador"])
        
        if accepted:
            return random.choice(phrases["accepted"])
        
        if withdrawn:
            return random.choice(phrases["withdrawn"])
        
        if made_offer and not accepted:
            return random.choice(phrases["offer_not_accepted"])
        
        if is_out:
            if interest < 30:
                return random.choice(phrases["out_low_interest"])
            elif idea_vs_presentation > 15:
                return random.choice(phrases["out_idea_vs_presentation"])
            elif idea_vs_presentation < -15:
                return random.choice(phrases["out_presentation_vs_idea"])
            else:
                return random.choice(phrases["out_neutral"])
        
        # Permaneceu mas não ofertou
        if interest > 70:
            return random.choice(phrases["stayed_high_interest"])
        elif interest > 50:
            return random.choice(phrases["stayed_medium_interest"])
        else:
            return random.choice(phrases["stayed_low_interest"])
    
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
        silences_count = len([e for e in events if e.get('event_type') == EventType.SHARK_SILENT])
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
        if silences_count > 2:
            sinais.append(f"Silêncios prolongados ({silences_count}x) indicam desinteresse")
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
        """Gera veredito final com variações cinematográficas"""
        sharks_out = len([s for s in sharks if s.get('is_out', False)])
        offer_events_count = sum(1 for s in sharks if s.get('state', {}).get('has_active_offer', False))
        
        # Calcular média de interesse
        avg_interest = sum(s.get('state', {}).get('interest', 50) for s in sharks) / len(sharks) if sharks else 50
        
        # Calcular média de confiança na ideia vs apresentação
        avg_idea = sum(s.get('state', {}).get('confianca_ideia', 50) for s in sharks) / len(sharks) if sharks else 50
        avg_apresentacao = sum(s.get('state', {}).get('confianca_apresentacao', 50) for s in sharks) / len(sharks) if sharks else 50
        
        if deals:
            deal_verdicts = [
                f"Deal fechado com {len(deals)} investidor(es). A mesa comprou.",
                f"Acordo selado. {len(deals)} investidor(es) viram o que buscavam.",
                "A negociação funcionou. Saiu com investimento no bolso."
            ]
            return random.choice(deal_verdicts)
        
        if ending_type == 'TABLE_BROKEN':
            broken_verdicts = [
                "Mesa quebrada. Havia dinheiro na mesa, mas a indecisão custou tudo.",
                "Ofertas existiram. Decisão não. A oportunidade evaporou.",
                "O painel estava disposto. O founder não estava pronto."
            ]
            return random.choice(broken_verdicts)
        
        if ending_type == 'DEAL_BITTER':
            bitter_verdicts = [
                "Deal fechado, mas a um preço alto. Às vezes vencer custa caro.",
                "Acordo feito, mas com gosto amargo. Pagou-se o preço da hesitação.",
                "Investimento garantido, mas em termos desfavoráveis."
            ]
            return random.choice(bitter_verdicts)
        
        # NO_DEAL com variações baseadas no contexto
        if sharks_out == len(sharks):
            # Todos saíram
            if avg_idea > 60:
                all_out_verdicts = [
                    "O painel não comprou — mas a ideia tinha mérito. A apresentação não convenceu.",
                    "Ideia interessante, founder não preparado. A mesa esvaziou.",
                    "Potencial reconhecido, confiança não construída. Todos saíram."
                ]
            elif avg_interest < 30:
                all_out_verdicts = [
                    "A mesa não viu fit. Simples assim.",
                    "Não era o deal certo para esse painel.",
                    "O pitch não encontrou audiência. Nenhum investidor permaneceu."
                ]
            else:
                all_out_verdicts = [
                    "O painel ouviu, questionou, e decidiu passar.",
                    "Sem alinhamento de visão. A mesa se esvaziou.",
                    "Quatro investidores, zero ofertas. O mercado falou."
                ]
            return random.choice(all_out_verdicts)
        
        elif sharks_out > 0:
            # Alguns saíram
            remaining = len(sharks) - sharks_out
            if avg_apresentacao < avg_idea - 10:
                partial_verdicts = [
                    f"A ideia tinha potencial, mas {sharks_out} investidor(es) perderam confiança na execução.",
                    f"{remaining} permaneceu(ram), mas sem convicção para ofertar. Apresentação matou a ideia.",
                    "O conceito interessou, a defesa não convenceu."
                ]
            elif offer_events_count > 0:
                partial_verdicts = [
                    f"Houve interesse, quase houve deal. {remaining} ficou(aram) na dúvida.",
                    "A mesa esquentou, mas não fechou. Quase lá.",
                    "Ofertas quase aconteceram. O 'quase' é o pior resultado."
                ]
            else:
                partial_verdicts = [
                    f"{sharks_out} investidor(es) saiu(ram). {remaining} permaneceu(ram) observando.",
                    "Interesse parcial, compromisso nenhum.",
                    f"O painel se dividiu. {sharks_out} desistiu(ram), {remaining} hesitou(aram)."
                ]
            return random.choice(partial_verdicts)
        
        else:
            # Ninguém saiu mas não houve deal
            if avg_interest > 60:
                no_exit_verdicts = [
                    "Todos permaneceram interessados, mas ninguém puxou o gatilho.",
                    "Alto interesse, zero ação. Faltou o empurrão final.",
                    "A mesa estava engajada, mas não convicta o suficiente."
                ]
            else:
                no_exit_verdicts = [
                    "O painel acompanhou por educação. Interesse morno.",
                    "Sessão morna. Ninguém saiu, ninguém ofertou.",
                    "Atenção sem entusiasmo. O painel observou, apenas."
                ]
            return random.choice(no_exit_verdicts)
    
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


    def _generate_micro_sinais(self, events: List[Dict], sharks: List[Dict], messages: List[Dict]) -> List[Dict[str, Any]]:
        """
        Gera micro-sinais não verbais baseados nos eventos da sessão.
        Sem texto explicativo, apenas descrição narrativa curta.
        """
        micro_sinais = []
        turno = 0
        
        # Mapear eventos para micro-sinais comportamentais
        for event in events:
            event_type = event.get('event_type', '')
            actor = event.get('actor', '')
            data = event.get('data', {})
            
            if event_type == EventType.QUESTION_ASKED:
                turno += 1
            
            # Shark ficou em silêncio
            if event_type == EventType.SHARK_SILENT:
                micro_sinais.append({
                    "turno": turno,
                    "shark": actor,
                    "sinal": "ficou em silêncio, olhando para os papéis",
                    "traducao_psicologica": "Resposta insuficiente"
                })
            
            # Shark saiu
            elif event_type == EventType.SHARK_OUT:
                micro_sinais.append({
                    "turno": turno,
                    "shark": actor,
                    "sinal": "olhou o relógio, fechou a pasta e recostou na cadeira",
                    "traducao_psicologica": "Perdi interesse"
                })
            
            # Shark fez oferta
            elif event_type == EventType.SHARK_OFFER:
                micro_sinais.append({
                    "turno": turno,
                    "shark": actor,
                    "sinal": "inclinou-se para frente, anotando algo rapidamente",
                    "traducao_psicologica": "Isso importa"
                })
            
            # Shark retirou oferta
            elif event_type == EventType.SHARK_OFFER_WITHDRAWN:
                micro_sinais.append({
                    "turno": turno,
                    "shark": actor,
                    "sinal": "cruzou os braços e balançou a cabeça levemente",
                    "traducao_psicologica": "Oportunidade perdida"
                })
            
            # Conflito entre sharks
            elif event_type == EventType.SHARK_CONFLICT:
                target = data.get('target_shark', '')
                micro_sinais.append({
                    "turno": turno,
                    "shark": actor,
                    "sinal": f"trocou olhares com {target}, sorriso contido",
                    "traducao_psicologica": "Avaliação paralela"
                })
            
            # Resposta evasiva detectada
            elif event_type == EventType.ANSWER_EVASIVE:
                # Adicionar reação de um shark aleatório que não saiu
                active_sharks = [s for s in sharks if not s.get('is_out', False)]
                if active_sharks:
                    random_shark = random.choice(active_sharks)
                    micro_sinais.append({
                        "turno": turno,
                        "shark": random_shark.get('archetype_name', 'Investidor'),
                        "sinal": "franziu a testa e fez uma anotação",
                        "traducao_psicologica": "Resposta não convenceu"
                    })
            
            # Pitch interrompido
            elif event_type == EventType.PITCH_INTERRUPTED:
                micro_sinais.append({
                    "turno": turno,
                    "shark": actor,
                    "sinal": "levantou a mão, interrompendo",
                    "traducao_psicologica": "Preciso de mais detalhes"
                })
            
            # Comentário lateral
            elif event_type == EventType.SHARK_COMMENT_LATERAL:
                # Cochichou com outro shark
                other_sharks = [s.get('archetype_name') for s in sharks if s.get('archetype_name') != actor]
                if other_sharks:
                    target = random.choice(other_sharks)
                    micro_sinais.append({
                        "turno": turno,
                        "shark": actor,
                        "sinal": f"cochichou algo com {target}",
                        "traducao_psicologica": "Avaliação paralela"
                    })
        
        # Adicionar sinais baseados no estado final dos sharks
        for shark in sharks:
            state = shark.get('state', {})
            interest = state.get('interest', 50)
            is_out = shark.get('is_out', False)
            archetype_name = shark.get('archetype_name', '')
            
            # Shark com alto interesse mas não ofertou
            if interest > 70 and not is_out and not any(s['shark'] == archetype_name and 'anotando' in s['sinal'] for s in micro_sinais):
                micro_sinais.append({
                    "turno": turno,  # Final da sessão
                    "shark": archetype_name,
                    "sinal": "manteve contato visual, sorriso contido",
                    "traducao_psicologica": "Gostei, mas não confio ainda"
                })
        
        # Ordenar por turno
        micro_sinais.sort(key=lambda x: x.get('turno', 0))
        
        return micro_sinais[:15]  # Limitar a 15 sinais mais relevantes
    
    def _generate_autopsia(self, events: List[Dict], sharks: List[Dict], messages: List[Dict], 
                          offers: List[Dict], deals: List[Dict], ending_type: str) -> Dict[str, Any]:
        """
        Gera análise profunda no estilo 'autópsia' - não diz se foi bem ou mal,
        mas responde perguntas específicas sobre a sessão.
        """
        autopsia = {
            "momento_irreversivel": None,
            "primeiro_shark_perdido": None,
            "pergunta_nao_respondida": None,
            "onde_perdeu_tracao": None,
            "onde_ganhou_respeito": None,
            "risco_desnecessario": None,
            "decisao_que_matou": None
        }
        
        # 1. "Qual foi o momento irreversível?"
        if ending_type == 'TABLE_BROKEN':
            # Encontrar o momento em que ofertas foram retiradas
            withdrawal_event = next((e for e in events if e.get('event_type') == EventType.SHARK_OFFER_WITHDRAWN), None)
            if withdrawal_event:
                autopsia["momento_irreversivel"] = f"Quando {withdrawal_event.get('actor')} retirou a oferta. A hesitação custou o deal."
            else:
                autopsia["momento_irreversivel"] = "A janela de negociação fechou antes de uma decisão ser tomada."
        elif ending_type == 'NO_DEAL':
            # Encontrar primeira saída significativa
            first_out = next((e for e in events if e.get('event_type') == EventType.SHARK_OUT), None)
            offer_events = [e for e in events if e.get('event_type') == EventType.SHARK_OFFER]
            if not offer_events:
                autopsia["momento_irreversivel"] = "Nenhuma oferta foi feita. O interesse nunca se converteu em compromisso."
            elif first_out:
                autopsia["momento_irreversivel"] = f"A saída de {first_out.get('actor')} mudou a dinâmica. Os outros perderam urgência."
        elif ending_type in ['DEAL_CLOSED', 'DEAL_BITTER']:
            deal_event = next((e for e in events if e.get('event_type') == EventType.DEAL_CLOSED), None)
            if deal_event:
                autopsia["momento_irreversivel"] = f"A decisão de fechar com {deal_event.get('actor')}. Não há volta depois de um aperto de mãos."
        
        # 2. "Qual shark você perdeu primeiro — e por quê?"
        shark_out_events = [e for e in events if e.get('event_type') == EventType.SHARK_OUT]
        if shark_out_events:
            first_out = shark_out_events[0]
            shark_name = first_out.get('actor', '')
            
            # Encontrar o shark correspondente para analisar o motivo
            shark_data = next((s for s in sharks if s.get('archetype_name') == shark_name), None)
            if shark_data:
                state = shark_data.get('state', {})
                confianca_ideia = state.get('confianca_ideia', 50)
                confianca_apresentacao = state.get('confianca_apresentacao', 50)
                
                if confianca_ideia < 40:
                    reason = "A ideia nunca convenceu."
                elif confianca_apresentacao < confianca_ideia - 15:
                    reason = "A ideia tinha potencial, mas as respostas não transmitiram confiança."
                else:
                    reason = "Não viu fit com sua tese de investimento."
                
                autopsia["primeiro_shark_perdido"] = f"{shark_name}. {reason}"
        
        # 3. "O que você nunca respondeu de verdade?"
        evasive_events = [e for e in events if e.get('event_type') == EventType.ANSWER_EVASIVE]
        if evasive_events:
            # Pegar a primeira pergunta que teve resposta evasiva
            first_evasive = evasive_events[0]
            data = first_evasive.get('data', {})
            question_topic = data.get('question_topic', 'uma pergunta crítica')
            autopsia["pergunta_nao_respondida"] = f"Quando perguntaram sobre {question_topic}, a resposta não foi direta."
        else:
            # Verificar se houve perguntas sobre temas difíceis
            questions = [m for m in messages if m.get('message_type') == MessageType.QUESTION]
            difficult_keywords = ['margem', 'concorrência', 'diferencial', 'CAC', 'churn', 'unit economics', 'defensável']
            for q in questions:
                content = q.get('content', '').lower()
                for keyword in difficult_keywords:
                    if keyword in content:
                        autopsia["pergunta_nao_respondida"] = f"A questão sobre {keyword} pode ter ficado no ar."
                        break
                if autopsia["pergunta_nao_respondida"]:
                    break
        
        # 4. "Onde você perdeu tração?"
        # Analisar sequência de eventos negativos
        negative_sequence = []
        for i, event in enumerate(events):
            event_type = event.get('event_type', '')
            if event_type in [EventType.SHARK_OUT, EventType.ANSWER_EVASIVE, EventType.SHARK_OFFER_WITHDRAWN]:
                negative_sequence.append(event)
        
        if len(negative_sequence) >= 2:
            first_negative = negative_sequence[0]
            if first_negative.get('event_type') == EventType.ANSWER_EVASIVE:
                autopsia["onde_perdeu_tracao"] = "Uma resposta evasiva gerou desconfiança que se espalhou pela mesa."
            elif first_negative.get('event_type') == EventType.SHARK_OUT:
                autopsia["onde_perdeu_tracao"] = f"A saída de {first_negative.get('actor')} criou um efeito dominó."
            else:
                autopsia["onde_perdeu_tracao"] = "A janela de oportunidade fechou mais rápido que o esperado."
        
        # 5. "Onde você ganhou respeito?"
        offer_events = [e for e in events if e.get('event_type') == EventType.SHARK_OFFER]
        high_interest_sharks = [s for s in sharks if s.get('state', {}).get('interest', 0) > 65]
        
        if deals:
            autopsia["onde_ganhou_respeito"] = "Fechar o deal mostra que algo funcionou. A pergunta é: foi o bastante?"
        elif len(offer_events) > 1:
            autopsia["onde_ganhou_respeito"] = f"Conseguir {len(offer_events)} ofertas simultaneamente é raro. Houve competição genuína."
        elif offer_events:
            autopsia["onde_ganhou_respeito"] = f"{offer_events[0].get('actor')} viu algo. Só um viu, mas viu."
        elif high_interest_sharks:
            names = ", ".join([s.get('archetype_name', '') for s in high_interest_sharks[:2]])
            autopsia["onde_ganhou_respeito"] = f"{names} mantiveram interesse alto. Quase lá."
        else:
            autopsia["onde_ganhou_respeito"] = "Nenhum ponto de respeito claro foi estabelecido."
        
        # 6. "Onde tomou risco desnecessário?"
        reject_events = [e for e in events if e.get('event_type') == EventType.FOUNDER_REJECTED]
        counter_events = [e for e in events if e.get('event_type') == EventType.FOUNDER_COUNTERED]
        wait_events = [e for e in events if e.get('event_type') == EventType.FOUNDER_WAITED]
        
        if reject_events and not deals:
            shark = reject_events[0].get('data', {}).get('shark', 'um investidor')
            autopsia["risco_desnecessario"] = f"Recusar a oferta de {shark}. Era confiança ou arrogância?"
        elif len(wait_events) > 1:
            autopsia["risco_desnecessario"] = "Esperar demais. Cada turno de espera custou paciência da mesa."
        elif counter_events:
            autopsia["risco_desnecessario"] = "A contra-proposta foi ousada. Nem sempre ousadia é premiada."
        
        # 7. "Qual decisão matou o jogo?" (se aplicável)
        if ending_type == 'TABLE_BROKEN':
            if wait_events and len(wait_events) >= 2:
                autopsia["decisao_que_matou"] = "Esperar demais. A indecisão foi interpretada como falta de convicção."
            elif reject_events:
                autopsia["decisao_que_matou"] = f"Recusar {reject_events[0].get('data', {}).get('shark', '')}. Depois disso, não houve volta."
            else:
                autopsia["decisao_que_matou"] = "Não agir quando havia oferta na mesa. O silêncio também é uma decisão."
        elif ending_type == 'NO_DEAL' and offer_events:
            autopsia["decisao_que_matou"] = "Havia interesse, mas não houve conversão. Alguma coisa no meio do caminho travou."
        
        return autopsia
