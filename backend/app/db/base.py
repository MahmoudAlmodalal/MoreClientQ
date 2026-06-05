from app.db.session import Base, TenantMixin

# Import all models here so that Base.metadata has them registered.
# These will be created in the app/models/ directory.
from app.models.tenant import Tenant
from app.models.user import User
from app.models.assistant import Assistant
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.models.quota_log import QuotaLog
