from pydantic import BaseModel, validator
from app.core.email_fixer import EmailFixer
import re

from v1.schemas.user import UserDetails


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
        v = EmailFixer().fix(v)
        return v

    @validator("gender")
    def check_gender(cls, v):
        if v not in ["male", "female"]:
            raise ValueError("Invalid gender")

        return v


class Application(BaseModel):
    payload: UserDetails
