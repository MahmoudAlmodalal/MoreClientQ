from app.db.session import Base, TenantMixin
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey, text, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Document(Base, TenantMixin):
    __tablename__ = "documents"

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
    filename = Column(String(512), nullable=False)
    storage_key = Column(String(1024), nullable=False)
    file_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False, default="pending")
    chunk_count = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Map Python 'doc_metadata' to DB column 'metadata' to avoid conflict with Base.metadata
    doc_metadata = Column("metadata", JSONB, nullable=False, server_default="{}")
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    __table_args__ = (
        Index("idx_documents_tenant_status", "tenant_id", "status"),
        Index("idx_documents_assistant", "assistant_id"),
        UniqueConstraint("assistant_id", "filename", name="uq_documents_assistant_filename"),
    )
