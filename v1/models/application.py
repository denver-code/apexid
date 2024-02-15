from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class ApplicationStatus(Enum):
    AWAITING_OPERATOR = "awaiting_operator"
    PENDING = "pending"
    AWAITING_DATA = "awaiting_data"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApplicationDoc(Document):
    operator_id: Optional[PydanticObjectId] = None
    user_id: PydanticObjectId
    service_document_id: PydanticObjectId
    data: dict = {}
    status: ApplicationStatus = Field(default=ApplicationStatus.AWAITING_OPERATOR)
    created_at: datetime
    modified_at: datetime

    class Settings:
        name = "applications"

        unique_together = [("_id", "user_id")]
