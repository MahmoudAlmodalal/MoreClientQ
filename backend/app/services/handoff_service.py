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


def get_handoff_match(message: str) -> str | None:
    """
    Normalizes the message to lowercase and returns the matched handoff keyword,
    or None if no match is found.
    """
    if not message:
        return None
    match = _handoff_regex.search(message.lower())
    return match.group(0) if match else None


def is_handoff_trigger(message: str) -> bool:
    """
    Normalizes the message to lowercase and checks if it contains
    any of the handoff keywords using a compiled regex.
    """
    return get_handoff_match(message) is not None


async def trigger_handoff(
    tenant_id: UUID, conversation_id: UUID, assistant_id: UUID, message: str | None = None
) -> bool:
    """
    Updates the conversation status to 'handoff' (using RLS context),
    publishes a handoff event to the tenant's Redis channel, and returns True.
    """
    matched_keyword = None
    if message:
        matched_keyword = get_handoff_match(message)

    logger.info(
        "Handoff triggered: tenant_id=%s, conversation_id=%s, matched_keyword=%s",
        tenant_id,
        conversation_id,
        matched_keyword,
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

