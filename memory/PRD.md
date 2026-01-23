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
5. Sistema de negociação com 4 ações do founder

### Sistema de Negociação

#### Tipos de Oferta
- 🟢 **ALIGNED:** Próximo do pedido
- 🟡 **AGGRESSIVE:** Mesmo valor, mais equity
- 🔵 **CREATIVE:** Valor diferente

#### Ações do Founder
1. **ACCEPT** - Aceita a oferta
2. **REJECT** - Recusa
3. **COUNTER** - Contra-proposta
4. **WAIT** - Esperar

#### Finais Cinematográficos
- 🎉 **DEAL_CLOSED** - Acordo fechado
- ⚖️ **DEAL_BITTER** - Acordo amargo
- 🔥 **TABLE_BROKEN** - Mesa quebrada
- ❌ **NO_DEAL** - Sem investimento

## O que foi implementado

### ✅ Concluído (Jan/2026)

#### Core Features
- [x] Autenticação completa (JWT)
- [x] CRUD de sessões
- [x] Orquestrador com Modelo Híbrido
- [x] Integração GPT-5.2
- [x] Sistema de negociação completo
- [x] 4 finais cinematográficos

#### Relatório como "Autópsia"
- [x] Micro-sinais não verbais
- [x] Análise profunda com perguntas-chave
- [x] Avaliação Ideia vs Apresentação
- [x] Pergunta provocativa final
- [x] Linha do tempo da negociação
- [x] Leitura individual de cada shark
- [x] 100+ variações de frases por arquétipo

#### Estados Granulares dos Sharks (NOVO)
- [x] Estados: ATIVO, INTERESSADO, CÉTICO, IMPACIENTE, ÚLTIMA CHANCE, OUT
- [x] Barra de interesse visual para cada shark
- [x] Cores e ícones diferenciados por estado

#### Recovery Window (NOVO)
- [x] Janela de 1-2 turnos para "redenção" antes de sair
- [x] Resposta "ultra objetiva + número concreto" pode salvar
- [x] Não é proteção, é teste de resiliência

#### Arco Dramático do Operador (NOVO)
- [x] Sinaliza frustração antes de sair
- [x] "Última chance em 20 segundos" antes da saída
- [x] Aumenta tensão e sensação de "quase deu"

#### "O QUE ACONTECERIA SE..." (NOVO)
- [x] Simulações contrafactuais no relatório
- [x] Não dá resposta pronta, só abre loop mental
- [x] Hipóteses baseadas em eventos da sessão

#### Guia de Entrada (NOVO)
- [x] Integrado na Landing Page como seção expandível
- [x] Explica o que é (e o que não é) o simulador
- [x] Como o painel pensa
- [x] Regras que não aparecem na tela
- [x] O que acontece depois
- [x] Aviso honesto

#### Nova Página "Nova Sessão"
- [x] 3 steps (Pitch → Painel → Revisar)
- [x] Indicador de "Força do Pitch" (0-100%)
- [x] Dicas contextuais para cada campo
- [x] Contagem de caracteres
- [x] Cálculo de valuation implícito

### 📋 Backlog (Próximas Tarefas)
- [ ] **(P1)** "Recusar exige justificativa" - modal com análise do LLM
- [ ] **(P2)** Integração real com Stripe (substituir fake paywall)

## Arquivos de Referência
- `/app/backend/server.py` - Rotas da API
- `/app/backend/orchestrator.py` - Lógica do orquestrador (com Recovery Window)
- `/app/backend/models.py` - Modelos de dados (com estados granulares)
- `/app/backend/report_generator.py` - Geração de relatório (com contrafactual)
- `/app/frontend/src/pages/Landing.js` - Landing page com guia expandível
- `/app/frontend/src/pages/SessionRoom.js` - Sessão com estados granulares
- `/app/frontend/src/pages/NewSession.js` - Nova sessão com 3 steps
- `/app/frontend/src/pages/Report.js` - Relatório com autópsia e contrafactual

## Credenciais de Teste
- Email: `test@test.com`
- Senha: `password`

## Notas
- Sistema de pagamento é um "fake paywall" (MOCKED)
- Emergent LLM Key é usado para GPT-5.2
