import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from app.core.config import settings

def create_token(
    subject: str,
    tenant_id: str,
    role: str,
    token_type: str,
    expires_delta: timedelta | None = None
) -> str:
    """Create a generic JWT token."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        if token_type == "access":
            expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        else:
            expire = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "sub": str(subject),
        "tenant_id": str(tenant_id),
        "role": role,
        "type": token_type,
        "exp": expire,
        "iat": now,
        "jti": str(uuid.uuid4())
    }
    encoded_jwt = jwt.encode(to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return encoded_jwt

def create_access_token(
    subject: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None
) -> str:
    """Create a stateless access JWT token."""
    return create_token(subject, tenant_id, role, "access", expires_delta)

def create_refresh_token(
    subject: str,
    tenant_id: str,
    role: str,
    expires_delta: timedelta | None = None
) -> str:
    """Create a stateless refresh JWT token."""
    return create_token(subject, tenant_id, role, "refresh", expires_delta)

def decode_token(token: str) -> dict[str, Any]:
    """Decode a JWT token. Raises PyJWTError if invalid or expired."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])

def verify_token(token: str) -> dict[str, Any] | None:
    """Verify and return token claims. Returns None if invalid or expired."""
    try:
        payload = decode_token(token)
        return payload
    except jwt.PyJWTError:
        return None
