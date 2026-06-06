from fastapi import APIRouter, Depends, HTTPException, status
from app.core.security import require_roles

router = APIRouter()

@router.get("")
async def list_users(current_user: dict = Depends(require_roles("owner", "admin", "member"))):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@router.post("/invite")
async def invite_user(current_user: dict = Depends(require_roles("owner", "admin"))):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@router.patch("/{user_id}")
async def update_user_role(user_id: str, current_user: dict = Depends(require_roles("owner", "admin"))):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")

@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(require_roles("owner", "admin"))):
    raise HTTPException(status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Not implemented")
