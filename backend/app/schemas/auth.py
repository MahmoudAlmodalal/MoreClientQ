from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
import re
import uuid

class TenantRegister(BaseModel):
    tenant_slug: str = Field(..., max_length=63, description="Tenant subdomain/slug")
    tenant_name: str = Field(..., max_length=255, description="Tenant business name")
    owner_email: EmailStr = Field(..., description="Email of the primary owner")
    owner_password: str = Field(..., min_length=8, description="Secure owner password")
    owner_full_name: str | None = Field(None, max_length=255, description="Full name of the owner")

    @field_validator("tenant_slug")
    @classmethod
    def validate_slug(cls, v: str) -> str:
        if not re.match(r"^[a-z0-9]+$", v):
            raise ValueError("Tenant slug must be lowercase and alphanumeric (no special characters or spaces)")
        return v

class TenantResponse(BaseModel):
    id: uuid.UUID
    slug: str
    name: str
    plan: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    full_name: str | None = None
    role: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)

class RegistrationResponse(BaseModel):
    tenant: TenantResponse
    owner: UserResponse

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int

class TokenRefreshRequest(BaseModel):
    refresh_token: str

