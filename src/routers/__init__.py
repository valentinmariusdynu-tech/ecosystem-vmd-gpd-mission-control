from .health import router as health_router
from .auth import router as auth_router
from .events import router as events_router
from .sync import router as sync_router
from .matches import router as matches_router
from .incidents import router as incidents_router
from .devices import router as devices_router

__all__ = ["health_router", "auth_router", "events_router", "sync_router", "matches_router", "incidents_router", "devices_router"]
