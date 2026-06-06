import logging
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_router
from app.api.v1.health import health_check
from app.core.config import settings
from app.core.middleware import TenantMiddleware

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Tenant AI Assistant Platform",
    description="Foundational Auth & Tenancy system"
)

# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_origin_regex=settings.ALLOWED_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Tenant Middleware - extracts X-Tenant-ID and sets request.state.tenant_id
app.add_middleware(TenantMiddleware)

# Global Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.error(f"HTTP error occurred: {exc.detail} (status code: {exc.status_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

from fastapi.encoders import jsonable_encoder

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.error(f"Validation error occurred: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": jsonable_encoder(exc.errors())},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("An unhandled exception occurred.")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error occurred."},
    )

# Register versioned API endpoints under /api/v1 prefix
app.include_router(api_router, prefix="/api/v1")

# Also map the health check endpoint directly to root /health for docker/k8s probes
app.add_api_route("/health", health_check, methods=["GET"], tags=["health"])

@app.get("/")
def read_root():
    return {"message": "FastAPI backend is operational"}
