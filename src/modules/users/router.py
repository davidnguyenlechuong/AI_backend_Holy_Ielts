from fastapi import APIRouter, Depends

from src.models.auth import User
from src.modules.auth.dependencies import get_current_user
from src.modules.users import service
from src.shared.responses.base import ResponseSchema

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=ResponseSchema)
async def get_me(user: User = Depends(get_current_user)):
    return ResponseSchema(message="Current user", data=service.user_to_me_dict(user))
