from app.db.session import Base, TenantMixin
from sqlalchemy import Column, String, Boolean, Integer, Float, Text, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB

class Assistant(Base, TenantMixin):
    __tablename__ = "assistants"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    name = Column(String(255), nullable=False)
    system_prompt = Column(Text, nullable=False, default="")
    model = Column(String(100), nullable=False, default="gpt-4o-mini")
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=False, default=1024)
    is_active = Column(Boolean, nullable=False, default=True)
    widget_config = Column(JSONB, nullable=False, server_default="{}")
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
