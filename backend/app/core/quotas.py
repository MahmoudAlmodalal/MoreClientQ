from pydantic import BaseModel

class QuotaLimit(BaseModel):
    max_assistants: int | None  # None means unlimited
    max_documents: int | None   # None means unlimited

# Plan-based resource limits map
PLAN_QUOTAS: dict[str, QuotaLimit] = {
    "starter": QuotaLimit(max_assistants=1, max_documents=5),
    "pro": QuotaLimit(max_assistants=5, max_documents=100),
    "business": QuotaLimit(max_assistants=None, max_documents=None),
    "enterprise": QuotaLimit(max_assistants=None, max_documents=None),
}

def get_tenant_quotas(plan: str | None) -> QuotaLimit:
    """
    Returns the QuotaLimit configuration for a given tenant plan.
    Defaults to 'starter' plan if the plan is invalid or unrecognized.
    """
    plan_key = plan.lower() if plan else "starter"
    return PLAN_QUOTAS.get(plan_key, PLAN_QUOTAS["starter"])
