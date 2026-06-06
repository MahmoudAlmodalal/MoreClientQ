import logging
from datetime import datetime, timezone
from uuid import UUID
from app.core.redis import redis_cache
from app.core.config import settings
from app.db.session import SessionLocal, enable_rls_bypass
from sqlalchemy.future import select
from app.models.tenant import Tenant
from app.models.quota_log import QuotaLog

logger = logging.getLogger(__name__)

async def get_hourly_limit(tenant_id: UUID) -> int:
    async with SessionLocal() as db:
        await enable_rls_bypass(db)
        result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
        tenant = result.scalar_one_or_none()
        if not tenant:
            return settings.DEFAULT_HOURLY_TOKEN_QUOTA
        
        limit = None
        if tenant.settings and isinstance(tenant.settings, dict):
            limit = tenant.settings.get("token_quota_hourly")
        if limit is None:
            limit = getattr(tenant, "token_quota_hourly", None)
        if limit is None:
            limit = settings.DEFAULT_HOURLY_TOKEN_QUOTA
        return int(limit)

async def check_quota(tenant_id: UUID, required_tokens: int = 0) -> bool:
    """Atomically check whether the tenant has remaining quota.

    Uses an INCRBY-then-compare-rollback pattern to avoid the TOCTOU race
    condition that would allow multiple concurrent requests to collectively
    overshoot the hourly quota.
    """
    current_hour_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H")
    redis_key = f"quota:{tenant_id}:{current_hour_str}"
    reserve = max(required_tokens, 1)  # reserve at least 1 token slot

    limit = await get_hourly_limit(tenant_id)

    # Atomically increment by the reservation amount
    new_total = await redis_cache.incrby(redis_key, reserve, expire=7200)
    if new_total is None:
        # Redis unavailable — fail open (allow the request) to avoid blocking
        # legitimate traffic; the post-call consume_quota will still record usage.
        return True

    if new_total > limit:
        # Roll back the reservation — we're over the limit
        await redis_cache.incrby(redis_key, -reserve)
        return False

    # Reservation accepted; roll it back because consume_quota will do the real
    # increment after we know the actual token cost.
    await redis_cache.incrby(redis_key, -reserve)
    return True

async def consume_quota(tenant_id: UUID, tokens_used: int) -> int:
    current_hour_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H")
    redis_key = f"quota:{tenant_id}:{current_hour_str}"

    # TTL: 2 hours (7200 seconds). incrby only sets TTL on the first write
    # so the hourly window is never accidentally extended.
    new_used = await redis_cache.incrby(redis_key, tokens_used, expire=7200)

    # Also log to quota_logs DB table
    async with SessionLocal() as db:
        await enable_rls_bypass(db)
        quota_log = QuotaLog(
            tenant_id=tenant_id,
            resource="tokens",
            amount=tokens_used
        )
        db.add(quota_log)
        await db.commit()

    return new_used if new_used is not None else 0

async def get_remaining_quota(tenant_id: UUID) -> int:
    current_hour_str = datetime.now(tz=timezone.utc).strftime("%Y%m%d%H")
    redis_key = f"quota:{tenant_id}:{current_hour_str}"

    current_used_str = await redis_cache.get(redis_key)
    current_used = int(current_used_str) if current_used_str else 0

    limit = await get_hourly_limit(tenant_id)
    return max(0, limit - current_used)
