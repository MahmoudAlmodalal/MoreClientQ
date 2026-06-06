from app.db.session import Base, TenantMixin
from sqlalchemy import Column, Integer, DateTime, text, String
from sqlalchemy.dialects.postgresql import UUID

class QuotaLog(Base, TenantMixin):
    __tablename__ = "quota_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    resource = Column(String(50), nullable=False)
    amount = Column(Integer, nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
