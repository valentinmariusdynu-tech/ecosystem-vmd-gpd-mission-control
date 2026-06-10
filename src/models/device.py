"""
Device Registry — model complet SQLAlchemy.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Enum, JSON, ForeignKey
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import enum

from src.database import Base


class DeviceType(str, enum.Enum):
    SMARTPHONE = "smartphone"
    TABLET = "tablet"
    EDGE_NODE = "edge_node"
    MESH_NODE = "mesh_node"
    WEARABLE = "wearable"
    SCOREBOARD = "scoreboard"
    VAR_SYSTEM = "var_system"


class DeviceStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    REVOKED = "revoked"


class DeviceDB(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, nullable=False, index=True)
    device_type = Column(String(32), nullable=False)
    status = Column(String(32), default=DeviceStatus.PENDING.value)
    name = Column(String(128))
    owner_id = Column(Integer, nullable=True)
    assigned_match_id = Column(Integer, nullable=True)
    public_key = Column(String(512))
    trust_score = Column(Integer, default=0)
    last_attestation = Column(DateTime)
    capabilities = Column(JSON)
    mesh_node_id = Column(String(64), nullable=True)
    last_seen_mesh = Column(DateTime)
    firmware_version = Column(String(32))
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


# Pydantic schemas
class DeviceCreate(BaseModel):
    device_id: str
    device_type: str
    name: str
    capabilities: Optional[Dict[str, Any]] = {}


class DeviceResponse(BaseModel):
    id: int
    device_id: str
    device_type: str
    status: str
    name: str
    trust_score: int
    capabilities: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True
