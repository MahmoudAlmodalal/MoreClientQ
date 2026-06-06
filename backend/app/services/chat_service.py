import asyncio
import logging
import time
from typing import AsyncGenerator, Any
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.db.session import set_tenant_context
from app.services.rag.chroma_client import chroma_client
from app.services import quota_service, llm_service
from app.models.assistant import Assistant
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ChatResponse, SourceReference

logger = logging.getLogger(__name__)

class QuotaExceededError(Exception):
    """Exception raised when the tenant's token quota is exceeded."""
    pass

class AssistantNotFoundError(Exception):
    """Exception raised when an assistant is not found."""
    pass

class ConversationNotFoundError(Exception):
    """Exception raised when a conversation is not found."""
    pass

class ConversationInHandoffError(Exception):
    """Exception raised when a conversation is in handoff mode."""
    pass

async def chat(
    db: AsyncSession,
    tenant_id: UUID,
    assistant_id: UUID,
    conversation_id: UUID | None,
    user_content: str
) -> ChatResponse:
    # Safety guard: explicitly bind RLS tenant context on this session.
    # The middleware already does this via get_db(), but we enforce it here
    # so the service is safe if called from a background task or test directly.
    await set_tenant_context(db, str(tenant_id))

    # 1. Validate assistant belongs to tenant (DB query with RLS context)
    assistant_res = await db.execute(
        select(Assistant).where(
            Assistant.id == assistant_id,
            Assistant.tenant_id == tenant_id
        )
    )
    assistant = assistant_res.scalar_one_or_none()
    if not assistant:
        raise AssistantNotFoundError("Assistant not found")

    # 2. Create or load conversation record
    conversation = None
    if conversation_id:
        conv_res = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id
            )
        )
        conversation = conv_res.scalar_one_or_none()
        if not conversation:
            raise ConversationNotFoundError("Conversation not found")
        
        # Check if conversation is in handoff
        if conversation.status == "handoff":
            raise ConversationInHandoffError("Conversation is in handoff mode; AI responses are suspended")
    else:
        # Create a new conversation
        conversation = Conversation(
            tenant_id=tenant_id,
            assistant_id=assistant_id,
            session_token=uuid4().hex,
            status="bot",
            channel="web",
            title=user_content[:100]  # Auto-generate title from first message
        )
        db.add(conversation)
        await db.flush()  # Generate conversation.id

    # 3. Pre-flight check_quota
    if not await quota_service.check_quota(tenant_id, required_tokens=0):
        raise QuotaExceededError("Token quota exceeded for this billing period")

    # 4. Retrieve history: last 10 messages from messages table ordered by created_at DESC limit 10, reversed
    history_res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history = list(history_res.scalars().all())
    history.reverse()

    # 5. Retrieve context
    sources = await chroma_client.retrieve(str(tenant_id), user_content, top_k=settings.RAG_TOP_K)
    
    # 6. Build LLM messages array
    llm_messages = []
    # System prompt — guard against NULL system_prompt which OpenAI rejects
    system_prompt = assistant.system_prompt or "You are a helpful AI assistant."
    llm_messages.append({"role": "system", "content": system_prompt})
    
    # Context note or content
    if not sources:
        context_note = "No relevant information was found in the knowledge base. Politely inform the user."
        llm_messages.append({"role": "system", "content": context_note})
    else:
        context_content = "Use the following context to help answer the user's question:\n\n"
        for src in sources:
            context_content += f"Document: {src.document_id}\nContent: {src.chunk_text}\n\n"
        llm_messages.append({"role": "system", "content": context_content})

    # Append history
    for msg in history:
        llm_messages.append({"role": msg.role, "content": msg.content})

    # Append user message
    llm_messages.append({"role": "user", "content": user_content})

    # 7. Call llm_service
    start_time = time.perf_counter()
    try:
        response = await llm_service.complete_with_fallback(llm_messages, stream=False)
    except Exception as e:
        logger.error(
            "LLM failure in chat: tenant_id=%s, conversation_id=%s, error=%s",
            tenant_id,
            conversation.id if conversation else None,
            str(e),
            exc_info=True
        )
        raise
    latency_ms = int((time.perf_counter() - start_time) * 1000)

    content = response.choices[0].message.content
    tokens_used = response.usage.total_tokens if response.usage else 0
    model_used = response.model

    # 8. Persist user Message record
    user_message = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        role="user",
        content=user_content,
        tokens_used=0,
        latency_ms=0,
        sources=[]
    )
    db.add(user_message)

    # 9. Persist assistant Message record
    sources_data = [src.model_dump() for src in sources]
    assistant_message = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        role="assistant",
        content=content,
        tokens_used=tokens_used,
        latency_ms=latency_ms,
        sources=sources_data
    )
    db.add(assistant_message)

    # Commit changes
    await db.flush()
    await db.commit()

    # 10. Consume quota
    await quota_service.consume_quota(tenant_id, tokens_used)

    logger.info(
        "Successful chat turn: tenant_id=%s, conversation_id=%s, model_used=%s, tokens_used=%d, latency_ms=%d",
        tenant_id,
        conversation.id,
        model_used,
        tokens_used,
        latency_ms
    )

    # 11. Return ChatResponse
    return ChatResponse(
        conversation_id=conversation.id,
        message_id=assistant_message.id,
        role="assistant",
        content=content,
        tokens_used=tokens_used,
        sources=sources,
        model_used=model_used
    )


