from datetime import datetime
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.fastjwt import FastJWT
from app.core.validate_membership import validate_membership
from v1.models.application import ApplicationDoc, ApplicationStatus
from v1.models.user import UserDoc, StaffLevel, StaffMembership
from v1.models.document import ServiceDocument, ApexDocument
from v1.schemas.application import ApplicationVerdictMessage
from v1.models.notification import Notification


staff_application_router = APIRouter(prefix="/application")


@staff_application_router.get("/all")
async def get_all_applications(request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.ADMIN.value)

    _applications = await ApplicationDoc.all().to_list()
    applications = []

    for application in _applications:
        applications.append(application.model_dump())

    return applications


@staff_application_router.patch("/{application_id}/assign/{operator}")
async def assign_application(application_id: str, operator: str, request: Request):
    # check if application id and operator id are valid
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    if not PydanticObjectId.is_valid(operator):
        raise HTTPException(400, "Invalid operator_id")

    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    initiator_membership = await validate_membership(
        auth_token["id"], StaffLevel.OPERATOR.value
    )

    # check if operator have enough permissions
    operator_membership = await StaffMembership.find_one(
        {"user_id": PydanticObjectId(operator)}
    )
    if not operator_membership:
        raise HTTPException(403, "Operator is not a staff member")

    # check if operator level is lower than the initiator
    if operator_membership.level.value > initiator_membership.value:
        raise HTTPException(403, "You do not have enough permissions")

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if not application:
        raise HTTPException(404, "Application not found")

    if application.status != ApplicationStatus.AWAITING_OPERATOR:
        raise HTTPException(400, "Application already assigned")

    application.operator_id = PydanticObjectId(operator)
    application.status = ApplicationStatus.PENDING

    await application.save()

    await Notification(
        user_id=str(application.user_id),
        message=f"Application 'REF_{str(application.id)}' assigned to operator",
        created_at=datetime.now(),
    ).insert()

    return {
        "message": "Application assigned to operator",
    }


@staff_application_router.patch("/{application_id}/deassign")
async def deassign_application(application_id: str, request: Request):
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.ADMIN.value)

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if not application:
        raise HTTPException(404, "Application not found")

    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(400, "Application already processed")

    application.operator_id = None
    application.status = ApplicationStatus.AWAITING_OPERATOR

    await application.save()

    await Notification(
        user_id=str(application.user_id),
        message=f"Application 'REF_{str(application.id)}' deassigned from operator",
        created_at=datetime.now(),
    ).insert()

    return {
        "message": "Application deassigned",
    }


@staff_application_router.get("/assignments")
async def get_assignments(request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.JUNIOR_OPERATOR.value)

    _applications = await ApplicationDoc.find(
        {
            "operator_id": auth_token["id"],
            "status": ApplicationStatus.PENDING,
        }
    ).to_list()
    applications = []

    for application in _applications:
        applications.append(application.model_dump())

    return applications


# Aprove or reject application
@staff_application_router.patch("/{application_id}/status")
async def change_application_status(
    application_id: str,
    status: ApplicationStatus,
    request: Request,
    message: ApplicationVerdictMessage = None,
):
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    if status not in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED]:
        raise HTTPException(400, "Invalid status")

    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.ADMIN.value)

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if not application:
        raise HTTPException(404, "Application not found")

    if application.status == ApplicationStatus.AWAITING_DATA:
        raise HTTPException(400, "Application is awaiting missing data")

    if application.status != ApplicationStatus.PENDING:
        raise HTTPException(400, "Application already processed")

    if status == ApplicationStatus.REJECTED:
        application.status = status

        if message:
            application.message = message.message

        await application.save()

    if status == ApplicationStatus.APPROVED:
        service_document = await ServiceDocument.get(application.service_document_id)

        missing_data = []

        for field in service_document.required_fields:
            if field not in application.data:
                missing_data.append(field)

        if missing_data:
            raise HTTPException(
                400, f"Application is missing data, approving is not possible!"
            )

        application.status = status

        if message:
            application.message = message.message

        await application.save()

        apex_doc = await ApexDocument(
            user_id=application.user_id,
            application_id=application.id,
            data=application.data,
            service_id=application.service_document_id,
            metadata={
                "application_id": str(application.id),
            },
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ).insert()

        await Notification(
            user_id=str(application.user_id),
            message=f"Congratulations! Your application for '{service_document.name}' is approved. Your 'DOC_{str(apex_doc.id)}' is ready.",
            created_at=datetime.now(),
        ).insert()

    await Notification(
        user_id=str(application.user_id),
        message=f"Application 'REF_{str(application.id)}' is {status.value}. Message: '{message.message if message else 'Has no message from operator'}'",
        created_at=datetime.now(),
    ).insert()

    return {
        "message": "Application status changed",
    }


