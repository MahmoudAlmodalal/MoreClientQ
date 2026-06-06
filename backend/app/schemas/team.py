from pydantic import BaseModel, EmailStr, Field, ConfigDict
import uuid
from datetime import datetime


class InviteRequest(BaseModel):
    email: EmailStr
    role: str = Field(..., pattern=r"^(admin|member|viewer)$")


class InviteResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    invitation_link: str

    model_config = ConfigDict(from_attributes=True)


class InviteResponseWrapper(BaseModel):
    status: str = "success"
    message: str = "Invitation created successfully"
    data: InviteResponse


class AcceptInviteRequest(BaseModel):
    token: str
    password: str = Field(..., min_length=8)


class AcceptInviteData(BaseModel):
    user_id: uuid.UUID
    email: str
    role: str


class AcceptInviteResponse(BaseModel):
    status: str = "success"
    message: str = "Invitation accepted successfully. Account activated."
    data: AcceptInviteData


class UserListResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UpdateRoleRequest(BaseModel):
    role: str = Field(..., pattern=r"^(admin|member|viewer)$")


class UpdateRoleData(BaseModel):
    id: uuid.UUID
    role: str


class UpdateRoleResponse(BaseModel):
    status: str = "success"
    message: str = "User role updated successfully"
    data: UpdateRoleData


class DeleteUserResponse(BaseModel):
    status: str = "success"
    message: str = "User deleted successfully"


class TenantOffboardResponse(BaseModel):
    status: str = "success"
    message: str = "Tenant offboarded successfully. PostgreSQL cascade deleted, JWT active sessions blocklisted."
