"""
Security Service v2.4 — JWT, RBAC, Password, Device-bound auth, Rate limiting.
"""

from fastapi import HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import hashlib
import secrets

from src.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class JWTBearer(HTTPBearer):
    def __init__(self, auto_error: bool = True):
        super().__init__(auto_error=auto_error)

    async def __call__(self, request: Request) -> Dict[str, Any]:
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        if not credentials:
            raise HTTPException(status_code=403, detail="Invalid authorization code.")
        if credentials.scheme != "Bearer":
            raise HTTPException(status_code=403, detail="Invalid authentication scheme.")

        payload = self._decode_jwt(credentials.credentials)
        if not payload:
            raise HTTPException(status_code=403, detail="Invalid or expired token.")

        return payload

    def _decode_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def hash_token(token: str) -> str:
    """Hash a token for storage (refresh tokens)."""
    return hashlib.sha256(token.encode()).hexdigest()


class SecurityService:

    @staticmethod
    def create_access_token(user_id: int, email: str, role: str, permissions: list, device_id: Optional[str] = None) -> str:
        expires = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRATION_MINUTES)
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "permissions": permissions,
            "device_id": device_id,
            "exp": expires,
            "iat": datetime.utcnow(),
            "type": "access",
            "jti": secrets.token_urlsafe(16),  # Unique token ID
        }
        return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

    @staticmethod
    def create_refresh_token(user_id: int, device_id: Optional[str] = None) -> str:
        expires = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRATION_DAYS)
        token = secrets.token_urlsafe(32)
        payload = {
            "sub": str(user_id),
            "device_id": device_id,
            "exp": expires,
            "iat": datetime.utcnow(),
            "type": "refresh",
            "jti": secrets.token_urlsafe(16),
        }
        # Return both the raw token (for client) and the JWT
        jwt_token = jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
        return token, jwt_token, hash_token(token)

    @staticmethod
    def verify_token(token: str) -> Optional[Dict[str, Any]]:
        try:
            return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        except JWTError:
            return None

    @staticmethod
    def check_permission(user: Dict[str, Any], required_permission: str) -> bool:
        role = user.get("role", "")
        permissions = user.get("permissions", [])

        if role in ["super_admin", "admin"]:
            return True
        if "*" in permissions:
            return True

        return required_permission in permissions

    @staticmethod
    def require_role(user: Dict[str, Any], allowed_roles: list) -> bool:
        return user.get("role") in allowed_roles

    @staticmethod
    def validate_password_policy(password: str) -> tuple[bool, Optional[str]]:
        """Validate password against policy."""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not any(c.isupper() for c in password):
            return False, "Password must contain uppercase letter"
        if not any(c.islower() for c in password):
            return False, "Password must contain lowercase letter"
        if not any(c.isdigit() for c in password):
            return False, "Password must contain digit"
        return True, None

    @staticmethod
    def check_device_binding(user: Dict[str, Any], request_device_id: Optional[str]) -> bool:
        """Check if token is bound to specific device."""
        bound_device = user.get("device_id")
        if bound_device and bound_device != request_device_id:
            return False
        return True


# Rate limiting storage (simple in-memory, use Redis in production)
_login_attempts: Dict[str, list] = {}


def check_rate_limit(ip_address: str, max_attempts: int = 5, window_seconds: int = 300) -> bool:
    """Check if IP is rate limited."""
    now = datetime.utcnow()
    attempts = _login_attempts.get(ip_address, [])

    # Clean old attempts
    attempts = [a for a in attempts if (now - a).total_seconds() < window_seconds]
    _login_attempts[ip_address] = attempts

    return len(attempts) < max_attempts


def record_login_attempt(ip_address: str):
    """Record a login attempt."""
    if ip_address not in _login_attempts:
        _login_attempts[ip_address] = []
    _login_attempts[ip_address].append(datetime.utcnow())
