"""
Device registry — cu RBAC enforcement.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from src.database import get_db
from src.models.device import DeviceDB, DeviceCreate, DeviceResponse
from src.services.security import JWTBearer, SecurityService
from src.models.audit_log import AuditLogDB

router = APIRouter()
auth_scheme = JWTBearer()


@router.post("/devices/register")
async def register_device(
    device: DeviceCreate, 
    user: dict = Depends(auth_scheme), 
    db: Session = Depends(get_db)
):
    """Înregistrează device — necesită write:devices."""
    if not SecurityService.check_permission(user, "write:devices"):
        raise HTTPException(status_code=403, detail="Permission denied: write:devices required")

    existing = db.query(DeviceDB).filter(DeviceDB.device_id == device.device_id).first()
    if existing:
        raise HTTPException(status_code=409, detail="Device ID already exists")

    dev = DeviceDB(
        device_id=device.device_id,
        device_type=device.device_type,
        name=device.name,
        capabilities=device.capabilities,
        status="pending",
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)

    return {"device_id": dev.device_id, "status": dev.status, "registered_at": dev.created_at.isoformat() if dev.created_at else datetime.utcnow().isoformat()}


@router.get("/devices")
async def list_devices(
    device_type: Optional[str] = None,
    status: Optional[str] = None,
    user: dict = Depends(auth_scheme),
    db: Session = Depends(get_db)
):
    """Listează devices — necesită read:devices."""
    if not SecurityService.check_permission(user, "read:devices"):
        raise HTTPException(status_code=403, detail="Permission denied: read:devices required")

    query = db.query(DeviceDB)
    if device_type:
        query = query.filter(DeviceDB.device_type == device_type)
    if status:
        query = query.filter(DeviceDB.status == status)

    devices = query.all()
    return {"devices": [DeviceResponse.from_orm(d) for d in devices], "count": len(devices)}


@router.get("/devices/{device_id}")
async def get_device(device_id: str, user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """Get device — necesită read:devices."""
    if not SecurityService.check_permission(user, "read:devices"):
        raise HTTPException(status_code=403, detail="Permission denied: read:devices required")

    device = db.query(DeviceDB).filter(DeviceDB.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return DeviceResponse.from_orm(device)


@router.post("/devices/{device_id}/attest")
async def attest_device(
    device_id: str, 
    attestation: dict, 
    user: dict = Depends(auth_scheme), 
    db: Session = Depends(get_db)
):
    """Attest device — necesită write:devices."""
    if not SecurityService.check_permission(user, "write:devices"):
        raise HTTPException(status_code=403, detail="Permission denied: write:devices required")

    device = db.query(DeviceDB).filter(DeviceDB.device_id == device_id).first()
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device.trust_score = attestation.get("trust_score", 90)
    device.last_attestation = datetime.utcnow()
    device.status = "active"
    db.commit()

    return DeviceResponse.from_orm(device)
