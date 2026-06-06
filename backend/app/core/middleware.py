import logging
import uuid
from starlette.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

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
        "/api/v1/tenants/resolve/",
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
        elif self._requires_tenant_context(request):
            return JSONResponse(
                status_code=400,
                content={"detail": "Missing tenant context"},
            )
        response = await call_next(request)
        return response
