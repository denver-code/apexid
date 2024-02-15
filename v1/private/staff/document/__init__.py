from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.fastjwt import FastJWT
from app.core.validate_membership import validate_membership
from v1.models.application import ApplicationDoc
from v1.models.user import StaffLevel
from datetime import datetime
from v1.schemas.document import NewServiceDocument
from v1.models.document import ApexDocument, ServiceDocument


document_router = APIRouter(prefix="/document")


@document_router.post("/create")
async def create_service_document(request: Request, payload: NewServiceDocument):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.ADMIN.value)

    service_document = await ServiceDocument(
        **payload.model_dump(),
        created_at=datetime.now(),
        updated_at=datetime.now(),
    ).insert()

    return service_document.model_dump()


# get user application by application id
@document_router.get("/{document_id}/application")
async def get_application_by_document_id(document_id: str, request: Request):
    if not PydanticObjectId.is_valid(document_id):
        raise HTTPException(400, "Invalid document_id")
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    await validate_membership(auth_token["id"], StaffLevel.STAFF.value)

    document = await ApexDocument.get(PydanticObjectId(document_id))

    if not document:
        raise HTTPException(404, "Document not found")

    if not document.metadata.get("application_id"):
        raise HTTPException(
            404,
            "Application not found in metadata, consider finding manually or report document as suspicious",
        )
    application = await ApplicationDoc.get(
        PydanticObjectId(document.metadata.get("application_id"))
    )

    return application.model_dump()
