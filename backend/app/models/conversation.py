from app.db.session import Base, TenantMixin
from sqlalchemy import Column, String, DateTime, ForeignKey, text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Conversation(Base, TenantMixin):
    __tablename__ = "conversations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    assistant_id = Column(
        UUID(as_uuid=True),
        ForeignKey("assistants.id", ondelete="CASCADE"),
        nullable=False
    )
    session_token = Column(String(255), unique=True, index=True, nullable=False)
    visitor_name = Column(String(255), nullable=True)
    visitor_email = Column(String(255), nullable=True)
    status = Column(String(50), nullable=False, default="active")
    channel = Column(String(50), nullable=False, default="web")
    
    # Map Python 'conv_metadata' to DB column 'metadata' to avoid conflict with Base.metadata
    conv_metadata = Column("metadata", JSONB, nullable=False, server_default="{}")
    
    started_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    ended_at = Column(DateTime(timezone=True), nullable=True)

    __table_args__ = (
        Index("idx_conversations_tenant", "tenant_id"),
    )
