from app.db.session import Base, TenantMixin
import uuid
from typing import Any

def to_uuid(value: Any) -> uuid.UUID | None:
    """Helper method to convert a string to UUID, or return if already UUID."""
    if value is None:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError):
        return None

def is_valid_uuid(value: Any) -> bool:
    """Check if value is a valid UUID."""
    if isinstance(value, uuid.UUID):
        return True
    try:
        uuid.UUID(str(value))
        return True
    except (ValueError, AttributeError):
        return False

# Import all models here so that Base.metadata has them registered.
# These will be created in the app/models/ directory.
from app.models.tenant import Tenant
from app.models.user import User
from app.models.assistant import Assistant
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.quota_log import QuotaLog
from app.models.invitation import Invitation
