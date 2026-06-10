"""
Event Log v2.4 — cu versionare, schema validation, conflict tracking.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text, BigInteger
from sqlalchemy.sql import func
from pydantic import BaseModel, validator
from typing import Dict, Any, Optional
from datetime import datetime

from src.database import Base


class EventLogDB(Base):
    __tablename__ = "event_log"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    event_id = Column(String(64), unique=True, nullable=False, index=True)
    event_type = Column(String(64), nullable=False, index=True)
    payload = Column(JSON, nullable=False)
    payload_hash = Column(String(64))
    schema_version = Column(String(16), default="1.0")
    entity_version = Column(Integer, default=1)  # For conflict detection
    base_revision = Column(String(64), nullable=True)  # Client's known server revision
    server_revision = Column(String(64), nullable=True)  # Server revision at time of processing
    conflict_type = Column(String(32), nullable=True)
    resolution_policy = Column(String(32), default="timestamp_wins")
    source_device_id = Column(String(64), index=True)
    source_service = Column(String(64))
    idempotency_key = Column(String(64), unique=True, index=True)
    event_signature = Column(String(512))
    replay_status = Column(String(16), default="original")
    replay_of = Column(String(64), nullable=True)
    event_timestamp = Column(DateTime, nullable=False, index=True)
    received_at = Column(DateTime, server_default=func.now())
    processed_at = Column(DateTime)
    partition_key = Column(String(32))
    tags = Column(JSON)


class EventLogCreate(BaseModel):
    event_id: str
    event_type: str
    payload: Dict[str, Any]
    schema_version: Optional[str] = "1.0"
    entity_version: Optional[int] = 1
    base_revision: Optional[str] = None
    source_device_id: str
    idempotency_key: str
    event_timestamp: datetime

    @validator('event_type')
    def validate_event_type(cls, v):
        allowed = ['goal_scored', 'incident_reported', 'referee_checkin', 'match_started', 
                   'match_ended', 'substitution', 'var_review', 'emergency', 'sync_request']
        if v not in allowed:
            raise ValueError(f'event_type must be one of: {allowed}')
        return v

    @validator('schema_version')
    def validate_schema_version(cls, v):
        if v not in ['1.0']:
            raise ValueError('schema_version must be 1.0')
        return v


class EventLogResponse(BaseModel):
    id: int
    event_id: str
    event_type: str
    source_device_id: str
    replay_status: str
    event_timestamp: datetime
    received_at: datetime
    entity_version: Optional[int]

    class Config:
        from_attributes = True
