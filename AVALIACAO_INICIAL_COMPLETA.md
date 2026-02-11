# Avaliação Inicial Completa — Projeto SharkTank Simulator

## 1) Objetivo desta avaliação
Esta avaliação inicial consolida o estado atual do projeto (backend + frontend), com foco em:
- arquitetura e organização geral;
- cobertura funcional aparente;
- riscos técnicos e operacionais;
- qualidade de teste e executabilidade local;
- prioridades práticas para estabilização.

---

## 2) Panorama do sistema
O projeto implementa um simulador de painel de investidores no formato “Shark Tank”, com:
- **Backend FastAPI + MongoDB** para autenticação, sessões, orquestração de rodadas, negociação e geração de relatório.
- **Frontend React (CRA + CRACO + Tailwind/Radix)** para fluxo de autenticação, criação/listagem de sessões, sala da sessão e relatório.

A proposta funcional está relativamente completa para um MVP evoluído: além do pitch e perguntas, existe estado de negociação com ofertas/counter-offers e encerramentos narrativos.

---

## 3) Avaliação técnica por camada

### 3.1 Backend
**Pontos fortes**
- API estruturada por recursos de negócio claros (`auth`, `sessions`, `offers`, `report`).
- Modelagem tipada com Pydantic para payloads e respostas.
- Persistência de eventos/mensagens por sessão, favorecendo auditabilidade.
- Componentes especializados (`orchestrator`, `pitch_evaluator`, `report_generator`, `negotiation_manager`) sugerem separação lógica razoável.

**Pontos de atenção**
- **Arquivo `server.py` muito grande e concentrando múltiplas responsabilidades** (rotas + regras de sessão + persistência), dificultando manutenção incremental.
- Dependência forte de variáveis de ambiente críticas (`MONGO_URL`, `DB_NAME`) sem fallback seguro para execução local guiada.
- CORS configurado com `'*'` por padrão (`CORS_ORIGINS`), o que é arriscado para ambientes não-dev.
- JWT com `fallback-secret` caso `JWT_SECRET` não esteja definido: aceitável para dev, inseguro para produção.

### 3.2 Frontend
**Pontos fortes**
- Rotas principais do produto cobertas (`landing`, `auth`, `sessions`, `new`, `room`, `report`).
- `ProtectedRoute` e contexto de autenticação indicam fluxo de sessão coerente.
- Camada de API centralizada em `src/api.js` com interceptor de token.

**Pontos de atenção**
- Dependência de `REACT_APP_BACKEND_URL`; sem configuração adequada, app quebra silenciosamente na integração.
- Estrutura funcional correta, mas sem evidência de suíte de testes frontend ativa/rodando.

---

## 4) Estado de qualidade e testes

### 4.1 O que foi validado agora
1. **Compilação estática de Python**: backend compila sem erro de sintaxe.
2. **Execução de testes backend (`pytest`)**: falha ainda na coleta por ausência de dependência `requests` no ambiente atual.

### 4.2 Interpretação
- Não há indício de erro sintático crítico no backend.
- A suíte automatizada não está “pronta para rodar” no ambiente corrente sem preparação de dependências.
- O principal bloqueio observado nesta rodada é de ambiente (dependency management), não necessariamente falha lógica do código testado.

---

## 5) Riscos prioritários (ordem recomendada)

### P0 — Segurança/Configuração
1. **Secret de JWT com fallback inseguro** em caso de ausência de variável de ambiente.
2. **CORS permissivo por default** (`*`) pode expor API em deploy indevido.

### P1 — Confiabilidade de entrega
3. **Suite de testes sem executabilidade imediata** (falta de dependências no ambiente base).
4. **Monolitização de `server.py`** aumenta risco de regressão e reduz previsibilidade de mudanças.

### P2 — Manutenibilidade
5. Possível ausência de pipeline explícito de lint/type/test para backend e frontend.
6. Falta de documentação operacional clara no `README.md` para onboarding (arquivo atual está vazio de instruções úteis).

---

## 6) Recomendações práticas (plano curto)

### Semana 1 (estabilização)
- Endurecer configurações sensíveis:
  - remover fallback inseguro de JWT em ambiente não-dev;
  - definir CORS restritivo por ambiente.
- Publicar **guia mínimo de execução local** com variáveis obrigatórias e sequência de start.
- Padronizar instalação e execução de testes (`requirements`, script Makefile/npm scripts, docs).

### Semana 2 (qualidade contínua)
- Quebrar `server.py` em módulos de rotas/serviços/repositórios.
- Introduzir checagens em CI:
  - backend: lint + pytest;
  - frontend: lint + testes básicos.
- Adicionar smoke tests de ponta-a-ponta do fluxo principal (login → criar sessão → iniciar → responder → gerar relatório).

### Semana 3 (evolução segura)
- Revisar estratégias de logs, observabilidade e tratamento de erros da API.
- Expandir testes para cenários de negociação e encerramentos especiais.

---

## 7) Conclusão executiva
O produto já demonstra **maturidade funcional de MVP avançado**, especialmente no núcleo de simulação e negociação. O maior gap imediato está em **robustez operacional** (configuração segura, documentação de execução e disciplina de testes/CI). Com ajustes de base, o projeto pode ganhar previsibilidade para evoluir sem perda de qualidade.
