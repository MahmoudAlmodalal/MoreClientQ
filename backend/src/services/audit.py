import uuid
from typing import Sequence
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.audit_log import AuditLog
from src.database import tenant_context

async def record(
    db: AsyncSession,
    actor_id: uuid.UUID | str,
    role: str,
    action_type: str,
    resource: str,
    metadata: dict | None = None,
    tenant_id: uuid.UUID | str | None = None
) -> AuditLog:
    """Persist a new audit log record.
    If tenant_id is not passed, it is read from the current tenant_context.
    """
    if not tenant_id:
        ctx_tenant = tenant_context.get()
        if not ctx_tenant:
            raise ValueError("tenant_id must be provided or set in tenant_context")
        tenant_id = ctx_tenant

    if isinstance(tenant_id, str):
        tenant_id = uuid.UUID(tenant_id)
    if isinstance(actor_id, str):
        actor_id = uuid.UUID(actor_id)

    log = AuditLog(
        tenant_id=tenant_id,
        actor_id=actor_id,
        actor_role=role,
        action_type=action_type,
        resource=resource,
        metadata_=metadata
    )
    db.add(log)
    await db.flush()  # populate ID and created_at
    return log

async def list_logs(
    db: AsyncSession,
    tenant_id: uuid.UUID | str,
    limit: int = 100,
    offset: int = 0
) -> Sequence[AuditLog]:
    """Retrieve audit logs for a tenant, ordered by creation time descending."""
    if isinstance(tenant_id, str):
        tenant_id = uuid.UUID(tenant_id)

    stmt = (
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(desc(AuditLog.created_at))
        .offset(offset)
        .limit(limit)
    )
    result = await db.execute(stmt)
    return result.scalars().all()
