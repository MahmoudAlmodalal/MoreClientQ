from fastapi import APIRouter
from app.api.v1 import health
from app.api.v1.endpoints import auth
from app.api.v1.endpoints import tenants
from app.api.v1.endpoints import users
from app.api.v1.endpoints import assistants
from app.api.v1.endpoints import documents
from app.api.v1.endpoints import chat
from app.api.v1.endpoints import ws_chat

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tenants.router, prefix="/tenants", tags=["tenants"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(assistants.router, prefix="/assistants", tags=["assistants"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(ws_chat.router, prefix="/ws", tags=["chat-ws"])


