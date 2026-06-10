# Sport OS Core v2.4 — Sync Hardening

## Status
**Offline-Sync Production Ready** — Alembic migrations, device-bound auth, conflict engine, schema validation, audit log, CI pipeline.

## Features v2.4

### 🔐 Security
- JWT access (1h) + refresh (7 zile) tokens
- Refresh token rotation + server-side revocation
- Device-bound authentication
- Password policy (min 8 chars, uppercase, lowercase, digit)
- Rate limiting login (5 attempts / 5 min)
- RBAC enforcement pe toate endpoint-urile
- Strict CORS

### 🔄 Sync Engine
- Real conflict detection (stale_data, concurrent_edit, version_mismatch)
- Conflict resolution policies (timestamp_wins, server_wins, manual)
- Entity versioning (entity_version, base_revision, server_revision)
- Idempotency strict (same key + diff payload = conflict)
- Batch processing cu audit

### ✅ Schema Validation
- JSON Schema per event_type
- Schema versioning
- Invalid event rejection
- Payload type checking

### 🗄️ Database
- Alembic migrations (001 initial, 002 refresh tokens, 003 conflicts)
- Versioned schema evolution
- Rollback support

### 📊 Audit Log
- Toate acțiunile critice logate
- IP address + user agent tracking
- Success/failure/denied status
- Resource type + ID tracking

### 🧪 Testing
- Gate 0 integration test complet
- RBAC enforcement tests
- Conflict detection tests
- Password policy tests
- Refresh token rotation tests
- Logout revocation tests

### 🚀 CI/CD
- GitHub Actions workflow
- Python 3.11 + 3.12 matrix
- Lint (black, flake8, isort)
- Type checking (mypy)
- Security scanning (bandit, safety)
- Coverage reporting

## Quick Start

```bash
# Instalare
make install

# Migratii
make migrate

# Development
make dev

# Teste
make test

# Docker
make docker-up
```

## Gate 0 Integration Test

```bash
pytest tests/test_gate0_integration.py -v
```

**Scenariu complet:**
1. Register referee
2. Login
3. Create match
4. Referee check-in
5. Report incident
6. Sync push offline events
7. Validate incident (as VAR)
8. Sync pull
9. Audit log check

## Changelog v2.4.0
- ✅ Alembic migrations (001, 002, 003)
- ✅ Refresh token table cu rotation și revocation
- ✅ Device-bound JWT
- ✅ Conflict engine real
- ✅ Strict schema validation
- ✅ Idempotency strict (same key + diff payload = conflict)
- ✅ Audit log extins (sync, device, conflict, override)
- ✅ Security hardening (env secret, password policy, rate limit, CORS)
- ✅ Gate 0 integration test complet
- ✅ CI pipeline (GitHub Actions)
- ✅ tox.ini pentru multi-env testing
- ✅ setup.py pentru package distribution
