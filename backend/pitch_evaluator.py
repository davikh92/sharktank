"""
Pitch Evaluator - Avaliação da Ideia vs Apresentação

Este módulo separa a avaliação em duas dimensões:
1. IDEIA: Originalidade, potencial de mercado, diferencial defensável
2. APRESENTAÇÃO: Como o founder responde às perguntas

A ideia cria um "piso" de interesse. Um pitch genial mal apresentado
ainda pode gerar ofertas. Um pitch fraco bem apresentado gera desconfiança.
"""

import re
from typing import Dict, Any, Tuple
from dataclasses import dataclass

@dataclass
class PitchScore:
    """Scores da avaliação do pitch"""
    originalidade: float  # 0-100
    potencial_mercado: float  # 0-100
    diferencial_defensavel: float  # 0-100
    clareza_problema: float  # 0-100
    modelo_negocio: float  # 0-100
    
    @property
    def idea_score(self) -> float:
        """Score geral da ideia (média ponderada)"""
        return (
            self.originalidade * 0.25 +
            self.potencial_mercado * 0.25 +
            self.diferencial_defensavel * 0.30 +
            self.clareza_problema * 0.10 +
            self.modelo_negocio * 0.10
        )
    
    @property
    def idea_tier(self) -> str:
        """Classificação da ideia"""
        score = self.idea_score
        if score >= 80:
            return "EXCEPCIONAL"  # Pode gerar múltiplas ofertas
        elif score >= 65:
            return "FORTE"  # Pode gerar 1-2 ofertas
        elif score >= 50:
            return "MEDIANA"  # Pode gerar 0-1 oferta
        elif score >= 35:
            return "FRACA"  # Muito difícil gerar oferta
        else:
            return "RUIM"  # Quase impossível


