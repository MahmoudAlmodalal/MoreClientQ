import logging
import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

logger = logging.getLogger(__name__)

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        tenant_id = request.headers.get("X-Tenant-ID")
        if tenant_id:
            try:
                uuid.UUID(hex=tenant_id)
                request.state.tenant_id = tenant_id
            except (ValueError, AttributeError):
                logger.warning(f"Invalid X-Tenant-ID format: {tenant_id}")
        response = await call_next(request)
        return response
