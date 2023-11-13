from beanie import Document
from pydantic import BaseModel


class BirthData(BaseModel):
    date: str
    place: str


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
