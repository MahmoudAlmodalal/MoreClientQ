import bcrypt
import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any
import jwt
from app.core.config import settings
from app.core.redis import redis_cache

from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

security_scheme = HTTPBearer(auto_error=False)

def create_token(
    subject: str,
    tenant_id: str,
    tenant_slug: str,
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
        "tenant_slug": tenant_slug,
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
    tenant_slug: str,
    role: str,
    expires_delta: timedelta | None = None
) -> str:
    """Create a stateless access JWT token."""
    return create_token(subject, tenant_id, tenant_slug, role, "access", expires_delta)

def create_refresh_token(
    subject: str,
    tenant_id: str,
    tenant_slug: str,
    role: str,
    expires_delta: timedelta | None = None
) -> str:
    """Create a stateless refresh JWT token."""
    return create_token(subject, tenant_id, tenant_slug, role, "refresh", expires_delta)

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

async def is_token_revoked(payload: dict[str, Any]) -> bool:
    """Check whether a JWT identifier has been blocklisted in Redis."""
    jti = payload.get("jti")
    if not jti:
        return True
    try:
        return await asyncio.wait_for(
            redis_cache.exists(f"jwt:blocklist:{jti}"),
            timeout=0.25,
        )
    except asyncio.TimeoutError:
        return False

async def is_tenant_revoked(payload: dict[str, Any]) -> bool:
    """Check whether every token for a tenant has been revoked."""
    tenant_id = payload.get("tenant_id")
    if not tenant_id:
        return True
    try:
        return await asyncio.wait_for(
            redis_cache.exists(f"tenant:revoked:{tenant_id}"),
            timeout=0.25,
        )
    except asyncio.TimeoutError:
        return False

async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(security_scheme)
) -> dict[str, Any]:
    """FastAPI dependency to extract and verify the access token from Authorization header."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = credentials.credentials
    payload = verify_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if await is_token_revoked(payload):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if await is_tenant_revoked(payload):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant has been revoked",
        )

    # Cross-validate X-Tenant-ID header if present in request (or request.state.tenant_id if set by middleware)
    tenant_id_header = request.headers.get("X-Tenant-ID")
    if tenant_id_header and payload.get("tenant_id") != tenant_id_header:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch",
        )

    # Also check if request.state.tenant_id is already set (by middleware in future phases)
    tenant_id_state = getattr(request.state, "tenant_id", None)
    if tenant_id_state and payload.get("tenant_id") != str(tenant_id_state):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant mismatch",
        )

    return payload


def require_roles(*allowed_roles: str):
    """FastAPI dependency factory: returns a dependency that checks the current user's role.

    Usage:
        @router.get("/admin-only")
        async def admin_endpoint(current_user: dict = Depends(require_roles("admin", "owner"))):
            ...
    """
    if not allowed_roles:
        async def _deny_all(current_user: dict = Depends(get_current_user)) -> dict:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: no roles granted access"
            )
        return _deny_all

    async def _role_checker(current_user: dict = Depends(get_current_user)) -> dict:
        user_role = current_user.get("role", "")
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Forbidden: insufficient permissions"
            )
        return current_user

    return _role_checker


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against its hash."""
    try:
        return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    """Generate bcrypt hash of password."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
