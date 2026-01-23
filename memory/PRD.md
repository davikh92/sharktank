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
3. Backend orquestra a dinâmica (turnos, interrupções, saídas)
4. LLM gera falas dos investidores com base na intenção do orquestrador

### Modelo Híbrido de IA
- **Camada 1:** Desgaste natural (paciência diminui a cada turno)
- **Camada 2:** Memória ponderada (histórico de respostas com decaimento)
- **Camada 3:** Confiança implícita (acumula com boas respostas)
- **Camada 4:** Eventos críticos (contradições, insights únicos)
- **Camada 5:** Impacto modulado pela confiança

### Endpoints Principais
- `POST /api/auth/register` - Registro de usuário
- `POST /api/auth/login` - Login
- `POST /api/sessions` - Criar sessão
- `POST /api/sessions/{id}/start` - Iniciar sessão
- `POST /api/sessions/{id}/respond` - Resposta do usuário
- `GET /api/sessions/{id}/report` - Relatório final

## O que foi implementado

### ✅ Concluído (Dez/2025)
- [x] Autenticação completa (JWT)
- [x] CRUD de sessões
- [x] Interface completa (Landing, Auth, NewSession, SessionRoom, Report)
- [x] Orquestrador com Modelo Híbrido
- [x] Integração GPT-5.2
- [x] Dinâmica de saídas de investidores
- [x] **BUG FIX: Persistência de turn_count e estado dos sharks entre turnos**
- [x] Testes automatizados (12/12 passando)

### 🔧 Em Progresso
- [ ] Validação dos 4 cenários de teste (FluxoLocal, RelatoXpress, PulseAds AI, NichoForte)
- [ ] Calibragem final de dificuldade

### 📋 Backlog (P1-P2)
- [ ] Melhorar Relatório Final (releitura comentada da sessão)
- [ ] Integração real com Stripe (substituir fake paywall)
- [ ] Refinamentos visuais na interface de eventos

## Arquivos de Referência
- `/app/backend/server.py` - Rotas da API
- `/app/backend/orchestrator.py` - Lógica do orquestrador
- `/app/backend/models.py` - Modelos de dados
- `/app/frontend/src/pages/SessionRoom.js` - Interface da sessão

## Credenciais de Teste
- Email: `testfix@test.com`
- Senha: `test123`

## Notas
- Sistema de pagamento é um "fake paywall" (MOCKED)
- Emergent LLM Key é usado para GPT-5.2
