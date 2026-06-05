from typing import List, Callable
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from src.config import settings
from src.database import tenant_context

security = HTTPBearer()

ROLE_HIERARCHY = {
    "super_admin": 4,
    "tenant_admin": 3,
    "agent": 2,
    "viewer": 1
}

def require_role(*allowed_roles: str) -> Callable:
    """FastAPI dependency factory to enforce RBAC and set the tenant context.
    Ensures the user has one of the allowed roles or a higher role in the hierarchy.
    """
    def dependency(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
        token = credentials.credentials
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
        except jwt.PyJWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )

        user_role = payload.get("role")
        user_id = payload.get("user_id")
        tenant_id = payload.get("tenant_id")

        if not user_role or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token payload is missing user ID or role"
            )

        # Enforce role hierarchy: user's role weight must be >= the minimum allowed role weight
        user_weight = ROLE_HIERARCHY.get(user_role, 0)
        
        authorized = False
        for allowed in allowed_roles:
            allowed_weight = ROLE_HIERARCHY.get(allowed, 0)
            if user_weight >= allowed_weight:
                authorized = True
                break

        if not authorized:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Operation not permitted for this role"
            )

        # Proactively set the tenant context variable for this request execution path
        if tenant_id:
            tenant_context.set(str(tenant_id))

        return payload

    return dependency
