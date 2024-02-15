from typing import Optional
from pydantic import BaseModel


class NewServiceDocument(BaseModel):
    name: str
    description: str
    required_fields: list[str]
    metadata: Optional[dict] = {}
