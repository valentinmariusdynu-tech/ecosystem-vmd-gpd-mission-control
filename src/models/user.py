"""
User model v2.4 — cu device-bound auth și offline auth window.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime

from src.database import Base


class UserDB(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(128), unique=True, nullable=False)
    hashed_password = Column(String(256))
    first_name = Column(String(64))
    last_name = Column(String(64))
    phone = Column(String(32))
    role = Column(String(32), default="spectator")
    permissions = Column(JSON)
    bound_device_id = Column(String(64), nullable=True)  # Device-bound auth
    offline_auth_window = Column(Integer, default=3600)  # Seconds (1 hour)
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    last_login = Column(DateTime)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = DateTime  # Will be set by onupdate
    created_by = Column(Integer, nullable=True)


class UserCreate(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    role: str
    password: str
    bound_device_id: Optional[str] = None
    offline_auth_window: Optional[int] = 3600


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    role: str
    bound_device_id: Optional[str]
    offline_auth_window: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
