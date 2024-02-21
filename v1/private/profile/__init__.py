from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Request
import datetime
from app.core.config import settings
from app.core.fastjwt import FastJWT
from v1.models.document import ApexDocument, ConfrimationToken, ServiceDocument
from v1.models.application import ApplicationDoc, ApplicationStatus
from v1.models.user import UserDoc
from v1.models.authorized_device import AuthorizedDevice
from v1.models.notification import Notification


profile_router = APIRouter(prefix="/profile")


async def is_user_active(id: str):
    _ap = await ApplicationDoc.find_one({"user_id": id})
    if _ap and _ap.status == ApplicationStatus.APPROVED:
        return
    raise HTTPException(403, "User is not active")


@profile_router.get("/my")
async def profile(request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    await is_user_active(auth_token["id"])

    _user = await UserDoc.get(auth_token["id"])
    _user = _user.model_dump()

    to_show = [
        "id",
        "first_name",
    ]
    for key in list(_user.keys()):
        if key not in to_show:
            _user.pop(key)

    return _user


@profile_router.get("/my/devices")
async def devices(request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    _devices = await AuthorizedDevice.find(
        {"user_id": auth_token["id"]},
    ).to_list()

    return _devices


# delete device
@profile_router.delete("/my/devices/{device_id}")
async def delete_device(device_id: str, request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    _device = await AuthorizedDevice.get(device_id)
    if not _device:
        raise HTTPException(
            status_code=404,
            detail="Device not found",
        )

    if _device.user_id != auth_token["id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to delete this device",
        )

    await _device.delete()
    return {"status": "ok"}


# get all notifications sorted
@profile_router.get("/my/notifications")
async def notifications(request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    _notifications = (
        await Notification.find(
            {"user_id": auth_token["id"]},
        )
        .sort("-created_at")
        .to_list()
    )

    return _notifications


# get my documents
@profile_router.get("/my/documents")
async def documents(request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    _documents = await ApexDocument.find(
        {"user_id": auth_token["id"]},
    ).to_list()

    return _documents


# get my document
@profile_router.get("/my/documents/{document_id}")
async def document(document_id: str, request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    _document = await ApexDocument.get(document_id)
    if not _document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if _document.user_id != auth_token["id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to view this document",
        )

    return _document


# Generate the confirmation token for the document that will expire in 3 minutes
@profile_router.get("/my/documents/{document_id}/confirm")
async def confirm_document(document_id: str, request: Request):
    auth_token = await FastJWT().decode(request.headers["Authorization"])
    auth_token["id"] = PydanticObjectId(auth_token["id"])

    _document = await ApexDocument.get(document_id)
    if not _document:
        raise HTTPException(
            status_code=404,
            detail="Document not found",
        )

    if _document.user_id != auth_token["id"]:
        raise HTTPException(
            status_code=403,
            detail="You are not allowed to confirm this document",
        )

    # delete all old tokens of the user
    await ConfrimationToken.find({"user_id": auth_token["id"]}).delete()

    _token = ConfrimationToken(
        user_id=auth_token["id"],
        document_id=_document.id,
    )
    await _token.insert()

    return {"token": str(_token.id)}
