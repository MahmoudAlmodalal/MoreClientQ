"""
Tenant management endpoints.

Exposes internal and admin tenant operations:
  - GET /tenants/resolve/{slug} — Internal slug resolution for Next.js middleware.
  - DELETE /tenants/self — Tenant offboarding (owner only).
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Header, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.db.session import get_db
from app.models.tenant import Tenant
from app.core.redis import redis_cache
from app.core.config import settings
from app.core.security import require_roles
from app.schemas.team import TenantOffboardResponse

logger = logging.getLogger(__name__)

router = APIRouter()

SLUG_CACHE_TTL = 300  # 5 minutes cache TTL for slug → tenant UUID mapping


class TenantResolveResponse(BaseModel):
    """Response schema for tenant slug resolution."""
    tenant_id: str
    slug: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


def _slug_cache_key(slug: str) -> str:
    """Build the Redis key for a tenant slug lookup."""
    return f"tenant:slug:{slug}"


async def _resolve_slug_from_db(
    slug: str,
    db: AsyncSession,
) -> Tenant | None:
    """Query PostgreSQL for a tenant by slug."""
    result = await db.execute(
        select(Tenant).where(Tenant.slug == slug)
    )
    return result.scalar_one_or_none()


@router.get(
    "/resolve/{slug}",
    response_model=TenantResolveResponse,
    summary="Resolve tenant slug to UUID",
    description=(
        "Internal service endpoint used by the Next.js middleware to validate a "
        "subdomain slug and retrieve the corresponding tenant UUID. Implements a "
        "Redis cache-aside pattern: Redis is checked first, and on a cache-miss the "
        "result is fetched from PostgreSQL and cached for subsequent requests. "
        "Requires X-Internal-Secret header for service-to-service authentication."
    ),
)
async def resolve_tenant_slug(
    slug: str,
    x_internal_secret: str | None = Header(None, alias="X-Internal-Secret"),
    db: AsyncSession = Depends(get_db),
) -> TenantResolveResponse:
    """
    Resolve a tenant subdomain slug to its UUID.

    - **Cache-aside**: Redis is checked first; on miss, falls back to PostgreSQL
      and caches the result for `SLUG_CACHE_TTL` seconds.
    - **Auth**: Expects `X-Internal-Secret` header matching `settings.INTERNAL_SECRET`
      to prevent spoofed external calls.
    - **404**: Returned if the slug is unknown or the tenant is inactive.
    """
    # --- Service authentication ---
    if not x_internal_secret or x_internal_secret != settings.INTERNAL_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid internal service secret",
        )

    cache_key = _slug_cache_key(slug)

    # --- Redis cache-aside: attempt fast path ---
    cached_value = await redis_cache.get(cache_key)
    if cached_value:
        # cached_value is stored as "<tenant_uuid>:<is_active>" e.g. "abc-123:1"
        parts = cached_value.split(":", 1)
        if len(parts) == 2:
            tenant_id_str, is_active_str = parts
            is_active = is_active_str == "1"
            if not is_active:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Tenant '{slug}' not found or inactive",
                )
            logger.debug(f"Tenant slug '{slug}' resolved from Redis cache: {tenant_id_str}")
            return TenantResolveResponse(
                tenant_id=tenant_id_str,
                slug=slug,
                is_active=True,
            )

    # --- Database fallback ---
    tenant = await _resolve_slug_from_db(slug, db)
    if not tenant:
        # Cache a negative result briefly to prevent DB hammering on bad slugs
        await redis_cache.set(cache_key, f"INVALID:0", expire=30)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{slug}' not found or inactive",
        )

    if not tenant.is_active:
        # Cache inactive result — invalidation happens when tenant is reactivated/deleted
        await redis_cache.set(
            cache_key, f"{str(tenant.id)}:0", expire=SLUG_CACHE_TTL
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{slug}' not found or inactive",
        )

    # --- Populate cache for next request ---
    await redis_cache.set(
        cache_key,
        f"{str(tenant.id)}:1",
        expire=SLUG_CACHE_TTL,
    )
    logger.debug(f"Tenant slug '{slug}' resolved from DB and cached: {str(tenant.id)}")

    return TenantResolveResponse(
        tenant_id=str(tenant.id),
        slug=slug,
        is_active=True,
    )


@router.delete(
    "/self",
    response_model=TenantOffboardResponse,
    summary="Tenant offboarding (cascade purge)",
    description=(
        "Owner-only endpoint that cascade-deletes all tenant database records "
        "and invalidates the tenant slug cache. Must be called with owner credentials."
    ),
)
async def offboard_tenant(
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_roles("owner")),
):
    tenant_id = uuid.UUID(current_user["tenant_id"])

    # Fetch the tenant
    tenant = await db.get(Tenant, tenant_id)
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )

    # Invalidate Redis slug cache
    cache_key = _slug_cache_key(tenant.slug)
    await redis_cache.delete(cache_key)
    await redis_cache.set(
        f"tenant:revoked:{tenant_id}",
        "revoked",
        expire=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    # Cascade delete tenant (all related records deleted via FK ON DELETE CASCADE)
    await db.delete(tenant)
    await db.commit()

    logger.info(f"Tenant '{tenant.slug}' ({tenant_id}) offboarded successfully.")

    return TenantOffboardResponse()
