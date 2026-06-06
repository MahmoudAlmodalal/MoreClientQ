import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.db.session import get_db
from app.core.security import require_roles
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import chat_service, handoff_service
from app.services.chat_service import (
    QuotaExceededError,
    AssistantNotFoundError,
    ConversationInHandoffError,
    ConversationNotFoundError
)
from app.services.llm_service import LLMUnavailableError

router = APIRouter()

def _get_tenant_id_from_user(current_user: dict) -> uuid.UUID:
    tenant_id_str = current_user.get("tenant_id", "")
    if not tenant_id_str:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tenant ID not found in credentials"
        )
    return uuid.UUID(tenant_id_str)

@router.post("", response_model=ChatResponse)
async def chat_endpoint(
    payload: ChatRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner", "admin", "member", "viewer")),
):
    tenant_id = _get_tenant_id_from_user(current_user)
    
    # 1. Check for handoff keywords before calling chat_service
    if handoff_service.is_handoff_trigger(payload.message):
        conv_id = payload.conversation_id
        if not conv_id:
            # Validate assistant belongs to tenant first to throw 404 if invalid assistant_id
            from app.models.assistant import Assistant
            from sqlalchemy.future import select
            assistant_res = await db.execute(
                select(Assistant).where(
                    Assistant.id == payload.assistant_id,
                    Assistant.tenant_id == tenant_id
                )
            )
            assistant = assistant_res.scalar_one_or_none()
            if not assistant:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Assistant not found"
                )
                
            # Create the conversation so we can set its status to handoff
            from app.models.conversation import Conversation
            from uuid import uuid4
            conv = Conversation(
                tenant_id=tenant_id,
                assistant_id=payload.assistant_id,
                session_token=uuid4().hex,
                status="bot",
                channel="web",
                title=payload.message[:100]
            )
            db.add(conv)
            await db.commit()
            conv_id = conv.id
            
        await handoff_service.trigger_handoff(tenant_id, conv_id, payload.assistant_id)
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Conversation is in handoff mode; AI responses are suspended"
            }
        )

    try:
        chat_resp = await chat_service.chat(
            db=db,
            tenant_id=tenant_id,
            assistant_id=payload.assistant_id,
            conversation_id=payload.conversation_id,
            user_content=payload.message
        )
        
        # Add Cache-Control: no-store header to prevent upstream caching of sensitive conversation data
        response.headers["Cache-Control"] = "no-store"
        return chat_resp

    except AssistantNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ConversationNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except QuotaExceededError as e:
        from datetime import datetime, timedelta
        next_hour = (datetime.utcnow() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "detail": "Token quota exceeded for this billing period",
                "retry_after": next_hour.isoformat() + "Z"
            }
        )
    except ConversationInHandoffError as e:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": "Conversation is in handoff mode; AI responses are suspended"
            }
        )
    except LLMUnavailableError as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "detail": "AI service temporarily unavailable. Please try again shortly."
            }
        )
