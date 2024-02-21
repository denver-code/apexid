from datetime import datetime, timedelta
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


class ConfrimationToken(Document):
    user_id: PydanticObjectId
    document_id: PydanticObjectId
    expire_at: datetime = Field(
        default_factory=lambda: datetime.now() + timedelta(minutes=3)
    )

    class Settings:
        name = "confirmation_tokens"
