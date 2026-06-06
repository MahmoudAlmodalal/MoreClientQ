from pydantic import BaseModel

MAX_UPLOAD_SIZE_BYTES = 10 * 1024 * 1024
ALLOWED_DOCUMENT_FILE_TYPES = frozenset({"pdf", "docx", "txt"})
ALLOWED_DOCUMENT_MIME_TYPES = frozenset({
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "text/plain",
})

class QuotaLimit(BaseModel):
    max_assistants: int | None  # None means unlimited
    max_documents: int | None   # None means unlimited
    max_upload_size_bytes: int = MAX_UPLOAD_SIZE_BYTES
    max_storage_bytes: int | None  # None means unlimited

# Plan-based resource limits map
PLAN_QUOTAS: dict[str, QuotaLimit] = {
    "starter": QuotaLimit(
        max_assistants=1,
        max_documents=5,
        max_storage_bytes=5 * MAX_UPLOAD_SIZE_BYTES,
    ),
    "pro": QuotaLimit(
        max_assistants=5,
        max_documents=100,
        max_storage_bytes=100 * MAX_UPLOAD_SIZE_BYTES,
    ),
    "business": QuotaLimit(
        max_assistants=None,
        max_documents=None,
        max_storage_bytes=None,
    ),
    "enterprise": QuotaLimit(
        max_assistants=None,
        max_documents=None,
        max_storage_bytes=None,
    ),
}

def get_tenant_quotas(plan: str | None) -> QuotaLimit:
    """
    Returns the QuotaLimit configuration for a given tenant plan.
    Defaults to 'starter' plan if the plan is invalid or unrecognized.
    """
    plan_key = plan.lower() if plan else "starter"
    return PLAN_QUOTAS.get(plan_key, PLAN_QUOTAS["starter"])
