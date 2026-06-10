"""
Conflict Resolution — tracking și rezolvare conflicte sync.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from src.database import Base


class ConflictDB(Base):
    __tablename__ = "conflicts"

    id = Column(Integer, primary_key=True, index=True)
    conflict_id = Column(String(64), unique=True, nullable=False, index=True)
    entity_type = Column(String(32), nullable=False)  # match, incident, event
    entity_id = Column(String(64), nullable=False, index=True)
    local_version = Column(JSON, nullable=False)
    server_version = Column(JSON, nullable=False)
    local_timestamp = Column(DateTime, nullable=False)
    server_timestamp = Column(DateTime, nullable=False)
    conflict_type = Column(String(32), nullable=False)  # concurrent_edit, stale_data, version_mismatch
    resolution = Column(String(32), nullable=True)  # timestamp_wins, server_wins, manual, merged
    resolved_by = Column(Integer, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    resolution_policy = Column(String(32), default="timestamp_wins")
    manual_override = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())


class ConflictCreate(BaseModel):
    conflict_id: str
    entity_type: str
    entity_id: str
    local_version: Dict[str, Any]
    server_version: Dict[str, Any]
    local_timestamp: datetime
    server_timestamp: datetime
    conflict_type: str
    resolution_policy: Optional[str] = "timestamp_wins"


class ConflictResponse(BaseModel):
    id: int
    conflict_id: str
    entity_type: str
    entity_id: str
    conflict_type: str
    resolution: Optional[str]
    resolution_policy: str
    manual_override: bool
    created_at: datetime

    class Config:
        from_attributes = True
