from fastapi import HTTPException

from v1.models.user import StaffMembership


async def validate_membership(user_id, required_membership: int):
    user_membership = await StaffMembership.find_one({"user_id": user_id})
    if not user_membership:
        raise HTTPException(403, "You are not a staff member")

    if user_membership.level.value < required_membership:
        raise HTTPException(403, "You do not have enough permissions")

    return user_membership.level
