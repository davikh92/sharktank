.PHONY: help install-backend install-frontend install test-backend test-frontend test lint-backend lint-frontend lint run-backend run-frontend

help:
	@echo "Targets disponíveis:"
	@echo "  install-backend  - instala dependências Python do backend"
	@echo "  install-frontend - instala dependências JS do frontend"
	@echo "  install          - instala backend + frontend"
	@echo "  test-backend     - executa pytest no backend"
	@echo "  test-frontend    - executa testes do frontend (modo CI)"
	@echo "  test             - executa backend + frontend"
	@echo "  lint-backend     - executa flake8 no backend"
	@echo "  lint-frontend    - executa eslint no frontend"
	@echo "  lint             - executa lint backend + frontend"
	@echo "  run-backend      - sobe API FastAPI em http://localhost:8000"
	@echo "  run-frontend     - sobe frontend em http://localhost:3000"

install-backend:
	python -m pip install -r backend/requirements.txt

install-frontend:
	cd frontend && yarn install --frozen-lockfile

install: install-backend install-frontend

test-backend:
	cd backend && pytest -q

test-frontend:
	cd frontend && yarn test:ci

test: test-backend test-frontend

test-negotiation:
	cd backend && pytest -q tests/test_negotiation_endings.py

lint-backend:
	flake8 backend --exclude backend/tests,__pycache__

lint-frontend:
	cd frontend && yarn lint

lint: lint-backend lint-frontend

run-backend:
	cd backend && uvicorn server:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && yarn start
