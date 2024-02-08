from beanie import Document
from pydantic import BaseModel

from v1.schemas.user import BirthData


class UserDoc(Document):
    id: str
    email: str
    first_name: str
    last_name: str
    gender: str
    born: BirthData
    phone_number: str
    nationality: str
    metadata: dict = {}

    class Settings:
        name = "users"
