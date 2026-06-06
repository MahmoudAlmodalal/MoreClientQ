from app.db.session import Base, TenantMixin
from sqlalchemy import Column, String, Boolean, DateTime, text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID

class User(Base, TenantMixin):
    __tablename__ = "users"

    id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()")
    )
    email = Column(String(255), nullable=False)
    hashed_password = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    role = Column(String(50), nullable=False, default="member")
    is_active = Column(Boolean, nullable=False, default=True)
    last_login = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()")
    )

    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
    )
