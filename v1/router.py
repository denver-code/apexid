from fastapi import APIRouter, Depends
from app.core.fastjwt import FastJWT
from v1.private import private_router
from v1.public import public_router

router = APIRouter(prefix="/v1")

router.include_router(private_router, dependencies=[Depends(FastJWT().login_required)])
router.include_router(public_router)
