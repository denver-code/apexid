from datetime import datetime
import re
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, validator

from app.core.authorization import auth_required
from app.core.email_fixer import EmailFixer
from v1.models.application import ApplicationDoc
from v1.models.user import BirthData, UserDoc

application_router = APIRouter(prefix="/application")

""" 
ZITADEL-PROVIDED DATA:
email
firstName
lastName
email_verified
gender

TO-PROVIDE DATA:
phone number
nationality
birth date
birth place
"""


class ZitadelProvided(BaseModel):
    id: str
    active: bool
    email: str
    first_name: str
    last_name: str
    is_email_verified: bool
    gender: str

    @validator("is_email_verified")
    def check_email_verified(cls, v):
        if not v:
            raise ValueError("Email not verified")
        return v

    @validator("email")
    def check_email_event(cls, v):
        regex = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b"
        if not re.fullmatch(regex, v):
            raise ValueError("Invalid email")
        v = EmailFixer.fix(v)
        return v

    @validator("gender")
    def check_gender(cls, v):
        if v not in ["male", "female"]:
            raise ValueError("Invalid gender")

        return v


class UserDetails(BaseModel):
    phone_number: str
    nationality: str
    born: BirthData
    metadata: Optional[dict] = {}


class GeneralUserID(BaseModel):
    email: str
    first_name: str
    last_name: str
    gender: str
    born: BirthData
    phone_number: str
    nationality: str
    metadata: dict = {}


class Application(BaseModel):
    payload: UserDetails


@application_router.post("/apply")
async def apply(payload: UserDetails, user=Depends(auth_required)):
    _user = await UserDoc.get(user.get("sub"))

    try:
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
        new_user = await UserDoc(
            id=_zd.id,
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

    _ap = await ApplicationDoc.find_one({"user_id": _user.id})
    if _ap:
        raise HTTPException(
            status_code=400,
            detail="Application already exists, visit cabinet to check status",
        )

    now = datetime.now()
    application = await ApplicationDoc(
        user_id=_user.id,
        created_at=now,
        modified_at=now,
    ).insert()

    return {
        "reference": f"REF_{str(application.id)}",
    }