async def stream_chat(
    db: AsyncSession,
    tenant_id: UUID,
    assistant_id: UUID,
    conversation_id: UUID | None,
    user_content: str
) -> AsyncGenerator[Any, None]:
    """
    Async generator that streams LLM response tokens for real-time delivery.

    Yields:
        str: individual token deltas from the LLM
        "quota_exceeded": sentinel when mid-stream quota limit is hit
        dict: final "done" sentinel with conversation_id, message_id, tokens_used, model_used, sources
    On asyncio.CancelledError (client disconnect): persists partial response with "[response truncated]".
    """
    # Safety guard: explicitly bind RLS tenant context (mirrors chat() above).
    await set_tenant_context(db, str(tenant_id))

    # 1. Validate assistant belongs to tenant
    assistant_res = await db.execute(
        select(Assistant).where(
            Assistant.id == assistant_id,
            Assistant.tenant_id == tenant_id
        )
    )
    assistant = assistant_res.scalar_one_or_none()
    if not assistant:
        raise AssistantNotFoundError("Assistant not found")

    # 2. Create or load conversation record
    conversation = None
    if conversation_id:
        conv_res = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id
            )
        )
        conversation = conv_res.scalar_one_or_none()
        if not conversation:
            raise ConversationNotFoundError("Conversation not found")
        if conversation.status == "handoff":
            raise ConversationInHandoffError("Conversation is in handoff mode; AI responses are suspended")
    else:
        conversation = Conversation(
            tenant_id=tenant_id,
            assistant_id=assistant_id,
            session_token=uuid4().hex,
            status="bot",
            channel="web",
            title=user_content[:100]
        )
        db.add(conversation)
        await db.flush()

    # 3. Pre-flight quota check
    if not await quota_service.check_quota(tenant_id, required_tokens=0):
        raise QuotaExceededError("Token quota exceeded for this billing period")

    # 4. Retrieve history: last 10 messages ordered by created_at DESC, reversed
    history_res = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.created_at.desc())
        .limit(10)
    )
    history = list(history_res.scalars().all())
    history.reverse()

    # 5. Retrieve RAG context
    sources = await chroma_client.retrieve(str(tenant_id), user_content, top_k=settings.RAG_TOP_K)

    # 6. Build LLM messages array
    # Guard against NULL system_prompt — OpenAI rejects None content fields.
    system_prompt = assistant.system_prompt or "You are a helpful AI assistant."
    llm_messages = [{"role": "system", "content": system_prompt}]
    if not sources:
        llm_messages.append({"role": "system", "content": "No relevant information was found in the knowledge base. Politely inform the user."})
    else:
        context_content = "Use the following context to help answer the user's question:\n\n"
        for src in sources:
            context_content += f"Document: {src.document_id}\nContent: {src.chunk_text}\n\n"
        llm_messages.append({"role": "system", "content": context_content})

    for msg in history:
        llm_messages.append({"role": msg.role, "content": msg.content})
    llm_messages.append({"role": "user", "content": user_content})

    # Persist user message before streaming begins
    user_message = Message(
        tenant_id=tenant_id,
        conversation_id=conversation.id,
        role="user",
        content=user_content,
        tokens_used=0,
        latency_ms=0,
        sources=[]
    )
    db.add(user_message)
    await db.flush()

    # Stream tokens
    collected_tokens: list[str] = []
    tokens_used = 0
    model_used: str | None = None
    start_time = time.perf_counter()
    quota_hit = False

    try:
        stream = await llm_service.complete_with_fallback(llm_messages, stream=True)

        async for chunk in stream:
            delta = chunk.choices[0].delta.content if chunk.choices and chunk.choices[0].delta.content else ""
            if not model_used and hasattr(chunk, "model"):
                model_used = chunk.model
            if delta:
                collected_tokens.append(delta)
                tokens_used += 1  # approximate; exact count in done event from usage

                # Check running quota mid-stream
                remaining = await quota_service.get_remaining_quota(tenant_id)
                if remaining <= 0:
                    quota_hit = True
                    yield "quota_exceeded"
                    break

                yield delta

        latency_ms = int((time.perf_counter() - start_time) * 1000)
        full_content = "".join(collected_tokens)

        # Persist assistant message
        sources_data = [src.model_dump() for src in sources]
        assistant_message = Message(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            role="assistant",
            content=full_content + (" [response truncated]" if quota_hit else ""),
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            sources=sources_data
        )
        db.add(assistant_message)
        await db.flush()
        await db.commit()

        await quota_service.consume_quota(tenant_id, tokens_used)

        if not quota_hit:
            logger.info(
                "Successful chat turn: tenant_id=%s, conversation_id=%s, model_used=%s, tokens_used=%d, latency_ms=%d",
                tenant_id,
                conversation.id,
                model_used,
                tokens_used,
                latency_ms
            )
            yield {
                "type": "done",
                "conversation_id": conversation.id,
                "message_id": assistant_message.id,
                "tokens_used": tokens_used,
                "model_used": model_used,
                "sources": sources,
            }

    except asyncio.CancelledError:
        # Client disconnected mid-stream — persist partial response
        latency_ms = int((time.perf_counter() - start_time) * 1000)
        partial_content = "".join(collected_tokens) + " [response truncated]"
        sources_data = [src.model_dump() for src in sources]
        assistant_message = Message(
            tenant_id=tenant_id,
            conversation_id=conversation.id,
            role="assistant",
            content=partial_content,
            tokens_used=tokens_used,
            latency_ms=latency_ms,
            sources=sources_data
        )
        db.add(assistant_message)
        try:
            await db.flush()
            await db.commit()
            if tokens_used > 0:
                await quota_service.consume_quota(tenant_id, tokens_used)
        except Exception:
            pass
        raise
    except Exception as e:
        logger.error(
            "LLM failure in stream_chat: tenant_id=%s, conversation_id=%s, error=%s",
            tenant_id,
            conversation.id if conversation else None,
            str(e),
            exc_info=True
        )
        raise
