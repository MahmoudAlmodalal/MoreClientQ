import uuid
import json
import logging
import asyncio
from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse, StreamingResponse
from openai import APIStatusError

from app.core.config import settings
from app.core.rate_limit import check_and_increment_demo_limits
from app.services.llm_service import client, LLMUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter()

SYSTEM_PROMPT = (
    "You are the demo assistant for our Multi-Tenant AI Assistant Platform. "
    "Your goal is to showcase the platform's capabilities to prospective customers (SMB owners and startup founders). "
    "Answer their questions concisely, professionally, and enthusiastically.\n\n"
    "Key platform features to highlight if asked:\n"
    "1. Custom Knowledge Bases (RAG): Customers can upload PDF, DOCX, or TXT documents to train their assistants in seconds.\n"
    "2. Multi-Tenant Security: Built with row-level security (RLS) and isolated data stores ensuring absolute tenant separation and privacy.\n"
    "3. Real-Time Streaming: Blazing fast responses using Server-Sent Events (SSE).\n"
    "4. Human Handoff: Seamless transition from AI to human agents when requested.\n"
    "5. Simple Integration: Easily embed widgets on any website with a single line of code.\n"
    "6. Robust Analytics: Monitor assistant performance and token usage in real time.\n\n"
    "Pricing plans:\n"
    "- Starter: Free, 1 assistant, 5 documents, 50MB storage.\n"
    "- Pro: $49/mo, 5 assistants, 100 documents, 1GB storage.\n"
    "- Business: $199/mo, unlimited assistants, unlimited documents.\n"
    "- Enterprise: Custom pricing, dedicated setup, SLA, contact sales.\n\n"
    "Keep your answers short and focused. Maximum response length is 256 tokens."
)

async def complete_demo_stream(messages: list, model: str):
    try:
        return await client.chat.completions.create(
            messages=messages,
            model=model,
            stream=True,
            max_tokens=256
        )
    except APIStatusError as e:
        logger.warning(f"Demo LLM error {e.status_code} for model {model}: {e}")
        raise LLMUnavailableError(f"LLM service error (HTTP {e.status_code}): {e}")
    except asyncio.TimeoutError as e:
        logger.warning(f"Demo LLM timeout for model {model}: {e}")
        raise LLMUnavailableError("LLM request timed out")
    except Exception as e:
        logger.error(f"Unexpected demo LLM error for model {model}: {e}")
        raise e

async def get_demo_llm_stream(messages: list):
    try:
        return await complete_demo_stream(messages, settings.LLM_PRIMARY_MODEL)
    except LLMUnavailableError as e:
        logger.warning(f"Primary model {settings.LLM_PRIMARY_MODEL} unavailable for demo. Retrying with fallback: {e}")
        try:
            return await complete_demo_stream(messages, settings.LLM_FALLBACK_MODEL)
        except LLMUnavailableError as fallback_err:
            logger.error(f"Fallback model {settings.LLM_FALLBACK_MODEL} also failed for demo: {fallback_err}")
            raise LLMUnavailableError("Both primary and fallback LLM models are unavailable.")

async def sse_stream_generator(stream, current_count: int):
    try:
        async for chunk in stream:
            if not chunk.choices:
                continue
            content = chunk.choices[0].delta.content
            if content:
                yield f"data: {json.dumps({'type': 'token', 'content': content})}\n\n"
        
        yield f"data: {json.dumps({'type': 'done', 'message_count': current_count})}\n\n"
    except Exception as e:
        logger.error(f"Error during demo chat stream: {e}")

@router.post("/chat")
async def public_chat_endpoint(request: Request):
    # 1. Parse request body
    try:
        data = await request.json()
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Invalid JSON body"
                }
            }
        )

    message = data.get("message")
    session_id = data.get("session_id")

    # 2. Validate inputs
    if not isinstance(message, str) or not isinstance(session_id, str):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Message is missing, too long, or session_id is malformed"
                }
            }
        )

    message = message.strip()
    if not message or len(message) > 500:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Message is missing, too long, or session_id is malformed"
                }
            }
        )

    try:
        uuid_obj = uuid.UUID(session_id)
        if uuid_obj.version != 4:
            raise ValueError()
    except ValueError:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": {
                    "code": "INVALID_REQUEST",
                    "message": "Message is missing, too long, or session_id is malformed"
                }
            }
        )

    # 3. Check rate limits
    ip = request.client.host if request.client else "127.0.0.1"
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        ip = forwarded_for.split(",")[0].strip()

    allowed, current_count = await check_and_increment_demo_limits(ip, session_id)
    if not allowed:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": {
                    "code": "DEMO_QUOTA_EXCEEDED",
                    "message": "You have reached the demo limit. Start your free trial to continue.",
                    "message_count": current_count
                }
            }
        )

    # 4. Get LLM stream (handling failure before streaming starts)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": message}
    ]

    try:
        stream = await get_demo_llm_stream(messages)
    except LLMUnavailableError:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "error": {
                    "code": "SERVICE_UNAVAILABLE",
                    "message": "AI service temporarily unavailable. Please try again shortly."
                }
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error when creating completion stream: {e}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": "An internal server error occurred."
                }
            }
        )

    # 5. Return Server-Sent Events stream
    return StreamingResponse(
        sse_stream_generator(stream, current_count),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
