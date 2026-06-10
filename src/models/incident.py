"""
Incident model — complet SQLAlchemy.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from src.database import Base


class IncidentDB(Base):
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    incident_id = Column(String(32), unique=True, nullable=False, index=True)
    match_id = Column(Integer, nullable=False)
    reported_by_device_id = Column(String(64), nullable=True)
    incident_type = Column(String(32), nullable=False)
    severity = Column(String(32), default="low")
    minute = Column(Integer)
    description = Column(Text)
    media_urls = Column(JSON)
    validated_by = Column(Integer, nullable=True)
    validated_at = Column(DateTime)
    validation_status = Column(String(16), default="pending")
    local_timestamp = Column(DateTime)
    synced_at = Column(DateTime)
    sync_batch_id = Column(String(32))
    idempotency_key = Column(String(64), unique=True, index=True)
    created_at = Column(DateTime, server_default=func.now())


class IncidentCreate(BaseModel):
    incident_id: str
    match_id: int
    incident_type: str
    minute: int
    description: str
    severity: Optional[str] = "low"
    idempotency_key: str
    local_timestamp: datetime


class IncidentResponse(BaseModel):
    id: int
    incident_id: str
    match_id: int
    incident_type: str
    minute: int
    description: str
    validation_status: str
    created_at: datetime

    class Config:
        from_attributes = True
