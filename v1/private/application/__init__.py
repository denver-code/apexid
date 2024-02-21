from datetime import datetime
import re
from typing import Optional
from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, validator
from app.core.fastjwt import FastJWT


from v1.models.application import ApplicationDoc, ApplicationStatus
from v1.models.user import BirthData, UserDoc
from v1.models.notification import Notification
from v1.models.document import ServiceDocument


application_router = APIRouter(prefix="/application")


# list of available services
@application_router.get("/serviceDocuments")
async def service_documents():
    _service_documents = await ServiceDocument.find().to_list()

    return _service_documents


@application_router.get("/{service_document_id}/apply")
async def apply(service_document_id: str, request: Request):
    if not PydanticObjectId.is_valid(service_document_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid service_document_id",
        )

    service_document = await ServiceDocument.get(PydanticObjectId(service_document_id))

    if not service_document:
        raise HTTPException(
            status_code=404,
            detail="Service document not found",
        )

    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    _user = await UserDoc.get(auth_token["id"])

    _ap = await ApplicationDoc.find_one(
        {
            "user_id": _user.id,
            "service_document_id": service_document.id,
            "status": {
                "$in": [ApplicationStatus.PENDING, ApplicationStatus.AWAITING_OPERATOR]
            },
        }
    )
    if _ap:
        raise HTTPException(
            status_code=400,
            detail="Application already exists, visit cabinet to check status",
        )

    data = {}

    for field in service_document.required_fields:
        if field == "apexid":
            data[field] = str(_user.id)
            continue
        data[field] = getattr(_user, field)

    now = datetime.now()
    application = await ApplicationDoc(
        user_id=_user.id,
        service_document_id=service_document.id,
        data=data,
        created_at=now,
        modified_at=now,
    ).insert()

    await Notification(
        user_id=_user.id,
        message=f"Application 'REF_{str(application.id)}' created",
        created_at=now,
    ).insert()

    return {
        "reference": f"REF_{str(application.id)}",
    }


@application_router.get("/cabinet")
async def cabinet(request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])
    _user = await UserDoc.get(auth_token["id"])

    _ap = await ApplicationDoc.find({"user_id": _user.id}).to_list()

    applications = []

    for ap in _ap:
        service_document = await ServiceDocument.get(ap.service_document_id)

        applications.append(
            {
                "reference": f"REF_{str(ap.id)}",
                "document_name": service_document.name,
                "status": ap.status,
            }
        )

    return applications


@application_router.get("/cabinet/{reference}/status")
async def cabinet_status(reference: str, request: Request):
    if not re.match(r"REF_[a-f0-9]{24}", reference):
        raise HTTPException(
            status_code=400,
            detail="Invalid reference",
        )
    jwt_token = await FastJWT().decode(request.headers["Authorization"])
    jwt_token["id"] = PydanticObjectId(jwt_token["id"])

    _user = await UserDoc.get(jwt_token["id"])

    _ap = await ApplicationDoc.find_one({"user_id": _user.id})

    _service_document_name = (await ServiceDocument.get(_ap.service_document_id)).name

    if not _ap:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {
        "status": _ap.status,
        "document_name": _service_document_name,
    }


# get missing data
@application_router.get("/cabinet/{reference}/missing_data")
async def get_missing_data(reference: str, request: Request):
    if not re.match(r"REF_[a-f0-9]{24}", reference):
        raise HTTPException(
            status_code=400,
            detail="Invalid reference",
        )
    jwt_token = await FastJWT().decode(request.headers["Authorization"])
    jwt_token["id"] = PydanticObjectId(jwt_token["id"])

    _user = await UserDoc.get(jwt_token["id"])

    _ap = await ApplicationDoc.find_one(
        {"user_id": _user.id, "_id": PydanticObjectId(reference[4:])}
    )

    if not _ap:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if _ap.status != ApplicationStatus.AWAITING_DATA:
        raise HTTPException(
            status_code=400,
            detail="Application is not awaiting data",
        )

    # get service document
    _service_document = await ServiceDocument.get(_ap.service_document_id)

    missing_data = []
    for field in _service_document.required_fields:
        if field not in _ap.data:
            missing_data.append(field)

    return missing_data


# send missing data to application
class MissingData(BaseModel):
    data: dict

    @validator("data")
    def validate_data(cls, v):
        if not v:
            raise ValueError("Data is empty")
        return v


@application_router.post("/cabinet/{reference}/missing_data")
async def send_missing_data(reference: str, payload: MissingData, request: Request):
    if not re.match(r"REF_[a-f0-9]{24}", reference):
        raise HTTPException(
            status_code=400,
            detail="Invalid reference",
        )
    jwt_token = await FastJWT().decode(request.headers["Authorization"])
    jwt_token["id"] = PydanticObjectId(jwt_token["id"])

    _user = await UserDoc.get(jwt_token["id"])

    _ap = await ApplicationDoc.find_one(
        {"user_id": _user.id, "_id": PydanticObjectId(reference[4:])}
    )

    if not _ap:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if _ap.status != ApplicationStatus.AWAITING_DATA:
        raise HTTPException(
            status_code=400,
            detail="Application is not awaiting data",
        )

    _service_document = await ServiceDocument.get(_ap.service_document_id)

    missing_data = []
    for field in _service_document.required_fields:
        if field not in _ap.data:
            missing_data.append(field)

    provided_data = list(payload.data.keys())
    if set(provided_data) != set(missing_data):
        raise HTTPException(
            status_code=400,
            detail="Provided data does not match missing data",
        )

    _ap.data = {**_ap.data, **payload.data}
    _ap.status = ApplicationStatus.PENDING
    _ap.modified_at = datetime.now()
    await _ap.save()

    return {
        "reference": f"REF_{str(_ap.id)}",
    }


# cancel application
@application_router.delete("/{reference}")
async def cancel_application(reference: str, request: Request):
    if not re.match(r"REF_[a-f0-9]{24}", reference):
        raise HTTPException(
            status_code=400,
            detail="Invalid reference",
        )
    jwt_token = await FastJWT().decode(request.headers["Authorization"])
    jwt_token["id"] = PydanticObjectId(jwt_token["id"])

    _user = await UserDoc.get(jwt_token["id"])

    _ap = await ApplicationDoc.find_one(
        {"user_id": _user.id, "_id": PydanticObjectId(reference[4:])}
    )

    if not _ap:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if _ap.status in [ApplicationStatus.APPROVED, ApplicationStatus.REJECTED]:
        raise HTTPException(
            status_code=400,
            detail="Application is already processed",
        )

    _ap.status = ApplicationStatus.CANCELLED
    _ap.modified_at = datetime.now()
    await _ap.save()

    return {
        "reference": f"REF_{str(_ap.id)}",
    }
