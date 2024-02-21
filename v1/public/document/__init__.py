from fastapi import APIRouter, Depends, HTTPException, Request
import datetime
from v1.models.document import ApexDocument, ConfrimationToken, ServiceDocument
from beanie import PydanticObjectId
import re

document_router = APIRouter(prefix="/document")


async def delete_confirmation_token(token: str):
    await ConfrimationToken.find_one({"_id": PydanticObjectId(token)}).delete()


# get document by confirmation token
@document_router.get("/verify/{token}")
async def get_document_by_token(token: str):
    if not re.match(r"^[a-f\d]{24}$", token):
        raise HTTPException(
            status_code=400,
            detail="Invalid token",
        )
    _token = await ConfrimationToken.find_one({"_id": PydanticObjectId(token)})
    if not _token:
        raise HTTPException(
            status_code=404,
            detail="Document is invalid",
        )

    if _token.expire_at < datetime.datetime.now():
        await delete_confirmation_token(token)
        raise HTTPException(
            status_code=400,
            detail="Token expired",
        )

    _document = await ApexDocument.get(_token.document_id)
    if not _document:
        # TODO: report suspicious activity
        await delete_confirmation_token(token)
        raise HTTPException(
            status_code=404,
            detail="Document is invalid",
        )

    _service_document = await ServiceDocument.get(_document.service_id)

    try:
        _public_data = {
            "document_name": _service_document.name,
            "DOB": _document.data["born"]["date"],
            "document_id": str(_document.id),
            "first_name": _document.data["first_name"],
            "last_name": _document.data["last_name"],
        }
    except:
        # TODO: report broken document
        await delete_confirmation_token(token)
        raise HTTPException(
            status_code=404,
            detail="Document is invalid",
        )

    return _public_data
