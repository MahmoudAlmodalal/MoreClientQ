from app.db.session import Base
from sqlalchemy import Column, String, Boolean, Integer, DateTime, text
from sqlalchemy.dialects.postgresql import UUID, JSONB
import datetime

class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    slug = Column(String(63), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=False)
    plan = Column(String(50), nullable=False, default="starter")
    is_active = Column(Boolean, nullable=False, default=True)
    settings = Column(JSONB, nullable=False, server_default="{}")
    monthly_quota = Column(Integer, nullable=False, default=1000)
    used_quota = Column(Integer, nullable=False, default=0)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=datetime.datetime.utcnow
    )
