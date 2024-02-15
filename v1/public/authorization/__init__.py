from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request
from app.core.fastjwt import FastJWT
from v1.models.authorized_device import AuthorizedDevice
from v1.schemas.user import GeneralUserID, AuthorizarionSchema
from v1.models.user import UserDoc
from app.core.password import hash_password
from v1.models.notification import Notification


authorization_router = APIRouter(prefix="/authorization")


@authorization_router.post("/signup")
async def signup_event(payload: GeneralUserID, request: Request):
    _user = await UserDoc.find_one({"email": payload.email})
    if _user:
        raise HTTPException(status_code=400, detail="User already exists")

    # Encrypt the password
    payload.password = hash_password(payload.password)

    user = UserDoc(
        **payload.model_dump(),
    )

    await user.save()

    notification = Notification(
        user_id=user.id,
        message="Welcome to the platform",
        created_at=datetime.now(),
    )

    await notification.insert()

    return {
        "message": "User created successfully",
    }


@authorization_router.post("/signin")
async def signin_event(payload: AuthorizarionSchema):
    payload.password = hash_password(payload.password)

    user = await UserDoc.find_one(
        {"email": payload.email, "password": payload.password}
    )

    if not user:
        raise HTTPException(
            status_code=400, detail="User not found or password is incorrect"
        )

    authorized_device = await AuthorizedDevice(
        user_id=user.id,
        metadata=payload.metadata,
        created_at=datetime.now(),
    ).save()

    jwt_token = await FastJWT().encode(
        optional_data={
            "id": str(user.id),
            "email": user.email,
            "authorized_device_id": str(authorized_device.id),
        }
    )

    await Notification(
        user_id=user.id,
        message=f"New device signed in to your account, DeviceID: {str(authorized_device.id)}",
        created_at=datetime.now(),
    ).insert()

    return {
        "message": "User signed in successfully",
        "token": jwt_token,
    }
