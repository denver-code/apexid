from fastapi import APIRouter, Depends, HTTPException, Request
from v1.private.staff.applications import staff_application_router
from beanie import PydanticObjectId
from app.core.fastjwt import FastJWT
from v1.models.application import ApplicationDoc, ApplicationStatus
from v1.models.user import UserDoc, StaffLevel, StaffMembership
from v1.private.staff.document import document_router
from datetime import datetime


staff_router = APIRouter(prefix="/staff")

staff_router.include_router(staff_application_router)
staff_router.include_router(document_router)


@staff_router.post("/promote")
async def promote_user(user_id: str, level: int, request: Request):
    if not user_id or not PydanticObjectId.is_valid(user_id):
        raise HTTPException(400, "Invalid user_id")
    user_id = PydanticObjectId(user_id)

    if level not in StaffLevel._value2member_map_:
        raise HTTPException(400, "Invalid level")

    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    user = await UserDoc.get(auth_token["id"])
    _initiator_membership = await StaffMembership.find_one({"user_id": user.id})
    if not _initiator_membership:
        raise HTTPException(403, "You are not a staff member")

    if _initiator_membership.level.value < StaffLevel.ADMIN.value:
        raise HTTPException(403, "You do not have enough permissions")

    if level > _initiator_membership.level.value:
        raise HTTPException(403, "You do not have enough permissions")

    target_user = await UserDoc.get(PydanticObjectId(user_id))
    if not target_user:
        raise HTTPException(404, "User not found")

    user_membership = await StaffMembership.find_one({"user_id": user_id})

    if user_membership and user_membership.level.value == level:
        raise HTTPException(400, "User already has this level")

    if user_membership and (
        user_membership.level.value > level
        and _initiator_membership.level.value < user_membership.level.value
    ):
        raise HTTPException(403, "You do not have enough permissions")

    if not user_membership:
        user_membership = StaffMembership(
            user_id=PydanticObjectId(user_id),
            membership=StaffLevel(level),
            promoted_by=auth_token["id"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
    else:
        user_membership.level = StaffLevel(level)
        user_membership.promoted_by = auth_token["id"]
        user_membership.updated_at = datetime.now()

    await user_membership.save()
    return {"message": "User promoted"}
