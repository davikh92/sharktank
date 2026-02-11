# SharkTank Simulator

Guia mínimo para rodar o projeto com segurança, mantendo compatibilidade com ambientes gerenciados (incluindo Emergent).

## Stack
- Backend: FastAPI + MongoDB.
- Frontend: React (CRA + CRACO).

## 1) Variáveis de ambiente obrigatórias

### Backend (`backend/.env`)
Use `backend/.env.example` como base.

Obrigatórias em qualquer ambiente:
- `MONGO_URL`
- `DB_NAME`

Obrigatórias quando `APP_ENV=production` ou `APP_ENV=staging`:
- `JWT_SECRET` (sem fallback)
- `CORS_ORIGINS` (lista separada por vírgula, sem wildcard)

Opcionais:
- `APP_ENV` (default: `development`)
- `JWT_ALGORITHM` (default: `HS256`)
- `JWT_EXPIRATION_MINUTES` (default: `43200`)

Comportamento de segurança implementado:
- Em `production/staging`: falha na inicialização se `JWT_SECRET` ou `CORS_ORIGINS` estiverem ausentes.
- Em `development` (default):
  - `JWT_SECRET` pode usar fallback local (`fallback-secret`) para não quebrar ambientes legados.
  - `CORS_ORIGINS` default restritivo para `http://localhost:3000,http://127.0.0.1:3000`.

> Compatibilidade com Emergent: se o ambiente atual já funciona sem `JWT_SECRET` explícito, mantenha `APP_ENV=development` e configure `CORS_ORIGINS` conforme a URL de preview quando necessário.

### Frontend (`frontend/.env`)
Use `frontend/.env.example` como base.

Obrigatória:
- `REACT_APP_BACKEND_URL` (ex.: `http://localhost:8000`)

## 2) Instalação

### Opção rápida (Makefile)
```bash
make install
```

### Opção manual
```bash
python -m pip install -r backend/requirements.txt
cd frontend && yarn install --frozen-lockfile
```

## 3) Rodando localmente

### Backend
```bash
make run-backend
```
API disponível em `http://localhost:8000/api`.

### Frontend
```bash
make run-frontend
```
UI disponível em `http://localhost:3000`.

## 4) Testes padronizados

### Backend
```bash
make test-backend
```

### Frontend
```bash
make test-frontend
```

### Tudo
```bash
make test
```

## 5) Troubleshooting rápido
- Erro de coleta no `pytest` por `ModuleNotFoundError`: execute `make install-backend`.
- Frontend sem comunicar com API: confirme `REACT_APP_BACKEND_URL`.
- Erro de CORS em produção/staging: defina `CORS_ORIGINS` explicitamente (sem `*`).


## 6) Qualidade contínua (Semana 2)

### Estrutura modular do backend
O backend foi organizado em camadas para reduzir acoplamento em `server.py`:
- `backend/api/routes/*`: rotas HTTP por domínio.
- `backend/services/*`: regras de serviço reutilizáveis.
- `backend/repositories/*`: acesso a dados.
- `backend/server.py`: bootstrap da aplicação e middleware.

### CI
Pipeline definido em `.github/workflows/ci.yml` com:
- Backend: `flake8` + `pytest -m "not smoke"`.
- Frontend: `yarn lint` + `yarn test:ci`.

### Smoke tests E2E
Fluxo principal (login → criar sessão → iniciar → responder → relatório):
- Arquivo: `backend/tests/test_smoke_main_flow.py`
- Execução manual:
```bash
cd backend && pytest -q -m smoke
```
- Variável opcional para apontar ambiente alvo:
  - `SMOKE_BASE_URL` (default: `REACT_APP_BACKEND_URL` ou `http://localhost:8000`)


## 7) Evolução segura (Semana 3)

### Logs e observabilidade
- Middleware de contexto por request (`backend/observability.py`) com:
  - geração/propagação de `X-Request-Id`,
  - log de início/fim com latência e status.
- Endpoints operacionais:
  - `GET /api/healthz` (liveness)
  - `GET /api/readyz` (readiness com `db.command("ping")`)

### Tratamento de erros da API
- Handlers centralizados em `backend/api/error_handlers.py`:
  - `HTTPException` padronizada,
  - `RequestValidationError` com detalhes,
  - fallback para `Exception` com resposta 500 consistente.
- Respostas de erro incluem `request_id` para correlação com logs.

### Testes expandidos de negociação e finais
- Novo teste unitário: `backend/tests/test_negotiation_endings.py`
  - cenários de finais: `NO_DEAL`, `TABLE_BROKEN`, `DEAL_CLOSED`, `DEAL_BITTER`.
  - cenários de contra-proposta (aceite/rejeição).
- Execução isolada:
```bash
make test-negotiation
```
