import json
import logging
import sys
from datetime import datetime
from fastapi import FastAPI, HTTPException, Request, status, APIRouter
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Structured JSON logging formatter
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage()
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry)

# Set up root logger with JSON stream handler
root_logger = logging.getLogger()
# Avoid duplicate logging if handlers exist
if not root_logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter())
    root_logger.addHandler(handler)
root_logger.setLevel(logging.INFO)

# Import api routers
from src.api.auth import router as auth_router
from src.api.tenants import router as tenants_router
from src.api.assistants import router as assistants_router
from src.api.knowledge import router as knowledge_router
from src.api.chat import router as chat_router
from src.api.agent_chat import router as agent_chat_router
from src.api.leads import router as leads_router
from src.api.training import router as training_router
from src.api.notifications import router as notifications_router
from src.api.exports import router as exports_router
from src.api.analytics import router as analytics_router
from src.api.webhooks import router as webhooks_router
from src.api.sockets import router as sockets_router

app = FastAPI(
    title="MoreClient AI Enterprise Platform",
    version="1.0.0"
)

# CORSMiddleware configuration (Dev setup)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logging.warning(f"HTTPException: status_code={exc.status_code} detail={exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logging.warning(f"ValidationError: errors={exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled exception: {str(exc)}", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "An internal server error occurred."}
    )

# Include all routers under /api/v1
v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(auth_router)
v1_router.include_router(tenants_router)
v1_router.include_router(assistants_router)
v1_router.include_router(knowledge_router)
v1_router.include_router(chat_router)
v1_router.include_router(agent_chat_router)
v1_router.include_router(leads_router)
v1_router.include_router(training_router)
v1_router.include_router(notifications_router)
v1_router.include_router(exports_router)
v1_router.include_router(analytics_router)
v1_router.include_router(webhooks_router)
v1_router.include_router(sockets_router)

app.include_router(v1_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}
