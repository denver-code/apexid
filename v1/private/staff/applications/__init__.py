from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from app.core.authorization import auth_required
from app.core.validator import check_scope
from v1.models.application import ApplicationDoc, ApplicationStatus

staff_application_router = APIRouter(prefix="/application")


@staff_application_router.get("/all")
async def get_all_applications(user=Depends(auth_required)):
    check_scope(["read:applications"], user, top_level=["admin"])

    _applications = await ApplicationDoc.all().to_list()
    applications = []

    for application in _applications:
        applications.append(application.model_dump())

    return applications


@staff_application_router.patch("/{application_id}/assign/{operator}")
async def assign_application(
    application_id: str, operator: str, user=Depends(auth_required)
):
    check_scope(["assign:applications"], user, top_level=["admin"])

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if not application:
        raise HTTPException(404, "Application not found")

    if application.status != ApplicationStatus.AWAITING_OPERATOR:
        raise HTTPException(400, "Application already assigned")

    application.operator_id = operator
    application.status = ApplicationStatus.PENDING

    await application.save()

    return {
        "message": "Application assigned to operator",
    }


@staff_application_router.patch("/{application_id}/approve")
async def approve_application(application_id: str, user=Depends(auth_required)):
    check_scope(["approve:applications"], user, top_level=["admin"])

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if application.operator_id != user["sub"]:
        raise HTTPException(403, "You are not assigned to this application")

    if not application:
        raise HTTPException(404, "Application not found")

    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(400, "Application already approved")

    application.status = ApplicationStatus.APPROVED

    await application.save()

    return {
        "message": "Application approved",
    }
