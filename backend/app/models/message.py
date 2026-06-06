from app.db.session import Base, TenantMixin
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, text, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Message(Base, TenantMixin):
    __tablename__ = "messages"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False
    )
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    tokens_used = Column(Integer, nullable=True, default=0)
    latency_ms = Column(Integer, nullable=True)
    sources = Column(JSONB, nullable=True, server_default="[]")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    __table_args__ = (
        Index("idx_messages_conversation", "conversation_id"),
        Index("idx_messages_tenant_created", "tenant_id", text("created_at DESC")),
    )
