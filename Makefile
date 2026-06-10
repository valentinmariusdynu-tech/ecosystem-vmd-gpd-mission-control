.PHONY: help install dev test lint type docker-up docker-down migrate clean

help:
	@echo "Sport OS Core v2.4 — Sync Hardening"
	@echo "  make install      — Instaleaza dependintele"
	@echo "  make dev          — Porneste serverul"
	@echo "  make test         — Ruleaza toate testele"
	@echo "  make lint         — Verifica codul"
	@echo "  make type         — Type checking"
	@echo "  make migrate      — Ruleaza migratiile"
	@echo "  make docker-up    — Stack Docker"
	@echo "  make docker-down  — Opreste Docker"
	@echo "  make clean        — Curata artefactele"

install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

dev:
	uvicorn main:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

lint:
	black --check src/ tests/
	flake8 src/ tests/
	isort --check-only src/ tests/

type:
	mypy src/

migrate:
	alembic upgrade head

docker-up:
	docker-compose -f docker-compose.dev.yml up -d --build

docker-down:
	docker-compose -f docker-compose.dev.yml down

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -f sport_os.db
