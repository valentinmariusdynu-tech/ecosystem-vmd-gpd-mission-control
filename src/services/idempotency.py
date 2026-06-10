"""
Idempotency Service — SQLite-based pentru development.
"""

from sqlalchemy.orm import Session
from src.models.event_log import EventLogDB


class IdempotencyService:
    @classmethod
    def is_duplicate(cls, db: Session, key: str) -> bool:
        if not key:
            return False
        existing = db.query(EventLogDB).filter(EventLogDB.idempotency_key == key).first()
        return existing is not None
