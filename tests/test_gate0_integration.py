"""
Gate 0 Integration Test — end-to-end complet.
Scenariu: register → login → create match → check-in → incident → sync → validate → audit check
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database import Base, get_db
from main import app

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}, poolclass=StaticPool)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


@pytest.fixture(scope="function", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


class TestGate0Integration:
    """Test complet Gate 0 — toate acțiunile într-un flux."""

    def test_complete_gate0_flow(self):
        """Flux complet Gate 0."""

        # 1. Register referee
        print("
[1/9] Register referee...")
        r = client.post("/v1/auth/register", json={
            "email": "referee@gate0.test",
            "password": "SecurePass123",
            "first_name": "Gate0",
            "last_name": "Referee",
            "role": "referee",
            "device_id": "dev_gate0_001",
        })
        assert r.status_code in [200, 201]
        tokens = r.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]
        print(f"   ✅ Registered: {tokens['user']['email']}")

        # 2. Login
        print("
[2/9] Login...")
        r = client.post("/v1/auth/login", json={
            "email": "referee@gate0.test",
            "password": "SecurePass123",
            "device_id": "dev_gate0_001",
        })
        assert r.status_code == 200
        access_token = r.json()["access_token"]
        print("   ✅ Logged in")

        # 3. Create match
        print("
[3/9] Create match...")
        r = client.post("/v1/matches", json={
            "match_id": "match_gate0_001",
            "home_team": "Offside Arena",
            "away_team": "D'Angelo",
            "scheduled_at": "2026-05-25T10:00:00",
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code in [200, 201]
        print(f"   ✅ Match created: {r.json()['match_id']}")

        # 4. Referee check-in
        print("
[4/9] Referee check-in...")
        r = client.post("/v1/events", json={
            "event_id": "evt_checkin_001",
            "event_type": "referee_checkin",
            "payload": {
                "match_id": "match_gate0_001",
                "referee_id": "ref_001",
                "location": {"lat": 44.4268, "lon": 26.1025},
                "device_battery": 87,
            },
            "idempotency_key": "idemp_checkin_001",
            "source_device_id": "dev_gate0_001",
            "event_timestamp": "2026-05-24T10:00:00",
            "schema_version": "1.0",
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200
        print("   ✅ Check-in ingested")

        # 5. Report incident (online)
        print("
[5/9] Report incident...")
        r = client.post("/v1/incidents", json={
            "incident_id": "inc_gate0_001",
            "match_id": 1,
            "incident_type": "yellow_card",
            "minute": 23,
            "description": "Unsporting behavior",
            "idempotency_key": "idemp_inc_001",
            "local_timestamp": "2026-05-24T10:00:00",
        }, headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code in [200, 201]
        print("   ✅ Incident reported")

        # 6. Sync push (offline events)
        print("
[6/9] Sync push offline events...")
        batch = [
            {
                "event_id": "evt_offline_001",
                "event_type": "goal_scored",
                "payload": {"match_id": "match_gate0_001", "team": "home", "scorer": "Player 7", "minute": 12},
                "idempotency_key": "idemp_off_001",
                "source_device_id": "dev_gate0_001",
                "event_timestamp": "2026-05-24T10:05:00",
                "schema_version": "1.0",
                "entity_version": 1,
            },
            {
                "event_id": "evt_offline_002",
                "event_type": "incident_reported",
                "payload": {"match_id": "match_gate0_001", "incident_type": "foul", "minute": 34, "player": "Player 5"},
                "idempotency_key": "idemp_off_002",
                "source_device_id": "dev_gate0_001",
                "event_timestamp": "2026-05-24T10:10:00",
                "schema_version": "1.0",
                "entity_version": 1,
            },
        ]
        r = client.post("/v1/sync/push?device_id=dev_gate0_001", json=batch, headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200
        result = r.json()
        assert result["processed"] == 2
        print(f"   ✅ Synced: {result['processed']} processed, {result['duplicates']} duplicates, {result['conflicts']} conflicts")

        # 7. Validate incident (as VAR)
        print("
[7/9] Validate incident as VAR...")
        # Register VAR
        r_var = client.post("/v1/auth/register", json={
            "email": "var@gate0.test",
            "password": "SecurePass123",
            "first_name": "VAR",
            "last_name": "Official",
            "role": "var",
        })
        var_token = r_var.json()["access_token"]

        r = client.post("/v1/incidents/inc_gate0_001/validate", json={"status": "approved"}, headers={"Authorization": f"Bearer {var_token}"})
        assert r.status_code == 200
        assert r.json()["validation_status"] == "approved"
        print("   ✅ Incident validated")

        # 8. Pull sync
        print("
[8/9] Sync pull...")
        r = client.get("/v1/sync/pull?device_id=dev_gate0_001&since=2026-05-24T00:00:00", headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200
        events = r.json()["events"]
        print(f"   ✅ Pulled {len(events)} events")

        # 9. Audit check
        print("
[9/9] Audit log check...")
        # Verify audit entries exist
        from src.database import SessionLocal
        db = SessionLocal()
        from src.models.audit_log import AuditLogDB
        audits = db.query(AuditLogDB).all()
        assert len(audits) >= 5  # register, login, match_created, event_ingested, sync_push, incident_validated
        print(f"   ✅ Audit log: {len(audits)} entries")
        db.close()

        print("
" + "=" * 50)
        print("🎉 GATE 0 INTEGRATION TEST — ALL PASSED")
        print("=" * 50)

    def test_rbac_enforcement(self):
        """Test RBAC enforcement throughout flow."""
        # Register spectator
        r = client.post("/v1/auth/register", json={
            "email": "spectator@gate0.test",
            "password": "SecurePass123",
            "first_name": "Spec",
            "last_name": "Tator",
            "role": "spectator",
        })
        spec_token = r.json()["access_token"]

        # Try create match — should fail
        r = client.post("/v1/matches", json={
            "match_id": "match_fail_001",
            "home_team": "A",
            "away_team": "B",
            "scheduled_at": "2026-05-25T10:00:00",
        }, headers={"Authorization": f"Bearer {spec_token}"})
        assert r.status_code == 403

        # Try validate incident — should fail
        r = client.post("/v1/incidents/inc_001/validate", json={"status": "approved"}, headers={"Authorization": f"Bearer {spec_token}"})
        assert r.status_code == 403

        print("   ✅ RBAC enforcement verified")

    def test_conflict_detection(self):
        """Test conflict detection in sync."""
        # Register referee
        r = client.post("/v1/auth/register", json={
            "email": "conflict@gate0.test",
            "password": "SecurePass123",
            "first_name": "Conflict",
            "last_name": "Test",
            "role": "referee",
        })
        token = r.json()["access_token"]

        # Create match
        client.post("/v1/matches", json={
            "match_id": "match_conflict_001",
            "home_team": "A",
            "away_team": "B",
            "scheduled_at": "2026-05-25T10:00:00",
        }, headers={"Authorization": f"Bearer {token}"})

        # First event
        client.post("/v1/events", json={
            "event_id": "evt_conflict_001",
            "event_type": "goal_scored",
            "payload": {"match_id": "match_conflict_001", "team": "home", "scorer": "Player A"},
            "idempotency_key": "idemp_conflict_001",
            "source_device_id": "dev_conflict_001",
            "event_timestamp": "2026-05-24T10:00:00",
            "schema_version": "1.0",
        }, headers={"Authorization": f"Bearer {token}"})

        # Same idempotency key, different payload = conflict
        r = client.post("/v1/sync/push?device_id=dev_conflict_001", json=[{
            "event_id": "evt_conflict_002",
            "event_type": "goal_scored",
            "payload": {"match_id": "match_conflict_001", "team": "home", "scorer": "Player B"},  # Different!
            "idempotency_key": "idemp_conflict_001",  # Same!
            "source_device_id": "dev_conflict_001",
            "event_timestamp": "2026-05-24T10:01:00",
            "schema_version": "1.0",
        }], headers={"Authorization": f"Bearer {token}"})

        assert r.status_code == 200
        result = r.json()
        assert result["conflicts"] == 1
        print(f"   ✅ Conflict detected: {result['conflicts']} conflicts")

    def test_password_policy(self):
        """Test password policy enforcement."""
        # Too short
        r = client.post("/v1/auth/register", json={
            "email": "weak@gate0.test",
            "password": "short",
            "first_name": "Weak",
            "last_name": "Pass",
            "role": "spectator",
        })
        assert r.status_code == 422

        # No uppercase
        r = client.post("/v1/auth/register", json={
            "email": "weak2@gate0.test",
            "password": "lowercase123",
            "first_name": "Weak",
            "last_name": "Pass",
            "role": "spectator",
        })
        assert r.status_code == 422

        # Valid
        r = client.post("/v1/auth/register", json={
            "email": "strong@gate0.test",
            "password": "SecurePass123",
            "first_name": "Strong",
            "last_name": "Pass",
            "role": "spectator",
        })
        assert r.status_code in [200, 201]
        print("   ✅ Password policy enforced")

    def test_refresh_token_rotation(self):
        """Test refresh token rotation."""
        r = client.post("/v1/auth/register", json={
            "email": "refresh@gate0.test",
            "password": "SecurePass123",
            "first_name": "Refresh",
            "last_name": "Test",
            "role": "referee",
        })
        refresh_token = r.json()["refresh_token"]

        # First refresh
        r1 = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r1.status_code == 200
        new_refresh = r1.json()["refresh_token"]

        # Old token should be revoked
        r2 = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r2.status_code == 401  # Revoked

        # New token should work
        r3 = client.post("/v1/auth/refresh", json={"refresh_token": new_refresh})
        assert r3.status_code == 200
        print("   ✅ Refresh token rotation working")

    def test_logout_revokes_tokens(self):
        """Test logout revokes all refresh tokens."""
        r = client.post("/v1/auth/register", json={
            "email": "logout@gate0.test",
            "password": "SecurePass123",
            "first_name": "Logout",
            "last_name": "Test",
            "role": "referee",
        })
        access_token = r.json()["access_token"]
        refresh_token = r.json()["refresh_token"]

        # Logout
        r = client.post("/v1/auth/logout", headers={"Authorization": f"Bearer {access_token}"})
        assert r.status_code == 200

        # Try refresh — should fail
        r = client.post("/v1/auth/refresh", json={"refresh_token": refresh_token})
        assert r.status_code == 401
        print("   ✅ Logout revokes tokens")
