from fastapi import APIRouter, Depends

from app.core.authorization import auth_required
from app.core.validator import check_scope
from v1.private.staff.applications import staff_application_router

staff_router = APIRouter(prefix="/staff")


@staff_router.get("/test")
async def test(user=Depends(auth_required)):
    check_scope(["read:applications"], user, top_level=["admin"])

    return {"message": "You allowed to see this"}


@staff_router.get("/myId")
async def get_my_id(user=Depends(auth_required)):
    return {"id": user["sub"]}


staff_router.include_router(staff_application_router)
