import logging
import time
from uuid import UUID, uuid4
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.core.config import settings
from app.services.rag.chroma_client import chroma_client
from app.services import quota_service, llm_service
from app.models.assistant import Assistant
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import ChatResponse

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
    # System prompt
    llm_messages.append({"role": "system", "content": assistant.system_prompt})
    
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
    response = await llm_service.complete_with_fallback(llm_messages, stream=False)
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
