from fastapi import APIRouter, Depends

from app.core.authorization import auth_required
from v1.private import private_router

router = APIRouter(prefix="/v1")

router.include_router(private_router, dependencies=[Depends(auth_required)])