class PitchEvaluator:
    """
    Avalia a qualidade intrínseca do pitch (a IDEIA, não a apresentação).
    
    Esta avaliação acontece UMA VEZ quando o pitch é submetido,
    e cria um "piso" de interesse para cada shark.
    """
    
    def __init__(self):
        # Palavras-chave para detecção
        self.mercados_saturados = [
            'marketplace', 'delivery', 'rede social', 'app de namoro',
            'uber de', 'airbnb de', 'netflix de', 'amazon de',
            'comércio local', 'e-commerce genérico'
        ]
        
        self.diferenciais_fortes = [
            'patente', 'patenteado', 'proprietário', 'exclusivo',
            'único', 'primeiro', 'pioneiro', 'tecnologia própria',
            'algoritmo', 'machine learning', 'ia proprietária',
            'rede de', 'parceria exclusiva', 'contrato exclusivo',
            'regulação', 'certificação', 'licença'
        ]
        
        self.diferenciais_fracos = [
            'melhor experiência', 'mais fácil', 'mais barato',
            'mais rápido', 'disruptivo', 'revolucionário',
            'inovador', 'game changer', 'transformador'
        ]
        
        self.modelos_validados = [
            'saas', 'assinatura', 'recorrente', 'mrr', 'arr',
            'comissão', 'transação', 'licenciamento', 'franquia'
        ]
        
        self.modelos_arriscados = [
            'publicidade', 'ads', 'freemium', 'grátis primeiro',
            'escalar depois monetizar', 'viral'
        ]
        
        self.sinais_tracao = [
            'cliente', 'usuário', 'pagante', 'mrr', 'arr',
            'faturamento', 'receita', 'contrato', 'piloto',
            'beta', 'validado', 'vendendo'
        ]
    
    def evaluate(self, pitch_data: Dict[str, Any]) -> PitchScore:
        """
        Avalia o pitch e retorna scores.
        
        Args:
            pitch_data: Dados do pitch (titulo, problema, solucao, etc.)
        
        Returns:
            PitchScore com todas as dimensões avaliadas
        """
        # Extrair campos
        titulo = pitch_data.get('titulo', '').lower()
        problema = pitch_data.get('problema', '').lower()
        solucao = pitch_data.get('solucao', '').lower()
        mercado = pitch_data.get('mercado', '').lower()
        modelo_negocio = pitch_data.get('modelo_negocio', '').lower()
        tracao = pitch_data.get('tracao', '').lower()
        diferencial = pitch_data.get('diferencial', '').lower()
        
        # Texto completo para análise
        full_text = f"{titulo} {problema} {solucao} {mercado} {modelo_negocio} {tracao} {diferencial}"
        
        # Avaliar cada dimensão
        originalidade = self._evaluate_originalidade(full_text, titulo, solucao)
        potencial_mercado = self._evaluate_mercado(mercado, full_text)
        diferencial_score = self._evaluate_diferencial(full_text, diferencial, solucao)
        clareza_problema = self._evaluate_problema(problema)
        modelo_score = self._evaluate_modelo(modelo_negocio, tracao, full_text)
        
        return PitchScore(
            originalidade=originalidade,
            potencial_mercado=potencial_mercado,
            diferencial_defensavel=diferencial_score,
            clareza_problema=clareza_problema,
            modelo_negocio=modelo_score
        )
    
    def _evaluate_originalidade(self, full_text: str, titulo: str, solucao: str) -> float:
        """Avalia quão original é a ideia"""
        score = 50.0  # Base
        
        # Penalizar mercados saturados
        for saturado in self.mercados_saturados:
            if saturado in full_text:
                score -= 15
        
        # Penalizar "cópia de X"
        if any(x in full_text for x in ['uber de', 'airbnb de', 'netflix de', 'amazon de']):
            score -= 20
        
        # Bonificar se menciona nicho específico
        nichos_especificos = ['b2b', 'enterprise', 'corporativo', 'industrial', 
                             'saúde', 'educação', 'agro', 'fintech', 'legaltech',
                             'proptech', 'hrtech', 'edtech', 'healthtech']
        for nicho in nichos_especificos:
            if nicho in full_text:
                score += 10
                break
        
        # Bonificar se tem abordagem única clara
        if any(x in full_text for x in ['primeiro a', 'único que', 'ninguém faz', 'inexistente']):
            score += 15
        
        return max(0, min(100, score))
    
    def _evaluate_mercado(self, mercado: str, full_text: str) -> float:
        """Avalia o potencial de mercado"""
        score = 40.0  # Base conservador
        
        # Detectar números no mercado
        numeros = re.findall(r'(\d+(?:[.,]\d+)?)\s*(bilh|milh|mil|bi|mi|m|b)', mercado)
        
        if numeros:
            for num, unidade in numeros:
                valor = float(num.replace(',', '.'))
                if 'bilh' in unidade or 'bi' in unidade or 'b' in unidade:
                    if valor >= 10:
                        score += 30  # Mercado enorme
                    elif valor >= 1:
                        score += 20  # Mercado grande
                elif 'milh' in unidade or 'mi' in unidade or 'm' in unidade:
                    if valor >= 500:
                        score += 15  # Mercado médio-grande
                    elif valor >= 100:
                        score += 10  # Mercado médio
                    else:
                        score += 5   # Mercado pequeno
        
        # Bonificar crescimento mencionado
        if any(x in full_text for x in ['cresce', 'crescimento', 'cagr', '% ao ano', 'expansão']):
            score += 10
        
        # Penalizar mercado vago
        if mercado in ['grande', 'enorme', 'muito grande', 'bilhões', '']:
            score -= 15
        
        return max(0, min(100, score))
    
    def _evaluate_diferencial(self, full_text: str, diferencial: str, solucao: str) -> float:
        """Avalia se o diferencial é defensável"""
        score = 30.0  # Base baixo (diferencial é difícil de ter)
        
        texto_analise = f"{diferencial} {solucao}"
        
        # Diferenciais FORTES (defensáveis)
        for forte in self.diferenciais_fortes:
            if forte in texto_analise:
                score += 20
        
        # Diferenciais FRACOS (copiáveis)
        for fraco in self.diferenciais_fracos:
            if fraco in texto_analise:
                score -= 10
        
        # Bonificar se menciona barreira de entrada
        barreiras = ['regulação', 'certificação', 'anos de desenvolvimento',
                    'dados proprietários', 'base de', 'rede de', 'efeito de rede']
        for barreira in barreiras:
            if barreira in full_text:
                score += 15
        
        return max(0, min(100, score))
    
    def _evaluate_problema(self, problema: str) -> float:
        """Avalia a clareza do problema"""
        score = 50.0
        
        # Problema muito curto
        if len(problema) < 20:
            score -= 20
        
        # Problema com números (específico)
        if re.search(r'\d+', problema):
            score += 15
        
        # Problema genérico
        genericos = ['precisam de', 'querem', 'necessitam', 'buscam']
        if any(g in problema for g in genericos) and len(problema) < 50:
            score -= 10
        
        # Problema específico (bom)
        if any(x in problema for x in ['perdem', 'gastam', 'desperdiçam', 'falham', 'morrem', 'fecham']):
            score += 10
        
        return max(0, min(100, score))
    
    def _evaluate_modelo(self, modelo: str, tracao: str, full_text: str) -> float:
        """Avalia o modelo de negócio e tração"""
        score = 40.0
        
        # Modelos validados
        for validado in self.modelos_validados:
            if validado in modelo or validado in full_text:
                score += 15
                break
        
        # Modelos arriscados
        for arriscado in self.modelos_arriscados:
            if arriscado in modelo:
                score -= 10
        
        # Tração real
        for sinal in self.sinais_tracao:
            if sinal in tracao:
                score += 5
        
        # Números na tração (muito bom)
        if re.search(r'r\$\s*\d+', tracao) or re.search(r'\d+\s*k', tracao):
            score += 15
        
        # Unit economics mencionados
        if any(x in full_text for x in ['cac', 'ltv', 'margem', 'payback', 'churn']):
            score += 10
        
        return max(0, min(100, score))
    
    def get_shark_initial_interest(self, pitch_score: PitchScore, shark_archetype: str) -> float:
        """
        Calcula o interesse inicial de cada shark baseado na IDEIA.
        
        Cada arquétipo valoriza aspectos diferentes:
        - Operador: Clareza do problema, modelo de negócio
        - Financeiro: Potencial de mercado, modelo de negócio
        - Cético: Diferencial defensável (difícil de impressionar)
        - Visionário: Originalidade, potencial de mercado
        """
        base = pitch_score.idea_score
        
        if shark_archetype == 'operador':
            # Operador valoriza execução
            modifier = (
                pitch_score.clareza_problema * 0.3 +
                pitch_score.modelo_negocio * 0.4 +
                pitch_score.diferencial_defensavel * 0.3
            ) / 100 * 20  # ±20 pontos
            return base + modifier - 10
        
        elif shark_archetype == 'financeiro':
            # Financeiro valoriza números
            modifier = (
                pitch_score.potencial_mercado * 0.4 +
                pitch_score.modelo_negocio * 0.4 +
                pitch_score.diferencial_defensavel * 0.2
            ) / 100 * 20
            return base + modifier - 10
        
        elif shark_archetype == 'cetico':
            # Cético é difícil - começa mais baixo
            modifier = (
                pitch_score.diferencial_defensavel * 0.5 +
                pitch_score.clareza_problema * 0.3 +
                pitch_score.modelo_negocio * 0.2
            ) / 100 * 15
            return base + modifier - 20  # Sempre começa mais baixo
        
        elif shark_archetype == 'visionario':
            # Visionário valoriza escala e originalidade
            modifier = (
                pitch_score.originalidade * 0.4 +
                pitch_score.potencial_mercado * 0.4 +
                pitch_score.diferencial_defensavel * 0.2
            ) / 100 * 20
            return base + modifier - 5
        
        return base
    
    def get_offer_probability_multiplier(self, pitch_score: PitchScore) -> float:
        """
        Retorna multiplicador de probabilidade de oferta baseado na ideia.
        
        - RUIM: 0.1x (quase impossível)
        - FRACA: 0.3x
        - MEDIANA: 0.6x
        - FORTE: 1.0x
        - EXCEPCIONAL: 1.5x
        """
        tier = pitch_score.idea_tier
        multipliers = {
            "RUIM": 0.1,
            "FRACA": 0.3,
            "MEDIANA": 0.6,
            "FORTE": 1.0,
            "EXCEPCIONAL": 1.5
        }
        return multipliers.get(tier, 0.5)
    
    def can_shark_see_potential(self, pitch_score: PitchScore, presentation_score: float) -> bool:
        """
        Verifica se o shark "vê além" de uma apresentação ruim.
        
        Se a ideia é forte mas a apresentação é fraca,
        sharks experientes podem perceber o potencial.
        """
        idea = pitch_score.idea_score
        
        # Se a ideia é FORTE ou EXCEPCIONAL e apresentação é ruim
        if idea >= 65 and presentation_score < 40:
            # 40% de chance de perceber o potencial
            return True  # Retorna True, a probabilidade será calculada no orchestrator
        
        return False
    
    def get_skepticism_level(self, pitch_score: PitchScore, presentation_score: float) -> str:
        """
        Detecta se apresentação boa esconde ideia fraca.
        
        Returns:
            - "CONFIANTE": Ideia e apresentação alinhadas
            - "DESCONFIADO": Apresentação boa, ideia fraca (red flag)
            - "CURIOSO": Ideia boa, apresentação fraca (potencial escondido)
        """
        idea = pitch_score.idea_score
        
        # Apresentação muito melhor que a ideia = suspeito
        if presentation_score > idea + 20:
            return "DESCONFIADO"
        
        # Ideia muito melhor que apresentação = potencial
        if idea > presentation_score + 20:
            return "CURIOSO"
        
        return "CONFIANTE"
