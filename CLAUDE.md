# CLAUDE.md — sport-os multirepo

## Stack v11.0
- Backend: FastAPI + PostgreSQL + Alembic
- Mobile: React Native
- AI: Python (sport-os-ai repo separat)
- Infra: Docker + Hetzner Cloud (CX22→CX32)
- Docs: sport-os-docs

## Convenții cross-repo
- Branch principal: main
- Commit format: type(scope): message
- Tests obligatorii înainte de merge
- Toate secretele în .env (niciodată în cod)

## Repo-uri
- ecosystem-vmd-gpd-mission-control — FastAPI, PostgreSQL, Alembic
- sport-os-mobile — React Native
- sport-os-ai — AI layer separat
- sport-os-infra — Docker Compose, Hetzner
- sport-os-docs — documentație, ADR-uri
- sfr-firmware — firmware dispozitive
