"""
Negotiation Manager - Sistema de Ofertas e Negociação

Implementa a lógica de:
- Tipos de oferta (Alinhada, Agressiva, Criativa)
- Ações do founder (Aceitar, Recusar, Contra-ofertar, Esperar)
- Validade de ofertas
- Conflito entre sharks
- Finais cinematográficos
"""

import random
import uuid
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone
from models import (
    Offer, OfferType, OfferStatus, FounderAction,
    EndingType, SessionPhase, NegotiationState,
    EventType, MessageType, MessageResponse, EventResponse,
    CounterOffer
)

class NegotiationManager:
    """Gerencia toda a lógica de negociação"""
    
    def __init__(self, db, session_id: str, pitch_data: Dict[str, Any]):
        self.db = db
        self.session_id = session_id
        self.pitch_data = pitch_data
        
        # Extrair pedido do pitch
        self.pedido_valor = pitch_data.get('pedido_valor', 'R$ 500.000')
        self.pedido_equity = pitch_data.get('pedido_equity', '10%')
        
    # === CRIAÇÃO DE OFERTAS ===
    
    def determine_offer_type(self, shark_archetype: str, interest: float, confianca: float) -> OfferType:
        """
        Determina o tipo de oferta baseado no arquétipo e estado do shark
        """
        # Financeiro tende a ser mais agressivo
        if shark_archetype == 'financeiro':
            if confianca < 60:
                return OfferType.AGGRESSIVE
            elif interest > 90:
                return OfferType.ALIGNED
            else:
                return OfferType.CREATIVE
        
        # Operador prefere ofertas alinhadas ou agressivas
        elif shark_archetype == 'operador':
            if confianca > 70:
                return OfferType.ALIGNED
            else:
                return OfferType.AGGRESSIVE
        
        # Cético quase sempre agressivo
        elif shark_archetype == 'cetico':
            if interest > 95 and confianca > 80:
                return OfferType.ALIGNED
            else:
                return OfferType.AGGRESSIVE
        
        # Visionário gosta de ofertas criativas
        elif shark_archetype == 'visionario':
            if random.random() < 0.5:
                return OfferType.CREATIVE
            else:
                return OfferType.ALIGNED
        
        # Default
        return OfferType.ALIGNED if random.random() < 0.4 else OfferType.AGGRESSIVE
    
    def generate_offer_values(self, offer_type: OfferType, interest: float) -> Tuple[str, str, Optional[str]]:
        """
        Gera valores da oferta baseado no tipo
        Retorna: (valor, equity, condições)
        """
        # Parsear valores do pedido
        try:
            pedido_valor_num = self._parse_valor(self.pedido_valor)
            pedido_equity_num = self._parse_equity(self.pedido_equity)
        except:
            pedido_valor_num = 500000
            pedido_equity_num = 10
        
        conditions = None
        
        if offer_type == OfferType.ALIGNED:
            # Próximo do pedido (equity 1-3% a mais)
            valor = pedido_valor_num
            equity = pedido_equity_num + random.randint(1, 3)
            if random.random() < 0.3:
                conditions = "com direito de preferência em próximas rodadas"
        
        elif offer_type == OfferType.AGGRESSIVE:
            # Mesmo valor, muito mais equity
            valor = pedido_valor_num
            # Quanto menor o interesse, mais agressivo
            extra_equity = int(10 + (100 - interest) * 0.15)
            equity = pedido_equity_num + extra_equity
            conditions = "sem direito a board seat para o founder"
        
        else:  # CREATIVE
            # Valor diferente, equity diferente
            if random.random() < 0.5:
                # Menos dinheiro, menos equity
                valor = int(pedido_valor_num * 0.6)
                equity = pedido_equity_num + random.randint(3, 8)
                conditions = "com opção de follow-on de mais R$ 300.000"
            else:
                # Mais dinheiro, mais equity
                valor = int(pedido_valor_num * 1.4)
                equity = pedido_equity_num + random.randint(10, 18)
                conditions = "para escalar operação mais rápido"
        
        # Formatar
        valor_str = f"R$ {valor:,.0f}".replace(",", ".")
        equity_str = f"{equity}%"
        
        return valor_str, equity_str, conditions
    
    def calculate_offer_validity(self, interest: float, patience: float) -> int:
        """
        Calcula quantos turnos a oferta fica na mesa
        Interesse alto + paciência alta = mais tempo
        """
        base = 2
        
        if interest > 90 and patience > 50:
            return 3
        elif interest > 80 or patience > 60:
            return 2
        else:
            return 1
    
    def create_offer(
        self, 
        shark_id: str, 
        shark_name: str, 
        shark_archetype: str,
        interest: float,
        confianca: float,
        patience: float,
        turn_count: int
    ) -> Offer:
        """Cria uma nova oferta"""
        offer_type = self.determine_offer_type(shark_archetype, interest, confianca)
        valor, equity, conditions = self.generate_offer_values(offer_type, interest)
        validity = self.calculate_offer_validity(interest, patience)
        
        offer = Offer(
            id=str(uuid.uuid4()),
            shark_id=shark_id,
            shark_name=shark_name,
            session_id=self.session_id,
            offer_type=offer_type,
            valor=valor,
            equity=equity,
            conditions=conditions,
            status=OfferStatus.ACTIVE,
            turns_remaining=validity,
            created_at_turn=turn_count
        )
        
        return offer
    
    # === FALAS DE OFERTA ===
    
    def generate_offer_speech(self, offer: Offer, shark_archetype: str) -> str:
        """Gera a fala do shark ao fazer a oferta"""
        
        if offer.offer_type == OfferType.ALIGNED:
            speeches = [
                f"Eu gosto do negócio e do jeito que você respondeu até aqui. "
                f"Eu te ofereço {offer.valor} por {offer.equity}. "
                f"Se fizer sentido pra você, a gente fecha agora.",
                
                f"Não é uma aposta sem risco, mas eu vejo caminho. "
                f"Minha proposta é simples: {offer.valor} por {offer.equity}.",
                
                f"Olha, eu acredito no que você está construindo. "
                f"Te ofereço {offer.valor} por {offer.equity}. Fechamos?"
            ]
        
        elif offer.offer_type == OfferType.AGGRESSIVE:
            speeches = [
                f"Vou ser direto. Do jeito que está hoje, o risco é todo meu. "
                f"Eu entro com {offer.valor}, mas preciso de {offer.equity}.",
                
                f"Se o negócio estivesse mais redondo, seria outra conversa. "
                f"Nessas condições, ofereço {offer.valor} por {offer.equity}. "
                f"Ou entra assim, ou eu fico fora.",
                
                f"O risco aqui é alto. Não vou fingir que não é. "
                f"{offer.valor} por {offer.equity}. Essa é a única forma que faz sentido pra mim."
            ]
        
        else:  # CREATIVE
            speeches = [
                f"Eu não entro exatamente no que você pediu. "
                f"O que eu posso fazer é o seguinte: {offer.valor} por {offer.equity}.",
                
                f"Tenho uma proposta diferente. {offer.valor} por {offer.equity}. "
                f"{'Isso ' + offer.conditions if offer.conditions else 'Pense nisso.'}",
                
                f"Vou te fazer uma proposta criativa: {offer.valor} por {offer.equity}. "
                f"Isso te força a escolher: crescimento mais rápido ou menos diluição."
            ]
        
        speech = random.choice(speeches)
        
        # Adicionar condições se houver
        if offer.conditions and offer.conditions not in speech:
            speech += f" Condição: {offer.conditions}."
        
        return speech
    
    def generate_pressure_speech(self, offer: Offer, turns_left: int) -> str:
        """Gera fala de pressão quando oferta está expirando"""
        
        if turns_left == 1:
            speeches = [
                "Minha oferta está na mesa agora. Se você quiser esperar, eu entendo — mas eu não prometo manter.",
                "Última chance. Depois disso, não tem mais conversa.",
                "Eu preciso de uma resposta. Agora ou a oferta cai."
            ]
        else:
            speeches = [
                "Tudo bem você querer ouvir os outros. Só entenda que tempo aqui não é neutro.",
                "Eu ainda estou interessado, mas não vou esperar pra sempre.",
                "A oferta continua na mesa. Por enquanto."
            ]
        
        return random.choice(speeches)
    
    def generate_withdrawal_speech(self, shark_archetype: str) -> str:
        """Gera fala quando shark retira oferta"""
        speeches = [
            "Tempo esgotado. Eu retiro minha proposta.",
            "Você hesitou demais. Estou fora.",
            "A janela fechou. Minha oferta não existe mais.",
            "Tudo bem. Boa sorte com o restante da mesa."
        ]
        return random.choice(speeches)
    
    # === REAÇÕES DO SHARK ÀS AÇÕES DO FOUNDER ===
    
    def generate_accept_reaction(self, offer: Offer) -> str:
        """Reação quando founder aceita"""
        speeches = [
            f"Fechado. {offer.valor} por {offer.equity}. Bem-vindo ao time.",
            f"Ótimo. Vamos fazer esse negócio acontecer.",
            f"Acordo feito. Agora é execução."
        ]
        return random.choice(speeches)
    
    def generate_reject_reaction(self, shark_archetype: str, will_stay: bool) -> str:
        """Reação quando founder recusa"""
        if will_stay:
            speeches = [
                "Tudo bem. Só queria ter certeza que você sabe exatamente o que está recusando.",
                "Ok. Vou observar como a mesa reage.",
                "Entendi. Vamos ver se aparece algo melhor pra você."
            ]
        else:
            speeches = [
                "Então eu retiro minha proposta. Boa sorte com o restante da mesa.",
                "Pra mim não fecha. Estou fora.",
                "Essa era minha melhor condição. Não vou mais longe."
            ]
        return random.choice(speeches)
    
    def generate_counter_reaction(self, accepted: bool, original_offer: Offer, counter: CounterOffer) -> str:
        """Reação à contra-proposta do founder"""
        if accepted:
            speeches = [
                f"Eu não concordo com tudo, mas consigo viver com isso. Fechamos em {counter.valor} por {counter.equity}.",
                f"Ok. {counter.valor} por {counter.equity}. Acordo feito.",
                f"Você negociou bem. Aceito."
            ]
        else:
            speeches = [
                "Eu respeito sua tentativa, mas minha proposta continua a mesma.",
                f"Não vou chegar em {counter.equity}. Minha oferta original permanece.",
                "Essa contra-proposta não funciona pra mim. A oferta original está na mesa."
            ]
        return random.choice(speeches)
    
    def generate_wait_reaction(self, shark_archetype: str) -> str:
        """Reação quando founder escolhe esperar"""
        speeches = [
            "Tudo bem você querer ouvir os outros. Só entenda que tempo aqui não é neutro.",
            "Se você precisa ouvir todo mundo pra decidir, talvez você ainda não esteja pronto pra captar.",
            "Ok. Mas minha paciência não é infinita."
        ]
        return random.choice(speeches)
    
    # === CONFLITO ENTRE SHARKS ===
    
    def generate_shark_conflict(self, commenting_shark: str, target_shark: str, target_offer: Offer) -> str:
        """Gera comentário de um shark sobre a oferta de outro"""
        speeches = [
            f"Nessas condições, eu não entraria. Pra mim, o risco ainda é alto demais.",
            f"Eu acho que você está pagando caro. Mas cada um joga o jogo do jeito que prefere.",
            f"Se ele aceitar a sua, estou fora.",
            f"{target_offer.equity} nesse estágio? Corajoso.",
            f"Interessante. Não é como eu faria, mas interessante."
        ]
        return random.choice(speeches)
    
    # === FINAIS CINEMATOGRÁFICOS ===
    
    def generate_ending_narration(self, ending_type: EndingType, deals: List[Dict], offers_made: int) -> str:
        """Gera narração final no estilo programa"""
        
        if ending_type == EndingType.DEAL_CLOSED:
            if len(deals) == 1:
                deal = deals[0]
                return (
                    f"Depois de pressão, silêncio e escolhas difíceis… um acordo foi fechado. "
                    f"{deal['shark_name']} entra com {deal['valor']} por {deal['equity']}."
                )
            else:
                sharks = ", ".join([d['shark_name'] for d in deals])
                return (
                    f"Uma disputa acirrada terminou com múltiplos acordos. "
                    f"{sharks} decidiram investir."
                )
        
        elif ending_type == EndingType.DEAL_BITTER:
            deal = deals[0]
            return (
                f"Você saiu com investimento, mas pagou caro por ele. "
                f"{deal['shark_name']} levou {deal['equity']} — mais do que você planejava. "
                f"Agora é execução. O tempo dirá se valeu a pena."
            )
        
        elif ending_type == EndingType.TABLE_BROKEN:
            return (
                f"Houve interesse. Houve dinheiro na mesa — {offers_made} oferta(s). "
                f"Mas as decisões custaram caro. "
                f"Às vezes o erro não é o negócio. É o tempo."
            )
        
        else:  # NO_DEAL
            if offers_made == 0:
                return (
                    "O painel ouviu. Questionou. E decidiu sair. "
                    "Você saiu sem investimento hoje. "
                    "A pergunta que fica: você convenceu de menos… ou o mercado não era pra eles?"
                )
            else:
                return (
                    "Você saiu sem investimento. "
                    f"Houve {offers_made} oferta(s), mas nenhuma fechou. "
                    "Às vezes recusar é estratégia. Às vezes é orgulho. "
                    "Só você sabe qual foi."
                )
    
    def determine_ending_type(
        self, 
        deals: List[Dict], 
        offers_made: int, 
        offers_withdrawn: int,
        original_equity: float
    ) -> EndingType:
        """Determina qual tipo de final"""
        
        if not deals:
            if offers_made > 0 and offers_withdrawn > 0:
                return EndingType.TABLE_BROKEN
            else:
                return EndingType.NO_DEAL
        
        # Teve deal - verificar se foi "amargo"
        deal = deals[0]
        try:
            deal_equity = self._parse_equity(deal.get('equity', '10%'))
            if deal_equity > original_equity * 1.5:  # Mais de 50% a mais que pediu
                return EndingType.DEAL_BITTER
        except:
            pass
        
        return EndingType.DEAL_CLOSED
    
    # === DECISÃO DO SHARK SOBRE CONTRA-PROPOSTA ===
    
    def evaluate_counter_offer(
        self, 
        original_offer: Offer, 
        counter: CounterOffer, 
        shark_interest: float,
        shark_confianca: float
    ) -> bool:
        """
        Avalia se o shark aceita a contra-proposta
        Retorna True se aceita
        """
        try:
            original_equity = self._parse_equity(original_offer.equity)
            counter_equity = self._parse_equity(counter.equity)
            
            # Diferença de equity
            diff = original_equity - counter_equity
            
            # Shark aceita se:
            # 1. Diferença é pequena (até 3%) E interesse alto
            if diff <= 3 and shark_interest > 80:
                return random.random() < 0.7
            
            # 2. Diferença média (3-5%) E interesse muito alto E confiança alta
            if diff <= 5 and shark_interest > 90 and shark_confianca > 70:
                return random.random() < 0.4
            
            # 3. Diferença grande - muito raro aceitar
            if diff <= 8 and shark_interest >= 100 and shark_confianca > 85:
                return random.random() < 0.2
            
            return False
        except:
            return random.random() < 0.3
    
    # === UTILITÁRIOS ===
    
    def _parse_valor(self, valor_str: str) -> int:
        """Converte 'R$ 500.000' para 500000"""
        clean = valor_str.replace("R$", "").replace(".", "").replace(",", "").strip()
        return int(clean)
    
    def _parse_equity(self, equity_str: str) -> float:
        """Converte '15%' para 15.0"""
        clean = equity_str.replace("%", "").strip()
        return float(clean)
