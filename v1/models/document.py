from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class ApexDocument(Document):
    service_id: PydanticObjectId
    user_id: PydanticObjectId
    data: dict
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = {}

    class Settings:
        name = "apex_documents"


class ServiceDocument(Document):
    name: str
    description: str
    required_fields: list[str]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[dict] = {}

    class Settings:
        name = "service_documents"
