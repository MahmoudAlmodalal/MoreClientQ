import json
import logging
import uuid as uuid_module

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.core.security import decode_token
from app.db.session import SessionLocal, set_tenant_context
from app.schemas.chat import (
    WSIncomingMessage,
    WSTokenEvent,
    WSDoneEvent,
    WSErrorEvent,
    WSHandoffEvent,
)
from app.services import chat_service, handoff_service
from app.services.chat_service import (
    AssistantNotFoundError,
    ConversationInHandoffError,
    ConversationNotFoundError,
    QuotaExceededError,
)
from app.services.llm_service import LLMUnavailableError

logger = logging.getLogger(__name__)

router = APIRouter()


@router.websocket("/chat")
async def ws_chat_endpoint(
    websocket: WebSocket,
    token: str | None = None,
    tenant_id: str | None = None,
    assistant_id: str | None = None,
):
    """
    WebSocket endpoint at GET /api/v1/ws/chat

    Query params:
        token       — JWT access token
        tenant_id   — UUID of the tenant (must match JWT claim)
        assistant_id — UUID of the assistant to chat with

    Close codes:
        4001 — authentication failed (invalid/missing JWT)
        4003 — forbidden (tenant_id mismatch or missing)
    """
    # ── Authentication ──────────────────────────────────────────────────────
    if not token:
        await websocket.close(code=4001, reason="Missing authentication token")
        return

    try:
        payload = decode_token(token)
    except Exception as exc:
        logger.warning("WS auth failure — invalid token: %s", exc)
        await websocket.close(code=4001, reason="Invalid or expired token")
        return

    jwt_tenant_id: str = payload.get("tenant_id", "")
    if not jwt_tenant_id:
        await websocket.close(code=4003, reason="Token does not contain tenant_id")
        return

    if not tenant_id or tenant_id != jwt_tenant_id:
        await websocket.close(code=4003, reason="tenant_id mismatch")
        return

    if not assistant_id:
        await websocket.close(code=4003, reason="Missing assistant_id")
        return

    try:
        tenant_uuid = uuid_module.UUID(tenant_id)
        assistant_uuid = uuid_module.UUID(assistant_id)
    except ValueError:
        await websocket.close(code=4003, reason="Invalid UUID format")
        return

    await websocket.accept()
    logger.info(
        "WS connection accepted — tenant=%s assistant=%s",
        tenant_id,
        assistant_id,
    )

    # ── Message loop ────────────────────────────────────────────────────────
    try:
        while True:
            raw = await websocket.receive_text()

            try:
                data = json.loads(raw)
                incoming = WSIncomingMessage(**data)
            except Exception as parse_err:
                await websocket.send_text(
                    WSErrorEvent(
                        code="invalid_message",
                        detail=f"Failed to parse message: {parse_err}",
                    ).model_dump_json()
                )
                continue

            # ── ping ──
            if incoming.type == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
                continue

            # ── message ──
            content = incoming.content or ""
            conversation_id = incoming.conversation_id

            async with SessionLocal() as db:
                await set_tenant_context(db, str(tenant_uuid))

                # Check if conversation is already in handoff
                if conversation_id:
                    from sqlalchemy.future import select
                    from app.models.conversation import Conversation
                    conv_res = await db.execute(
                        select(Conversation).where(
                            Conversation.id == conversation_id,
                            Conversation.tenant_id == tenant_uuid
                        )
                    )
                    conv = conv_res.scalar_one_or_none()
                    if conv and conv.status == "handoff":
                        await websocket.send_text(
                            WSHandoffEvent(
                                conversation_id=conversation_id,
                                detail="This conversation has been transferred to a human agent.",
                            ).model_dump_json()
                        )
                        continue

                # Check handoff trigger before streaming
                if handoff_service.is_handoff_trigger(content):
                    try:
                        conv_id = conversation_id
                        if not conv_id:
                            # Create a minimal conversation to record the handoff
                            from uuid import uuid4
                            from app.models.conversation import Conversation
                            conv = Conversation(
                                tenant_id=tenant_uuid,
                                assistant_id=assistant_uuid,
                                session_token=uuid4().hex,
                                status="bot",
                                channel="web",
                                title=content[:100],
                            )
                            db.add(conv)
                            await db.flush()
                            await db.commit()
                            conv_id = conv.id

                        await handoff_service.trigger_handoff(
                            tenant_uuid, conv_id, assistant_uuid
                        )
                        await websocket.send_text(
                            WSHandoffEvent(
                                conversation_id=conv_id,
                                detail="This conversation has been transferred to a human agent.",
                            ).model_dump_json()
                        )
                    except Exception as ho_err:
                        logger.error("Handoff trigger error: %s", ho_err)
                        await websocket.send_text(
                            WSErrorEvent(
                                code="handoff_active",
                                detail="Failed to initiate handoff",
                            ).model_dump_json()
                        )
                    continue

                # Stream tokens via chat_service.stream_chat
                try:
                    gen = chat_service.stream_chat(
                        db=db,
                        tenant_id=tenant_uuid,
                        assistant_id=assistant_uuid,
                        conversation_id=conversation_id,
                        user_content=content,
                    )

                    async for item in gen:
                        if item == "quota_exceeded":
                            await websocket.send_text(
                                WSErrorEvent(
                                    code="quota_exceeded",
                                    detail="Token quota exhausted; response has been truncated.",
                                ).model_dump_json()
                            )
                            break

                        if isinstance(item, dict) and item.get("type") == "done":
                            done_event = WSDoneEvent(
                                conversation_id=item["conversation_id"],
                                message_id=item["message_id"],
                                tokens_used=item["tokens_used"],
                                model_used=item.get("model_used"),
                                sources=item.get("sources", []),
                            )
                            await websocket.send_text(done_event.model_dump_json())
                        else:
                            # Plain string token delta
                            await websocket.send_text(
                                WSTokenEvent(delta=str(item)).model_dump_json()
                            )

                except AssistantNotFoundError:
                    await websocket.send_text(
                        WSErrorEvent(
                            code="assistant_not_found",
                            detail="Assistant not found for this tenant.",
                        ).model_dump_json()
                    )
                except ConversationNotFoundError:
                    await websocket.send_text(
                        WSErrorEvent(
                            code="invalid_message",
                            detail="Conversation not found.",
                        ).model_dump_json()
                    )
                except ConversationInHandoffError:
                    await websocket.send_text(
                        WSErrorEvent(
                            code="handoff_active",
                            detail="Conversation is in handoff mode; AI responses are suspended.",
                        ).model_dump_json()
                    )
                except QuotaExceededError:
                    await websocket.send_text(
                        WSErrorEvent(
                            code="quota_exceeded",
                            detail="Token quota exceeded. Please try again later.",
                        ).model_dump_json()
                    )
                except LLMUnavailableError:
                    await websocket.send_text(
                        WSErrorEvent(
                            code="llm_unavailable",
                            detail="AI service temporarily unavailable. Please try again shortly.",
                        ).model_dump_json()
                    )
                except Exception as exc:
                    logger.error("Unexpected WS stream error: %s", exc, exc_info=True)
                    await websocket.send_text(
                        WSErrorEvent(
                            code="internal_error",
                            detail="An unexpected error occurred.",
                        ).model_dump_json()
                    )

    except WebSocketDisconnect:
        logger.info(
            "WS client disconnected — tenant=%s assistant=%s",
            tenant_id,
            assistant_id,
        )
    except Exception as exc:
        logger.error("WS connection error: %s", exc, exc_info=True)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
