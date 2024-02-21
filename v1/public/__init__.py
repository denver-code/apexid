from fastapi import APIRouter, Depends
from v1.public.authorization import authorization_router
from v1.public.document import document_router

public_router = APIRouter(prefix="/public")

public_router.include_router(authorization_router)
public_router.include_router(document_router)
