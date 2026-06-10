"""
Audit Log — tracking toate acțiunile critice.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from src.database import Base


class AuditLogDB(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    action = Column(String(64), nullable=False, index=True)
    user_id = Column(Integer, nullable=True, index=True)
    details = Column(JSON)
    ip_address = Column(String(45))  # IPv6 compatible
    user_agent = Column(String(256))
    resource_type = Column(String(64))
    resource_id = Column(String(64))
    success = Column(String(16), default="success")  # success, failure, denied
    created_at = Column(DateTime, server_default=func.now())


class AuditLogCreate(BaseModel):
    action: str
    user_id: Optional[int] = None
    details: Optional[Dict[str, Any]] = {}
    ip_address: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    success: Optional[str] = "success"
