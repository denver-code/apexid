from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document
from pydantic import Field


class ApplicationStatus(Enum):
    AWAITING_OPERATOR = "awaiting_operator"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class ApplicationDoc(Document):
    operator_id: Optional[str] = ""
    user_id: str
    status: ApplicationStatus = Field(default=ApplicationStatus.AWAITING_OPERATOR)
    created_at: datetime
    modified_at: datetime

    class Settings:
        name = "applications"

        unique_together = [("_id", "user_id")]
