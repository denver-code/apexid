from datetime import datetime
from enum import Enum
from typing import Optional
from beanie import Document, PydanticObjectId
from pydantic import Field


class AuthorizedDevice(Document):
    user_id: PydanticObjectId
    created_at: datetime
    metadata: dict

    class Settings:
        name = "authorized_devices"
        unique_together = [("user_id", "_id")]
