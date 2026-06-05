from app.db.session import Base, TenantMixin
from sqlalchemy import Column, Integer, DateTime, text
from sqlalchemy.dialects.postgresql import UUID

class QuotaLog(Base, TenantMixin):
    __tablename__ = "quota_logs"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    period = Column(DateTime(timezone=True), nullable=False)
    message_count = Column(Integer, nullable=False, default=0)
    token_count = Column(Integer, nullable=False, default=0)
