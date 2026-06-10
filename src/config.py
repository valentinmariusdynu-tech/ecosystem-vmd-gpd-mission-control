"""
Configurare runtime Sport OS Core v2.4.
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "Sport OS Core"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "sqlite:///./sport_os.db"

    # Redis (optional, for production)
    REDIS_URL: str = "redis://localhost:6379/0"

    # Security — MUST be set in production
    JWT_SECRET: str = "dev-secret-change-me-in-production-min-32-chars-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRATION_DAYS: int = 7

    # CORS — strict in production
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:8080", "http://localhost:50000"]

    # Sync
    SYNC_BATCH_SIZE: int = 100
    SYNC_CONFLICT_RESOLUTION: str = "timestamp_wins"

    # Idempotency
    IDEMPOTENCY_KEY_TTL: int = 86400

    # Rate limiting
    RATE_LIMIT_MAX_ATTEMPTS: int = 5
    RATE_LIMIT_WINDOW_SECONDS: int = 300

    # Password policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True

    # Monitoring
    PROMETHEUS_ENABLED: bool = True
    METRICS_PORT: int = 9090

    # Gate 0
    GATE0_DEMO_MODE: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
