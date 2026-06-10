"""
Match management — cu RBAC enforcement.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from src.database import get_db
from src.models.match import MatchDB, MatchCreate, MatchResponse
from src.services.security import JWTBearer, SecurityService
from src.models.audit_log import AuditLogDB

router = APIRouter()
auth_scheme = JWTBearer()


def log_audit(db: Session, action: str, user_id: int, details: dict):
    db.add(AuditLogDB(action=action, user_id=user_id, details=details))
    db.commit()


@router.post("/matches")
async def create_match(
    match_data: MatchCreate, 
    user: dict = Depends(auth_scheme), 
    db: Session = Depends(get_db)
):
    """Creează meci — necesită write:matches."""
    if not SecurityService.check_permission(user, "write:matches"):
        raise HTTPException(status_code=403, detail="Permission denied: write:matches required")

    existing = db.query(MatchDB).filter(MatchDB.match_id == match_data.match_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Match ID already exists")

    match = MatchDB(
        match_id=match_data.match_id,
        home_team=match_data.home_team,
        away_team=match_data.away_team,
        scheduled_at=match_data.scheduled_at,
        venue_id=match_data.venue_id,
        competition_id=match_data.competition_id,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    log_audit(db, "match_created", int(user["sub"]), {"match_id": match.match_id})
    return MatchResponse.from_orm(match)


@router.get("/matches")
async def list_matches(
    status: Optional[str] = None,
    venue_id: Optional[int] = None,
    date_from: Optional[str] = None,
    user: dict = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    """Listează meciuri — necesită read:matches."""
    if not SecurityService.check_permission(user, "read:matches"):
        raise HTTPException(status_code=403, detail="Permission denied: read:matches required")

    query = db.query(MatchDB)
    if status:
        query = query.filter(MatchDB.status == status)
    if venue_id:
        query = query.filter(MatchDB.venue_id == venue_id)

    matches = query.order_by(MatchDB.scheduled_at).all()
    return {"matches": [MatchResponse.from_orm(m) for m in matches], "count": len(matches)}


@router.get("/matches/{match_id}")
async def get_match(match_id: str, user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """Get match — necesită read:matches."""
    if not SecurityService.check_permission(user, "read:matches"):
        raise HTTPException(status_code=403, detail="Permission denied: read:matches required")

    match = db.query(MatchDB).filter(MatchDB.match_id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")
    return MatchResponse.from_orm(match)


@router.post("/matches/{match_id}/start")
async def start_match(match_id: str, user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """Start match — necesită write:matches."""
    if not SecurityService.check_permission(user, "write:matches"):
        raise HTTPException(status_code=403, detail="Permission denied: write:matches required")

    match = db.query(MatchDB).filter(MatchDB.match_id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.status = "live"
    match.started_at = datetime.utcnow()
    db.commit()

    log_audit(db, "match_started", int(user["sub"]), {"match_id": match_id})
    return MatchResponse.from_orm(match)


@router.post("/matches/{match_id}/end")
async def end_match(match_id: str, user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """End match — necesită write:matches."""
    if not SecurityService.check_permission(user, "write:matches"):
        raise HTTPException(status_code=403, detail="Permission denied: write:matches required")

    match = db.query(MatchDB).filter(MatchDB.match_id == match_id).first()
    if not match:
        raise HTTPException(status_code=404, detail="Match not found")

    match.status = "finished"
    match.ended_at = datetime.utcnow()
    db.commit()

    log_audit(db, "match_ended", int(user["sub"]), {"match_id": match_id})
    return MatchResponse.from_orm(match)
