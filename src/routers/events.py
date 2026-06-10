"""
Events Router v2.4 — cu schema validation strict și audit extins.
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, Any
import json

from src.database import get_db
from src.models.event_log import EventLogDB, EventLogCreate
from src.models.audit_log import AuditLogDB
from src.services.security import JWTBearer, SecurityService

router = APIRouter()
auth_scheme = JWTBearer()

# JSON Schema validation (simplified — in production use jsonschema library)
EVENT_SCHEMAS = {
    "goal_scored": {
        "required": ["match_id", "team", "scorer", "minute"],
        "properties": {
            "match_id": {"type": "string"},
            "team": {"type": "string", "enum": ["home", "away"]},
            "scorer": {"type": "string"},
            "minute": {"type": "integer", "minimum": 0, "maximum": 120},
            "assist": {"type": "string"},
        }
    },
    "incident_reported": {
        "required": ["match_id", "incident_type", "minute"],
        "properties": {
            "match_id": {"type": "string"},
            "incident_type": {"type": "string", "enum": ["goal", "yellow_card", "red_card", "foul", "offside", "injury", "substitution", "var_review", "emergency", "other"]},
            "minute": {"type": "integer", "minimum": 0, "maximum": 120},
            "player": {"type": "string"},
            "description": {"type": "string"},
        }
    },
    "referee_checkin": {
        "required": ["match_id", "referee_id", "location"],
        "properties": {
            "match_id": {"type": "string"},
            "referee_id": {"type": "string"},
            "location": {"type": "object", "required": ["lat", "lon"]},
            "device_battery": {"type": "integer", "minimum": 0, "maximum": 100},
        }
    },
}


def validate_payload(event_type: str, payload: dict) -> tuple[bool, Optional[str]]:
    """Validate event payload against schema."""
    schema = EVENT_SCHEMAS.get(event_type)
    if not schema:
        return True, None  # Unknown types allowed (extensibility)

    # Check required fields
    for field in schema.get("required", []):
        if field not in payload:
            return False, f"Missing required field: {field}"

    # Check types (simplified)
    for field, prop in schema.get("properties", {}).items():
        if field in payload:
            expected_type = prop.get("type")
            if expected_type == "string" and not isinstance(payload[field], str):
                return False, f"Field {field} must be string"
            if expected_type == "integer" and not isinstance(payload[field], int):
                return False, f"Field {field} must be integer"
            if expected_type == "object" and not isinstance(payload[field], dict):
                return False, f"Field {field} must be object"

            # Check enum
            if "enum" in prop and payload[field] not in prop["enum"]:
                return False, f"Field {field} must be one of: {prop['enum']}"

            # Check range
            if "minimum" in prop and payload[field] < prop["minimum"]:
                return False, f"Field {field} must be >= {prop['minimum']}"
            if "maximum" in prop and payload[field] > prop["maximum"]:
                return False, f"Field {field} must be <= {prop['maximum']}"

    return True, None


@router.post("/events")
async def ingest_event(
    event: Dict[str, Any],
    background_tasks: BackgroundTasks,
    user: dict = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    """Ingest event cu schema validation strict."""
    if not SecurityService.check_permission(user, "write:events"):
        db.add(AuditLogDB(action="event_ingest_denied", user_id=int(user["sub"]), details={"event_id": event.get("event_id")}, success="denied"))
        db.commit()
        raise HTTPException(status_code=403, detail="Permission denied: write:events required")

    # Strict validation
    required = ["event_id", "event_type", "payload", "idempotency_key", "source_device_id", "event_timestamp", "schema_version"]
    for field in required:
        if field not in event:
            raise HTTPException(status_code=400, detail=f"Missing required field: {field}")

    # Schema version check
    if event.get("schema_version") != "1.0":
        raise HTTPException(status_code=400, detail="Unsupported schema_version. Must be 1.0")

    # Payload validation
    valid, error = validate_payload(event["event_type"], event.get("payload", {}))
    if not valid:
        db.add(AuditLogDB(action="event_validation_failed", user_id=int(user["sub"]), details={"event_id": event.get("event_id"), "error": error}, success="failure"))
        db.commit()
        raise HTTPException(status_code=400, detail=f"Payload validation failed: {error}")

    # Idempotency (strict: same key + diff payload = conflict)
    import hashlib
    new_hash = hashlib.sha256(str(event["payload"]).encode()).hexdigest()

    existing = db.query(EventLogDB).filter(EventLogDB.idempotency_key == event["idempotency_key"]).first()
    if existing:
        if existing.payload_hash == new_hash:
            return {"status": "duplicate", "event_id": event.get("event_id"), "message": "Event already processed"}
        else:
            db.add(AuditLogDB(action="idempotency_conflict", user_id=int(user["sub"]), details={"event_id": event.get("event_id"), "idempotency_key": event["idempotency_key"]}, success="failure"))
            db.commit()
            raise HTTPException(status_code=409, detail="Idempotency conflict: same key, different payload")

    # Persist
    event_log = EventLogDB(
        event_id=event["event_id"],
        event_type=event["event_type"],
        payload=event["payload"],
        payload_hash=new_hash,
        schema_version=event.get("schema_version", "1.0"),
        entity_version=event.get("entity_version", 1),
        base_revision=event.get("base_revision"),
        source_device_id=event["source_device_id"],
        source_service="api",
        idempotency_key=event["idempotency_key"],
        event_timestamp=datetime.fromisoformat(event["event_timestamp"].replace("Z", "+00:00")),
        partition_key=event["source_device_id"][:4],
    )
    db.add(event_log)
    db.commit()
    db.refresh(event_log)

    # Audit
    db.add(AuditLogDB(action="event_ingested", user_id=int(user["sub"]), details={"event_id": event["event_id"], "type": event["event_type"], "schema_validated": True}))
    db.commit()

    return {"status": "accepted", "event_id": event["event_id"], "received_at": datetime.utcnow().isoformat(), "entity_version": event_log.entity_version}


@router.get("/events/{event_id}")
async def get_event(event_id: str, user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """Get event."""
    if not SecurityService.check_permission(user, "read:events"):
        raise HTTPException(status_code=403, detail="Permission denied: read:events required")

    event = db.query(EventLogDB).filter(EventLogDB.event_id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    return {"event_id": event.event_id, "event_type": event.event_type, "payload": event.payload, "schema_version": event.schema_version, "entity_version": event.entity_version}
