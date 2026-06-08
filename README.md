# ECOSYSTEM VMD GPD MISSION CONTROL

[![CI](https://github.com/valentinmariusdynu-tech/ecosystem-vmd-gpd-mission-control/actions/workflows/ci.yml/badge.svg)](https://github.com/valentinmariusdynu-tech/ecosystem-vmd-gpd-mission-control/actions/workflows/ci.yml)

FastAPI backend for the Sport-OS platform — authentication, athlete profiles, events, and real-time telemetry ingestion.

## Stack
Python 3.11 · FastAPI · SQLAlchemy 2 (async) · Alembic · PostgreSQL 16 · Redis · Docker

## Architecture
```
app/
├── api/v1/       — route handlers grouped by domain
├── core/         — settings, JWT, shared dependencies
├── models/       — SQLAlchemy ORM models
├── schemas/      — Pydantic v2 request/response schemas
├── services/     — business logic (called by routes)
├── workers/      — background tasks
└── main.py
tests/            — pytest + httpx AsyncClient
alembic/          — database migrations
```

## Quick Start
```bash
cp .env.example .env
docker compose up -d db redis
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Dev Commands
```bash
uv run pytest                          # tests
uv run ruff check . --fix             # lint + autofix
uv run mypy app/                       # type check
uv run alembic revision --autogenerate -m "desc"  # new migration
```

## Related Repos
| Repo | Role |
|---|---|
| [sport-os-mobile](https://github.com/valentinmariusdynu-tech/sport-os-mobile) | Mobile client |
| [sport-os-ai](https://github.com/valentinmariusdynu-tech/sport-os-ai) | AI/ML services |
| [sport-os-infra](https://github.com/valentinmariusdynu-tech/sport-os-infra) | Infrastructure |
| [sport-os-docs](https://github.com/valentinmariusdynu-tech/sport-os-docs) | Documentation |
| [sfr-firmware](https://github.com/valentinmariusdynu-tech/sfr-firmware) | SFR device firmware |
