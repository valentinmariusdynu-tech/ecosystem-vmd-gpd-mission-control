"""
Sync Router v2.4 — cu conflict engine real și audit extins.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.database import get_db
from src.models.event_log import EventLogDB
from src.models.audit_log import AuditLogDB
from src.models.conflict import ConflictDB
from src.services.security import JWTBearer, SecurityService
from src.services.sync_engine import SyncEngine

router = APIRouter()
auth_scheme = JWTBearer()


@router.post("/sync/push")
async def sync_push(
    batch: List[Dict[str, Any]],
    device_id: str,
    last_sync_timestamp: Optional[str] = None,
    user: dict = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    """Push batch cu conflict detection real."""
    if not SecurityService.check_permission(user, "write:sync"):
        db.add(AuditLogDB(action="sync_push_denied", user_id=int(user["sub"]), details={"device_id": device_id}, success="denied"))
        db.commit()
        raise HTTPException(status_code=403, detail="Permission denied: write:sync required")

    # Check device binding
    if not SecurityService.check_device_binding(user, device_id):
        raise HTTPException(status_code=403, detail="Device mismatch")

    result = SyncEngine.process_batch(db, batch, device_id)

    # Audit
    db.add(AuditLogDB(
        action="sync_push",
        user_id=int(user["sub"]),
        details={"device_id": device_id, **result},
    ))
    db.commit()

    return result


@router.get("/sync/pull")
async def sync_pull(
    device_id: str,
    since: str,
    limit: int = 100,
    user: dict = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    """Pull events noi."""
    if not SecurityService.check_permission(user, "read:sync"):
        raise HTTPException(status_code=403, detail="Permission denied: read:sync required")

    since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
    events = db.query(EventLogDB).filter(
        EventLogDB.event_timestamp > since_dt,
        EventLogDB.source_device_id != device_id
    ).order_by(EventLogDB.event_timestamp).limit(limit).all()

    db.add(AuditLogDB(action="sync_pull", user_id=int(user["sub"]), details={"device_id": device_id, "count": len(events)}))
    db.commit()

    return {
        "events": [{"event_id": e.event_id, "event_type": e.event_type, "payload": e.payload, "source_device_id": e.source_device_id, "event_timestamp": e.event_timestamp.isoformat() if e.event_timestamp else None, "entity_version": e.entity_version} for e in events],
        "has_more": len(events) == limit,
        "server_timestamp": datetime.utcnow().isoformat(),
    }


@router.get("/sync/status/{device_id}")
async def sync_status(device_id: str, user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """Status sync."""
    if not SecurityService.check_permission(user, "read:sync"):
        raise HTTPException(status_code=403, detail="Permission denied: read:sync required")

    last_event = db.query(EventLogDB).filter(EventLogDB.source_device_id == device_id).order_by(EventLogDB.event_timestamp.desc()).first()
    total_events = db.query(EventLogDB).filter(EventLogDB.source_device_id == device_id).count()
    pending_conflicts = db.query(ConflictDB).filter(ConflictDB.resolution == "pending_manual").count()

    return {
        "device_id": device_id,
        "last_sync": last_event.event_timestamp.isoformat() if last_event and last_event.event_timestamp else None,
        "total_events": total_events,
        "pending_conflicts": pending_conflicts,
        "sync_status": "active" if total_events > 0 else "unknown",
    }
