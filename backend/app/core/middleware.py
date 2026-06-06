import logging
import time
import uuid
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.core.config import settings
from app.core.redis import redis_cache

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    PUBLIC_PREFIXES = (
        "/",
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/v1/health",
        "/api/v1/auth/register",
        "/api/v1/auth/login",
        "/api/v1/auth/refresh",
        "/api/v1/auth/invite/accept",
        "/api/v1/tenants/resolve/",
        "/api/v1/public/",
    )

    def _requires_tenant_context(self, request: Request) -> bool:
        path = request.url.path
        if request.method == "OPTIONS":
            return False
        if path == "/":
            return False
        return not any(path.startswith(prefix) for prefix in self.PUBLIC_PREFIXES if prefix != "/")

    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            try:
                uuid.UUID(tenant_id)
                request.state.tenant_id = tenant_id
            except (ValueError, AttributeError):
                logger.warning(f"Invalid X-Tenant-ID format: {tenant_id}")
                if self._requires_tenant_context(request):
                    return JSONResponse(
                        status_code=400,
                        content={"detail": "Invalid tenant context"},
                    )
            else:
                if await redis_cache.exists(f"tenant:revoked:{tenant_id}"):
                    return JSONResponse(
                        status_code=403,
                        content={"detail": "Tenant has been offboarded or revoked"},
                    )

                window = int(time.time() // 60)
                rate_key = f"rate_limit:{tenant_id}:{window}"
                request_count = await redis_cache.incr(rate_key, expire=65)
                if (
                    request_count is not None
                    and request_count > settings.RATE_LIMIT_REQUESTS_PER_MINUTE
                ):
                    return JSONResponse(
                        status_code=429,
                        content={"detail": "Rate limit exceeded"},
                    )
        elif self._requires_tenant_context(request):
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing tenant context"},
            )
        response = await call_next(request)
        return response
