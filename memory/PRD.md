# Investor Panel Simulator - PRD

## Problema Original
Construir uma aplicação web full-stack chamada "Investor Panel Simulator" que simula um painel de 4 investidores interrogando um usuário sobre um pitch de negócios de forma REALISTA e DIFÍCIL.

## Stack Técnica
- **Frontend:** React + TailwindCSS
- **Backend:** FastAPI + Python
- **Database:** MongoDB (Motor async driver)
- **IA:** OpenAI GPT-5.2 via Emergent LLM Key

## Arquitetura

### Core Loop
1. Usuário submete um pitch com dados do negócio
2. Painel de 4 "sharks" (Operador, Financeiro, Cético, Visionário) interroga o usuário
3. Backend orquestra a dinâmica (turnos, interrupções, saídas, OFERTAS)
4. LLM gera falas dos investidores com base na intenção do orquestrador
5. **NOVO:** Sistema de negociação com 4 ações do founder

### Sistema de Negociação (NOVO)

#### Tipos de Oferta
- 🟢 **ALIGNED:** Próximo do pedido (500k/10% → 500k/12%)
- 🟡 **AGGRESSIVE:** Mesmo valor, mais equity (500k/25%)
- 🔵 **CREATIVE:** Valor diferente (300k/15% ou 700k/25%)

#### Ações do Founder
1. **ACCEPT** - Aceita a oferta (fecha deal)
2. **REJECT** - Recusa (shark pode sair ou ficar)
3. **COUNTER** - Contra-proposta (shark avalia)
4. **WAIT** - Esperar outras ofertas (aumenta fadiga)

#### Finais Cinematográficos
- 🎉 **DEAL_CLOSED** - Acordo fechado
- ⚖️ **DEAL_BITTER** - Acordo amargo (pagou caro)
- 🔥 **TABLE_BROKEN** - Mesa quebrada (tinha oferta, perdeu)
- ❌ **NO_DEAL** - Sem investimento

### Endpoints Principais
- `POST /api/auth/register` - Registro de usuário
- `POST /api/auth/login` - Login
- `POST /api/sessions` - Criar sessão
- `POST /api/sessions/{id}/start` - Iniciar sessão
- `POST /api/sessions/{id}/respond` - Resposta do usuário
- `POST /api/sessions/{id}/founder-action` - **NOVO** Ação do founder (negociação)
- `GET /api/sessions/{id}/offers` - **NOVO** Ofertas ativas
- `GET /api/sessions/{id}/report` - Relatório final

## O que foi implementado

### ✅ Concluído (Jan/2026)
- [x] Autenticação completa (JWT)
- [x] CRUD de sessões
- [x] Interface completa (Landing, Auth, NewSession, SessionRoom, Report)
- [x] Orquestrador com Modelo Híbrido
- [x] Integração GPT-5.2
- [x] Dinâmica de saídas de investidores
- [x] BUG FIX: Persistência de turn_count e estado dos sharks entre turnos
- [x] CALIBRAGEM: Validação dos 4 cenários de teste
- [x] **SISTEMA DE NEGOCIAÇÃO COMPLETO:**
  - [x] 3 tipos de oferta (Aligned, Aggressive, Creative)
  - [x] 4 ações do founder (Accept, Reject, Counter, Wait)
  - [x] Validade de ofertas (1-3 turnos)
  - [x] Pressão de tempo ("Minha oferta está na mesa agora")
  - [x] Conflito entre sharks
  - [x] 4 finais cinematográficos
  - [x] Interface de negociação no frontend

### 📋 Backlog (P1-P2)
- [ ] Melhorar Relatório Final (releitura comentada da sessão)
- [ ] Integração real com Stripe (substituir fake paywall)
- [ ] Refinamentos visuais na interface de eventos
- [ ] Ajuste fino da avaliação da IDEIA vs APRESENTAÇÃO

## Arquivos de Referência
- `/app/backend/server.py` - Rotas da API
- `/app/backend/orchestrator.py` - Lógica do orquestrador
- `/app/backend/negotiation_manager.py` - **NOVO** Sistema de negociação
- `/app/backend/models.py` - Modelos de dados
- `/app/frontend/src/pages/SessionRoom.js` - Interface da sessão (com negociação)
- `/app/RELATORIO_CALIBRAGEM_FINAL.md` - Relatório de testes

## Credenciais de Teste
- Email: `testfix@test.com`
- Senha: `test123`

## Notas
- Sistema de pagamento é um "fake paywall" (MOCKED)
- Emergent LLM Key é usado para GPT-5.2
