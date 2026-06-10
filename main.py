"""
Sport OS Core — FastAPI Backend v2.4 SYNC HARDENING
Alembic migrations + device auth + conflict engine + schema validation + CI ready.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn

from src.config import settings
from src.database import engine, Base
from src.routers import health, auth, events, sync, matches, incidents, devices


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: verify DB, run migrations if needed."""
    # Check if tables exist, if not create (dev fallback)
    from sqlalchemy import inspect
    inspector = inspect(engine)
    if not inspector.get_table_names():
        print("⚠️  No tables found — running Base.metadata.create_all (dev fallback)")
        Base.metadata.create_all(bind=engine)
    else:
        print("✅ Database tables verified")

    print("🚀 Sport OS Core v2.4 — Sync Hardening Ready")
    yield
    print("🛑 Server shutting down")


app = FastAPI(
    title="Sport OS Core API",
    version="2.4.0",
    description="API hardened: Alembic migrations, device-bound auth, conflict engine, schema validation, audit log",
    lifespan=lifespan,
)

# Strict CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Device-ID"],
)

# Routere
app.include_router(health.router, tags=["System"])
app.include_router(auth.router, prefix="/v1", tags=["Authentication"])
app.include_router(events.router, prefix="/v1", tags=["Events"])
app.include_router(sync.router, prefix="/v1", tags=["Sync"])
app.include_router(matches.router, prefix="/v1", tags=["Matches"])
app.include_router(incidents.router, prefix="/v1", tags=["Incidents"])
app.include_router(devices.router, prefix="/v1", tags=["Devices"])


@app.get("/")
async def root():
    return {
        "service": "Sport OS Core",
        "version": "2.4.0",
        "status": "operational",
        "features": [
            "alembic_migrations",
            "device_bound_auth",
            "refresh_token_rotation",
            "conflict_engine",
            "schema_validation",
            "audit_log",
            "rate_limiting",
            "password_policy",
        ],
        "docs": "/docs",
        "health": "/v1/health",
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
