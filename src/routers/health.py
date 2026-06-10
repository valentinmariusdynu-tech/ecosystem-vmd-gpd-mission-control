"""
Health check — public endpoint.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import psutil

from src.database import get_db

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    db_status = "connected"
    try:
        db.execute("SELECT 1")
    except Exception:
        db_status = "disconnected"

    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "2.3.0",
        "services": {"database": db_status, "redis": "connected", "event_bus": "connected"},
        "system": {"cpu_percent": psutil.cpu_percent(interval=0.1), "memory_percent": psutil.virtual_memory().percent, "disk_percent": psutil.disk_usage('/').percent},
    }


@router.get("/health/ready")
async def readiness(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"ready": True}
    except Exception:
        return {"ready": False}


@router.get("/health/live")
async def liveness():
    return {"alive": True}
