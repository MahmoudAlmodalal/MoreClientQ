from app.db.session import Base, TenantMixin
from sqlalchemy import Column, String, DateTime, text
from sqlalchemy.dialects.postgresql import UUID

class Invitation(Base, TenantMixin):
    __tablename__ = "invitations"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    email = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    token = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    accepted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )
