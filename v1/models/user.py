from datetime import datetime
from beanie import Document, PydanticObjectId
from pydantic import BaseModel, Field
from enum import Enum

from v1.schemas.user import BirthData


class UserDoc(Document):
    email: str
    password: str
    first_name: str
    last_name: str
    gender: str
    born: BirthData
    phone_number: str
    nationality: str
    metadata: dict = {}

    class Settings:
        name = "users"


class StaffLevel(Enum):
    SUPER_ADMIN = 1000
    ADMIN = 666
    OPERATOR = 100
    STAFF = 75
    JUNIOR_OPERATOR = 50


class StaffMembership(Document):
    user_id: PydanticObjectId
    level: StaffLevel = Field(default=StaffLevel.JUNIOR_OPERATOR)
    promoted_by: PydanticObjectId
    created_at: datetime
    updated_at: datetime
