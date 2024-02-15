from fastapi import APIRouter, Depends
from v1.public.authorization import authorization_router

public_router = APIRouter(prefix="/public")

public_router.include_router(authorization_router)
