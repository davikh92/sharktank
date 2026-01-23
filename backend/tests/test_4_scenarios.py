"""
Testes dos 4 Cenários de Validação - Investor Panel Simulator
Objetivo: Validar calibragem de dificuldade, saídas e ofertas

Cenários:
1. FluxoLocal - Pitch ruim → Rejeição total (esperado: 3-4 OUTs)
2. RelatoXpress - Pitch médio → 1 oferta esperada
3. PulseAds AI - Pitch bom → 2-3 ofertas esperadas
4. NichoForte - Pitch excelente → Muitas propostas
"""
import requests
import time
import os
import json
from dataclasses import dataclass
from typing import List, Dict, Any

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://investor-sim.preview.emergentagent.com').rstrip('/')

@dataclass
class ScenarioResult:
    name: str
    total_turns: int
    sharks_out: List[str]
    offers_received: List[str]
    final_states: Dict[str, Any]
    session_completed: bool
    interruptions: int
    silences: int

def get_auth_token():
    """Login e retorna token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": "testfix@test.com",
        "password": "test123"
    })
    if response.status_code != 200:
        # Tentar registrar
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": "testfix@test.com",
            "password": "test123"
        })
    return response.json()["access_token"]

def run_scenario(token: str, pitch: dict, responses: list, scenario_name: str) -> ScenarioResult:
    """Executa um cenário completo e coleta métricas"""
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"\n{'='*60}")
    print(f"🎬 CENÁRIO: {scenario_name}")
    print(f"{'='*60}")
    
    # Criar sessão
    response = requests.post(f"{BASE_URL}/api/sessions", json={
        "pitch": pitch,
        "reading_hints_enabled": False
    }, headers=headers)
    
    session_id = response.json()["id"]
    print(f"📌 Session ID: {session_id}")
    
    # Iniciar sessão
    requests.post(f"{BASE_URL}/api/sessions/{session_id}/start", headers=headers)
    
    # Métricas
    sharks_out = []
    offers_received = []
    interruptions = 0
    silences = 0
    total_turns = 0
    session_completed = False
    
    # Executar turnos
    for i, user_response in enumerate(responses, 1):
        total_turns = i
        print(f"\n--- Turno {i} ---")
        print(f"  📝 Resposta: '{user_response[:50]}...'")
        
        response = requests.post(
            f"{BASE_URL}/api/sessions/{session_id}/respond",
            json={"content": user_response},
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"  ❌ Erro: {response.text}")
            break
        
        data = response.json()
        
        # Processar eventos
        for event in data['events']:
            if event['event_type'] == 'SHARK_OUT':
                sharks_out.append(event['actor'])
                print(f"  🚪 SHARK_OUT: {event['actor']}")
            elif event['event_type'] == 'SHARK_OFFER':
                offers_received.append(event['actor'])
                print(f"  💰 OFERTA: {event['actor']}")
            elif event['event_type'] == 'PITCH_INTERRUPTED':
                interruptions += 1
                print(f"  ⚡ Interrupção: {event['actor']}")
            elif event['event_type'] == 'SHARK_SILENT':
                silences += 1
        
        # Mostrar mensagens importantes
        for msg in data['messages']:
            if msg['message_type'] == 'OFFER':
                print(f"  💬 Oferta: {msg['content'][:80]}...")
            elif msg['message_type'] == 'OUT_ANNOUNCEMENT':
                print(f"  💬 Saída: {msg['content'][:80]}...")
        
        # Verificar estado
        session_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", headers=headers)
        session_data = session_response.json()
        
        active_sharks = [s for s in session_data['sharks'] if not s['state']['is_out']]
        print(f"  🦈 Sharks ativos: {len(active_sharks)}/4")
        
        # Mostrar estados
        for shark in session_data['sharks']:
            state = shark['state']
            status = "❌ OUT" if state['is_out'] else f"interest={state['interest']:.0f}, patience={state['patience']:.0f}"
            decision = state.get('latent_decision', 'N/A')
            print(f"      {shark['archetype_name']}: {status} [{decision}]")
        
        if data['session_status'] == 'COMPLETED':
            session_completed = True
            print(f"\n  🎬 SESSÃO ENCERRADA no turno {i}")
            break
        
        time.sleep(1.5)  # Rate limiting
    
    # Coletar estado final
    final_response = requests.get(f"{BASE_URL}/api/sessions/{session_id}", headers=headers)
    final_data = final_response.json()
    
    final_states = {}
    for shark in final_data['sharks']:
        final_states[shark['archetype_name']] = {
            'interest': shark['state']['interest'],
            'patience': shark['state']['patience'],
            'confianca': shark['state'].get('confianca', 50),
            'is_out': shark['state']['is_out'],
            'latent_decision': shark['state'].get('latent_decision', 'N/A')
        }
    
    return ScenarioResult(
        name=scenario_name,
        total_turns=total_turns,
        sharks_out=sharks_out,
        offers_received=offers_received,
        final_states=final_states,
        session_completed=session_completed,
        interruptions=interruptions,
        silences=silences
    )

def print_result(result: ScenarioResult, expected_outs: str, expected_offers: str):
    """Imprime resultado formatado"""
    print(f"\n{'='*60}")
    print(f"📊 RESULTADO: {result.name}")
    print(f"{'='*60}")
    print(f"  Turnos: {result.total_turns}")
    print(f"  Sharks OUT: {len(result.sharks_out)} → {result.sharks_out}")
    print(f"  Ofertas: {len(result.offers_received)} → {result.offers_received}")
    print(f"  Interrupções: {result.interruptions}")
    print(f"  Silêncios: {result.silences}")
    print(f"  Sessão completa: {result.session_completed}")
    print(f"\n  📈 Estados Finais:")
    for shark, state in result.final_states.items():
        print(f"    {shark}: interest={state['interest']:.0f}, patience={state['patience']:.0f}, out={state['is_out']}")
    print(f"\n  🎯 Esperado: OUTs={expected_outs}, Ofertas={expected_offers}")
    
    # Validação
    passed = True
    if "3-4" in expected_outs and len(result.sharks_out) < 3:
        print(f"  ⚠️ ALERTA: Esperado 3-4 OUTs, obteve {len(result.sharks_out)}")
        passed = False
    if "1" in expected_offers and len(result.offers_received) < 1 and "ruim" not in result.name.lower():
        print(f"  ⚠️ ALERTA: Esperado pelo menos 1 oferta, obteve {len(result.offers_received)}")
    
    return passed

# ============= CENÁRIO 1: FluxoLocal (Pitch Ruim) =============
def test_scenario_fluxolocal():
    """Pitch genérico sem diferencial - deve ter rejeição alta"""
    token = get_auth_token()
    
    pitch = {
        "titulo": "FluxoLocal",
        "problema": "Comércios locais precisam de mais clientes",
        "solucao": "Marketplace conectando consumidores a comércios locais",
        "mercado": "Milhões de comércios no Brasil",
        "modelo_negocio": "Comissão por transação",
        "tracao": "Alguns usuários beta testando",
        "pedido_valor": "R$500.000",
        "pedido_equity": "15%"
    }
    
    # Respostas RUINS (genéricas, evasivas, sem números)
    responses = [
        "Nossa solução é inovadora e vai revolucionar o mercado local.",
        "O diferencial é a experiência do usuário, muito superior.",
        "Ainda estamos validando o modelo mas os feedbacks são positivos.",
        "O mercado é enorme, bilhões em potencial.",
        "Estamos focados em crescer primeiro, monetizar depois.",
        "A tecnologia é proprietária, não posso detalhar.",
        "Vamos escalar rápido com marketing viral.",
        "Os concorrentes não têm nossa visão.",
        "Confia que vai dar certo.",
        "Temos um roadmap ambicioso para 2026.",
        "O time é muito bom e dedicado.",
        "Vamos pivotar se necessário.",
    ]
    
    result = run_scenario(token, pitch, responses, "FluxoLocal (Pitch Ruim)")
    return print_result(result, "3-4", "0")

# ============= CENÁRIO 2: RelatoXpress (Pitch Médio) =============
def test_scenario_relatoxpress():
    """Pitch com alguns números mas escala questionável - deve ter 1 oferta"""
    token = get_auth_token()
    
    pitch = {
        "titulo": "RelatoXpress",
        "problema": "Influenciadores perdem 5h/semana fazendo relatórios manuais",
        "solucao": "Plataforma que gera relatórios automatizados de métricas",
        "mercado": "5 milhões de influenciadores no Brasil, 50M globalmente",
        "modelo_negocio": "Assinatura mensal de R$49 (básico) a R$199 (premium)",
        "tracao": "800 usuários pagantes, R$35k MRR",
        "pedido_valor": "R$800.000",
        "pedido_equity": "12%"
    }
    
    # Respostas MÉDIAS (alguns números, mas com gaps)
    responses = [
        "Nosso CAC atual é de R$45 via Instagram Ads, com LTV de R$400.",
        "Temos 800 assinantes pagando em média R$45/mês, totalizando R$35k MRR.",
        "O churn é de 8% ao mês, estamos trabalhando para reduzir.",
        "Nosso time tem 4 pessoas, 2 devs e 2 de marketing.",
        "O mercado de creators cresce 25% ao ano segundo estudos.",
        "Nosso diferencial é a integração com TikTok, que poucos têm.",
        "Usamos IA para gerar insights automáticos dos dados.",
        "O roadmap inclui expansão para LATAM em 2026.",
        "Margem bruta de 75% após custos de servidor.",
        "Recebemos alguns investimentos anjo, R$150k até agora.",
        "Break-even projetado para dezembro deste ano.",
        "Principal risco é dependência das APIs das plataformas.",
    ]
    
    result = run_scenario(token, pitch, responses, "RelatoXpress (Pitch Médio)")
    return print_result(result, "1-2", "1")

# ============= CENÁRIO 3: PulseAds AI (Pitch Bom) =============
def test_scenario_pulseads():
    """Pitch sólido com tração forte - deve ter 2-3 ofertas"""
    token = get_auth_token()
    
    pitch = {
        "titulo": "PulseAds AI",
        "problema": "PMEs gastam 30% a mais em ads por falta de otimização",
        "solucao": "IA que otimiza campanhas automaticamente 24/7",
        "mercado": "R$25 bilhões em ads digitais no Brasil, 8% ao ano",
        "modelo_negocio": "% do ad spend otimizado (2-5%) + SaaS",
        "tracao": "R$280k MRR, 150 clientes, 40% crescimento mensal",
        "pedido_valor": "R$3 milhões",
        "pedido_equity": "10%"
    }
    
    # Respostas BOAS (números sólidos, clareza, visão)
    responses = [
        "Nosso CAC é R$1.200, LTV de R$18.000, ratio de 15x.",
        "Gerenciamos R$8 milhões em ad spend mensalmente, cobramos 3% em média.",
        "Margem bruta de 85%, time de 12 pessoas sendo 8 engenheiros.",
        "Churn de apenas 2% ao mês, NPS de 78.",
        "Temos 3 patentes pendentes na nossa tecnologia de otimização.",
        "60% dos clientes vêm por indicação, CAC orgânico de R$200.",
        "Crescemos 40% ao mês nos últimos 8 meses consecutivos.",
        "Principais clientes: e-commerces de moda e suplementos.",
        "Runway atual de 14 meses, break-even em 6 meses.",
        "Competimos com ferramentas de $200/mês, cobramos performance.",
        "Meta: R$1M MRR em 12 meses, IPO em 5 anos.",
        "Time fundador: ex-Google, ex-Meta, ex-Nubank.",
    ]
    
    result = run_scenario(token, pitch, responses, "PulseAds AI (Pitch Bom)")
    return print_result(result, "0-1", "2-3")

# ============= CENÁRIO 4: NichoForte (Pitch Excelente) =============
def test_scenario_nichoforte():
    """Pitch excepcional em nicho dominado - deve ter muitas propostas"""
    token = get_auth_token()
    
    pitch = {
        "titulo": "NichoForte - Gestão para Academias",
        "problema": "90% das academias fecham em 3 anos por má gestão",
        "solucao": "Sistema completo: CRM + financeiro + app aluno + IA retenção",
        "mercado": "35.000 academias no Brasil, R$2 bilhões em software",
        "modelo_negocio": "SaaS de R$299-999/mês por unidade",
        "tracao": "R$890k MRR, 1.200 academias, líder no segmento",
        "pedido_valor": "R$5 milhões",
        "pedido_equity": "8%"
    }
    
    # Respostas EXCELENTES (domínio total, métricas impecáveis)
    responses = [
        "CAC de R$800, LTV de R$28.000, payback em 45 dias.",
        "Somos líderes com 3.5% do mercado, segundo maior tem 1.2%.",
        "Churn de 0.8% ao mês, menor do setor. NPS de 82.",
        "Margem bruta de 88%, EBITDA positivo há 8 meses.",
        "Time de 45 pessoas, 20 em produto/tech.",
        "Receita recorrente de R$890k, crescendo 12% ao mês.",
        "Pipeline de R$2M em contratos enterprise para redes.",
        "3 patentes aprovadas em IA para predição de churn de alunos.",
        "70% das vendas por indicação, CAC caindo 5% ao mês.",
        "Acabamos de fechar contrato com a maior rede: 180 unidades.",
        "Valuation da última rodada: R$50M. Queremos R$80M agora.",
        "Meta: consolidar mercado brasileiro e entrar no México em 2026.",
    ]
    
    result = run_scenario(token, pitch, responses, "NichoForte (Pitch Excelente)")
    return print_result(result, "0", "3-4")

# ============= MAIN =============
def run_all_scenarios():
    """Executa todos os 4 cenários"""
    print("\n" + "="*60)
    print("🚀 INICIANDO TESTES DOS 4 CENÁRIOS")
    print("="*60)
    
    results = []
    
    # Cenário 1: FluxoLocal
    print("\n\n" + "🔴"*20)
    print("CENÁRIO 1: FluxoLocal (Pitch Ruim)")
    print("🔴"*20)
    results.append(("FluxoLocal", test_scenario_fluxolocal()))
    time.sleep(3)
    
    # Cenário 2: RelatoXpress
    print("\n\n" + "🟡"*20)
    print("CENÁRIO 2: RelatoXpress (Pitch Médio)")
    print("🟡"*20)
    results.append(("RelatoXpress", test_scenario_relatoxpress()))
    time.sleep(3)
    
    # Cenário 3: PulseAds AI
    print("\n\n" + "🟢"*20)
    print("CENÁRIO 3: PulseAds AI (Pitch Bom)")
    print("🟢"*20)
    results.append(("PulseAds AI", test_scenario_pulseads()))
    time.sleep(3)
    
    # Cenário 4: NichoForte
    print("\n\n" + "💎"*20)
    print("CENÁRIO 4: NichoForte (Pitch Excelente)")
    print("💎"*20)
    results.append(("NichoForte", test_scenario_nichoforte()))
    
    # Resumo final
    print("\n\n" + "="*60)
    print("📊 RESUMO FINAL DOS 4 CENÁRIOS")
    print("="*60)
    for name, passed in results:
        status = "✅ OK" if passed else "⚠️ VERIFICAR"
        print(f"  {name}: {status}")
    
    return all(r[1] for r in results)

if __name__ == "__main__":
    run_all_scenarios()
