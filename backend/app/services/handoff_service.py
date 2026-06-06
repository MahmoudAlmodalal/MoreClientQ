import json
import logging
import re
from datetime import datetime, timezone
from uuid import UUID

from app.core.config import settings
from app.core.redis import redis_client
from app.db.session import SessionLocal, set_tenant_context
from app.models.conversation import Conversation
from sqlalchemy.future import select

logger = logging.getLogger(__name__)

# Compile regex from comma-separated keywords, normalized to lowercase
_keywords = [
    re.escape(k.strip().lower())
    for k in settings.HANDOFF_KEYWORDS.split(",")
    if k.strip()
]
_pattern = "|".join(_keywords)
_handoff_regex = re.compile(_pattern)


def is_handoff_trigger(message: str) -> bool:
    """
    Normalizes the message to lowercase and checks if it contains
    any of the handoff keywords using a compiled regex.
    """
    if not message:
        return False
    return bool(_handoff_regex.search(message.lower()))


async def trigger_handoff(
    tenant_id: UUID, conversation_id: UUID, assistant_id: UUID
) -> bool:
    """
    Updates the conversation status to 'handoff' (using RLS context),
    publishes a handoff event to the tenant's Redis channel, and returns True.
    """
    logger.info(
        "Initiating handoff for tenant %s, conversation %s, assistant %s",
        tenant_id,
        conversation_id,
        assistant_id,
    )
    async with SessionLocal() as db:
        await set_tenant_context(db, str(tenant_id))

        # Retrieve the conversation
        result = await db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id,
                Conversation.tenant_id == tenant_id,
            )
        )
        conversation = result.scalar_one_or_none()
        if not conversation:
            logger.error(
                "Conversation %s not found for tenant %s",
                conversation_id,
                tenant_id,
            )
            raise ValueError(f"Conversation {conversation_id} not found")

        # Update status to handoff
        conversation.status = "handoff"
        await db.commit()

    # Publish to Redis channel handoff:{tenant_id}
    channel = f"handoff:{tenant_id}"
    event_payload = {
        "conversation_id": str(conversation_id),
        "event": "handoff_requested",
        "assistant_id": str(assistant_id),
        "ts": datetime.now(timezone.utc).isoformat(),
    }
    await redis_client.publish(channel, json.dumps(event_payload))
    logger.info("Successfully published handoff event to Redis channel %s", channel)
    return True

