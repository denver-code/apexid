from typing import Optional
from pydantic import BaseModel


class BirthData(BaseModel):
    date: str
    place: str


class UserDetails(BaseModel):
    phone_number: str
    nationality: str
    born: BirthData
    metadata: Optional[dict] = {}


class GeneralUserID(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    gender: str
    born: BirthData
    phone_number: str
    nationality: str
    metadata: dict = {}


class AuthorizarionSchema(BaseModel):
    email: str
    password: str
    metadata: Optional[dict] = {}
