"""
Match model — complet SQLAlchemy.
"""

from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

from src.database import Base


class MatchDB(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(String(32), unique=True, nullable=False, index=True)
    home_team = Column(String(128), nullable=False)
    away_team = Column(String(128), nullable=False)
    home_score = Column(Integer, default=0)
    away_score = Column(Integer, default=0)
    status = Column(String(32), default="scheduled")
    phase = Column(String(32), default="regular")
    scheduled_at = Column(DateTime, nullable=False)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    venue_id = Column(Integer, nullable=True)
    field_number = Column(Integer)
    referee_id = Column(Integer, nullable=True)
    assistant_1_id = Column(Integer, nullable=True)
    assistant_2_id = Column(Integer, nullable=True)
    var_id = Column(Integer, nullable=True)
    config = Column(JSON)
    competition_id = Column(Integer, nullable=True)
    season = Column(String(16))
    created_at = Column(DateTime, server_default=func.now())


class MatchCreate(BaseModel):
    match_id: str
    home_team: str
    away_team: str
    scheduled_at: datetime
    venue_id: Optional[int] = None
    competition_id: Optional[int] = None


class MatchResponse(BaseModel):
    id: int
    match_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    status: str
    scheduled_at: datetime
    started_at: Optional[datetime] = None
    ended_at: Optional[datetime] = None

    class Config:
        from_attributes = True
