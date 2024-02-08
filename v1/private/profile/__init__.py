from fastapi import APIRouter, Depends, HTTPException
from app.core.authorization import AuthInfo, auth_required
from app.core.config import settings
from app.core.validator import check_scope
from v1.models.application import ApplicationDoc, ApplicationStatus
from v1.models.user import UserDoc


profile_router = APIRouter(prefix="/profile")


async def is_user_active(id: str):
    _ap = await ApplicationDoc.find_one({"user_id": id})
    if _ap and _ap.status == ApplicationStatus.APPROVED:
        return
    raise HTTPException(403, "User is not active")


@profile_router.get("/my")
async def profile_me(user=Depends(auth_required)):
    await is_user_active(user["sub"])
    _user = await UserDoc.get(user["sub"])

    _user = _user.model_dump()

    del _user["metadata"]

    return _user
