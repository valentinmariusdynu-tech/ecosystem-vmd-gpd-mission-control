"""
Incident reporting — cu RBAC enforcement.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from src.database import get_db
from src.models.incident import IncidentDB, IncidentCreate, IncidentResponse
from src.services.security import JWTBearer, SecurityService
from src.models.audit_log import AuditLogDB

router = APIRouter()
auth_scheme = JWTBearer()


@router.post("/incidents")
async def report_incident(
    incident: IncidentCreate, 
    user: dict = Depends(auth_scheme), 
    db: Session = Depends(get_db)
):
    """Raportează incident — necesită write:incidents."""
    if not SecurityService.check_permission(user, "write:incidents"):
        raise HTTPException(status_code=403, detail="Permission denied: write:incidents required")

    existing = db.query(IncidentDB).filter(IncidentDB.idempotency_key == incident.idempotency_key).first()
    if existing:
        return {"status": "duplicate", "incident_id": existing.incident_id}

    inc = IncidentDB(
        incident_id=incident.incident_id,
        match_id=incident.match_id,
        incident_type=incident.incident_type,
        minute=incident.minute,
        description=incident.description,
        severity=incident.severity,
        idempotency_key=incident.idempotency_key,
        local_timestamp=incident.local_timestamp,
        reported_by_device_id=user.get("sub"),
    )
    db.add(inc)
    db.commit()
    db.refresh(inc)

    db.add(AuditLogDB(action="incident_reported", user_id=int(user["sub"]), details={"incident_id": inc.incident_id}))
    db.commit()

    return IncidentResponse.from_orm(inc)


@router.get("/incidents")
async def list_incidents(
    match_id: Optional[int] = None,
    incident_type: Optional[str] = None,
    user: dict = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    """Listează incidente — necesită read:incidents."""
    if not SecurityService.check_permission(user, "read:incidents"):
        raise HTTPException(status_code=403, detail="Permission denied: read:incidents required")

    query = db.query(IncidentDB)
    if match_id:
        query = query.filter(IncidentDB.match_id == match_id)
    if incident_type:
        query = query.filter(IncidentDB.incident_type == incident_type)

    incidents = query.order_by(IncidentDB.created_at.desc()).all()
    return {"incidents": [IncidentResponse.from_orm(i) for i in incidents], "count": len(incidents)}


@router.post("/incidents/{incident_id}/validate")
async def validate_incident(
    incident_id: str, 
    validation: dict, 
    user: dict = Depends(auth_scheme), 
    db: Session = Depends(get_db)
):
    """Validare incident — necesită validate:incidents (VAR/Admin)."""
    if not SecurityService.check_permission(user, "validate:incidents"):
        raise HTTPException(status_code=403, detail="Permission denied: validate:incidents required")

    incident = db.query(IncidentDB).filter(IncidentDB.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")

    incident.validation_status = validation.get("status", "approved")
    incident.validated_by = int(user["sub"])
    incident.validated_at = datetime.utcnow()
    db.commit()

    return IncidentResponse.from_orm(incident)
