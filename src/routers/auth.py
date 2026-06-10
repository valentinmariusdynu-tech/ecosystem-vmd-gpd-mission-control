"""
Auth Router — Login, Register, Refresh Token, Profile.
"""

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

from src.database import get_db
from src.models.user import UserDB, UserResponse
from src.services.security import (
    SecurityService, verify_password, get_password_hash, 
    JWTBearer, check_permission
)
from src.models.audit_log import AuditLogDB

router = APIRouter(prefix="/auth", tags=["Authentication"])
auth_scheme = JWTBearer()


# Schemas
class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = "spectator"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


# Helper: log audit
def log_audit(db: Session, action: str, user_id: int, details: dict):
    log = AuditLogDB(
        action=action,
        user_id=user_id,
        details=details,
        ip_address="0.0.0.0",  # TODO: extract from request
    )
    db.add(log)
    db.commit()


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Înregistrare utilizator nou."""
    # Verifică email unic
    existing = db.query(UserDB).filter(UserDB.email == request.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Creează user
    user = UserDB(
        email=request.email,
        hashed_password=get_password_hash(request.password),
        first_name=request.first_name,
        last_name=request.last_name,
        role=request.role,
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Generează tokens
    permissions = get_role_permissions(request.role)
    access_token = SecurityService.create_access_token(
        user.id, user.email, user.role, permissions
    )
    refresh_token = SecurityService.create_refresh_token(user.id)

    # Audit log
    log_audit(db, "user_registered", user.id, {"email": user.email, "role": user.role})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60,  # 1 hour
        user=UserResponse.from_orm(user),
    )


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Autentificare utilizator."""
    user = db.query(UserDB).filter(UserDB.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account disabled")

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Generează tokens
    permissions = get_role_permissions(user.role)
    access_token = SecurityService.create_access_token(
        user.id, user.email, user.role, permissions
    )
    refresh_token = SecurityService.create_refresh_token(user.id)

    # Audit log
    log_audit(db, "user_login", user.id, {"email": user.email})

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60,
        user=UserResponse.from_orm(user),
    )


@router.post("/refresh")
async def refresh(request: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token."""
    payload = SecurityService.verify_token(request.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id = int(payload["sub"])
    user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    permissions = get_role_permissions(user.role)
    access_token = SecurityService.create_access_token(
        user.id, user.email, user.role, permissions
    )

    log_audit(db, "token_refreshed", user.id, {})

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": 60 * 60,
    }


@router.get("/me", response_model=UserResponse)
async def get_me(user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """Profil utilizator curent."""
    user_id = int(user["sub"])
    db_user = db.query(UserDB).filter(UserDB.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserResponse.from_orm(db_user)


@router.post("/logout")
async def logout(user: dict = Depends(auth_scheme), db: Session = Depends(get_db)):
    """Logout — invalidează token (client-side)."""
    user_id = int(user["sub"])
    log_audit(db, "user_logout", user_id, {})
    return {"status": "logged_out"}


# Helper: role permissions mapping
ROLE_PERMISSIONS = {
    "super_admin": ["*"],  # All permissions
    "admin": [
        "read:matches", "write:matches", "delete:matches",
        "read:incidents", "write:incidents", "validate:incidents",
        "read:devices", "write:devices", "delete:devices",
        "read:users", "write:users",
        "read:events", "write:events",
        "read:sync", "write:sync",
    ],
    "organizer": [
        "read:matches", "write:matches",
        "read:incidents",
        "read:devices",
        "read:events",
    ],
    "referee": [
        "read:matches", "write:matches",
        "read:incidents", "write:incidents",
        "read:devices",
        "read:events", "write:events",
        "read:sync", "write:sync",
    ],
    "assistant": [
        "read:matches",
        "read:incidents", "write:incidents",
        "read:events", "write:events",
    ],
    "var": [
        "read:matches",
        "read:incidents", "validate:incidents",
        "read:events",
    ],
    "observer": [
        "read:matches",
        "read:incidents",
        "read:events",
    ],
    "player": [
        "read:matches",
        "read:incidents",
    ],
    "spectator": [
        "read:matches",
    ],
}


def get_role_permissions(role: str) -> List[str]:
    return ROLE_PERMISSIONS.get(role, [])
