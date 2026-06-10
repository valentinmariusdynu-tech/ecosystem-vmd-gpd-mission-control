"""
Refresh Token — server-side storage cu rotation și revocation.
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from src.database import Base


class RefreshTokenDB(Base):
    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token_hash = Column(String(128), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    device_id = Column(String(64), nullable=True, index=True)
    rotation_id = Column(String(64), nullable=True)  # For token rotation
    issued_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_reason = Column(String(128), nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(256), nullable=True)

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None or datetime.utcnow() > self.expires_at


class RefreshTokenCreate(BaseModel):
    token_hash: str
    user_id: int
    device_id: Optional[str] = None
    rotation_id: Optional[str] = None
    expires_at: datetime
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


class RefreshTokenResponse(BaseModel):
    id: int
    user_id: int
    device_id: Optional[str]
    issued_at: datetime
    expires_at: datetime
    is_revoked: bool

    class Config:
        from_attributes = True
