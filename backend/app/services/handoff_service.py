from uuid import UUID

def is_handoff_trigger(message: str) -> bool:
    """
    Stub for handoff trigger keyword matching.
    Always returns False.
    """
    return False

async def trigger_handoff(tenant_id: UUID, conversation_id: UUID, assistant_id: UUID) -> None:
    """
    Stub for triggering human handoff.
    """
    pass
