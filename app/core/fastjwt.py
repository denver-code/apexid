from beanie import PydanticObjectId
import jwt
import datetime
from app.core.config import settings

from fastapi import HTTPException, Header
from v1.models.authorized_device import AuthorizedDevice
from v1.models.user import UserDoc


class FastJWT:
    def __init__(self):
        self.secret_key = settings.SECRET_KEY

    async def encode(self, optional_data=None, expire=None):
        if not expire:
            expire = (datetime.datetime.now() + datetime.timedelta(days=30)).timestamp()

        token_json = {"expire": expire}

        if optional_data:
            token_json.update(optional_data)
        jwt_token = jwt.encode(token_json, self.secret_key, algorithm="HS256")

        return jwt_token

    async def decode(self, payload):
        return jwt.decode(payload, self.secret_key, algorithms=["HS256"])

    async def login_required(self, Authorization=Header("Authorization")):
        try:
            if Authorization == "Authorization":
                raise

            jwt_token = await self.decode(Authorization)

            if not isinstance(jwt_token, dict):
                raise

            if jwt_token.get("expire") < int(datetime.datetime.now().timestamp()):
                raise

            user = await UserDoc.get(PydanticObjectId(jwt_token.get("id")))

            if not user:
                raise

            if not jwt_token.get("authorized_device_id"):
                raise

            authorized_device = await AuthorizedDevice.find_one(
                {
                    "_id": PydanticObjectId(jwt_token.get("authorized_device_id")),
                    "user_id": PydanticObjectId(jwt_token.get("id")),
                }
            )
            if not authorized_device:
                raise

        except Exception as e:
            raise HTTPException(status_code=401, detail="Unauthorized")
