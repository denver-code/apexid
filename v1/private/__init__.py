from fastapi import APIRouter, Depends
from v1.private.profile import profile_router
from v1.private.application import application_router
from v1.private.staff import staff_router


private_router = APIRouter(prefix="/private")


private_router.include_router(profile_router)
private_router.include_router(application_router)
private_router.include_router(staff_router)