# analyze application and the service document and return the expected result
@staff_application_router.get("/{application_id}/analyze")
async def analyze_application(application_id: str, request: Request):
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.JUNIOR_OPERATOR.value)

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if not application:
        raise HTTPException(404, "Application not found")

    # check if application operator is the same as the current user
    if application.operator_id != auth_token["id"]:
        raise HTTPException(403, "You are not assigned to this application")

    service_document = await ServiceDocument.get(application.service_document_id)

    # compare application data with service document data
    missing_fields = []
    for field in service_document.required_fields:
        if field not in application.data:
            missing_fields.append(field)

    return {
        "result": "Application analyzed",
        "missing_fields": missing_fields,
        "message": (
            "All fields are present in the application data"
            if not missing_fields
            else "Application data is missing some fields, request user to fill them"
        ),
    }


# set application field value
@staff_application_router.patch("/{application_id}/data")
async def set_application_data(
    application_id: str, field: str, value: str, request: Request
):
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    if not field or not value:
        raise HTTPException(400, "Invalid field or value")
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.OPERATOR.value)

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    service_document = await ServiceDocument.get(application.service_document_id)

    if not application:
        raise HTTPException(404, "Application not found")

    # check if application operator is the same as the current user
    if application.operator_id != auth_token["id"]:
        raise HTTPException(403, "You are not assigned to this application")

    if field not in service_document.required_fields:
        raise HTTPException(
            400, "Field do not exist in service document required fields"
        )

    application.data[field] = value

    await application.save()

    await Notification(
        user_id=str(application.user_id),
        message=f"Application 'REF_{str(application.id)}' data updated. Field: {field} Value: {value}",
        created_at=datetime.now(),
    ).insert()

    return {
        "message": "Application data updated",
    }


# request missing application data
@staff_application_router.get("/{application_id}/request_data")
async def request_missing_data(application_id: str, request: Request):
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.JUNIOR_OPERATOR.value)

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    service_document = await ServiceDocument.get(application.service_document_id)

    if not application:
        raise HTTPException(404, "Application not found")

    # check if application operator is the same as the current user
    if application.operator_id != auth_token["id"]:
        raise HTTPException(403, "You are not assigned to this application")

    missing_fields = []
    for field in service_document.required_fields:
        if field not in application.data:
            missing_fields.append(field)

    if not missing_fields:
        raise HTTPException(400, "No missing fields")

    application.status = ApplicationStatus.AWAITING_DATA

    await application.save()

    await Notification(
        user_id=str(application.user_id),
        message=f"Please fill the missing fields in the application 'REF_{application.id}' data: {' '.join(missing_fields)}",
        created_at=datetime.now(),
    ).insert()

    return {
        "message": "Missing fields requested sent to user notifications",
        "missing_fields": missing_fields,
    }


# get user profile by application id
@staff_application_router.get("/{application_id}/user")
async def get_user_by_application_id(application_id: str, request: Request):
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.STAFF.value)

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if not application:
        raise HTTPException(404, "Application not found")

    user = await UserDoc.get(application.user_id)

    del user.password

    return user.model_dump()


# get user documents by application id
@staff_application_router.get("/{application_id}/documents")
async def get_user_documents_by_application_id(application_id: str, request: Request):
    if not PydanticObjectId.is_valid(application_id):
        raise HTTPException(400, "Invalid application_id")
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.STAFF.value)

    application = await ApplicationDoc.get(PydanticObjectId(application_id))

    if not application:
        raise HTTPException(404, "Application not found")

    documents = await ApexDocument.find({"user_id": application.user_id}).to_list()

    return documents
