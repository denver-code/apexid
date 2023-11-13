from fastapi import APIRouter, Depends, HTTPException
from app.core.authorization import AuthInfo, auth_required
from app.core.config import settings
from app.core.validator import check_scope

profile_router = APIRouter(prefix="/profile")


@profile_router.get("/my")
def profile_me(user=Depends(auth_required)):
    check_scope(["read:id_profile"], user)

    return user
