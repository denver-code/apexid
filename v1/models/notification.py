from datetime import datetime
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class Notification(Document):
    user_id: PydanticObjectId
    message: str
    created_at: datetime
    created_by: Optional[str] = "system"
    metadata: Optional[dict] = {}

    class Settings:
        name = "notifications"
        unique_together = [("user_id", "_id")]
