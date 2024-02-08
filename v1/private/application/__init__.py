from datetime import datetime
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator

from app.core.authorization import auth_required

from v1.models.application import ApplicationDoc
from v1.models.user import BirthData, UserDoc
from v1.schemas.application import ZitadelProvided
from v1.schemas.user import UserDetails


application_router = APIRouter(prefix="/application")


@application_router.post("/apply")
async def apply(payload: UserDetails, user=Depends(auth_required)):
    _user = await UserDoc.get(user.get("sub"))

    # Check if user already has an application
    # At the moment only one application is allowed
    _ap = await ApplicationDoc.find_one({"user_id": _user.id})
    if _ap:
        raise HTTPException(
            status_code=400,
            detail="Application already exists, visit cabinet to check status",
        )

    # if user is not active or missing some field it will return an error, raise an error
    try:
        # Getting user details from Zitadel
        _zd = ZitadelProvided(
            id=user.get("sub"),
            active=user.get("active"),
            email=user.get("email"),
            first_name=user.get("given_name"),
            last_name=user.get("family_name"),
            is_email_verified=user.get("email_verified"),
            gender=user.get("gender"),
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not _user:
        # To create an application user must exist in the database
        new_user = await UserDoc(
            id=_zd.id,
            # Zitadel ID is used as a AIDN (Apex ID Number)
            email=_zd.email,
            first_name=_zd.first_name,
            gender=_zd.gender,
            last_name=_zd.last_name,
            born=BirthData(
                date=payload.born.date,
                place=payload.born.place,
            ),
            phone_number=payload.phone_number,
            nationality=payload.nationality,
            metadata=payload.metadata,
        ).insert()

        _user = new_user

    now = datetime.now()
    application = await ApplicationDoc(
        user_id=_user.id,
        created_at=now,
        modified_at=now,
    ).insert()

    return {
        "reference": f"REF_{str(application.id)}",
    }


@application_router.get("/cabinet")
async def cabinet(user=Depends(auth_required)):
    _user = await UserDoc.get(user.get("sub"))
    # User is allowed to have only one application
    # So cabinet is used to get the reference of the application
    _ap = await ApplicationDoc.find_one({"user_id": _user.id})
    if not _ap:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {
        "reference": f"REF_{str(_ap.id)}",
    }


@application_router.get("/cabinet/{reference}/status/")
async def cabinet_status(reference: str, user=Depends(auth_required)):
    # TODO: Use reference in pair with user_id to get the application status
    # Because in future multiple applications will be allowed
    _user = await UserDoc.get(user.get("sub"))
    _ap = await ApplicationDoc.find_one({"user_id": _user.id})
    if not _ap:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    return {
        "status": _ap.status,
    }
