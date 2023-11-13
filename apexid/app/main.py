from beanie import init_beanie
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.authorization import auth_required

from app.core.config import settings
from app.core.database import db
from v1.models.application import ApplicationDoc
from v1.models.user import UserDoc
from v1.router import router as v1_router


def get_application():
    _app = FastAPI(title=settings.PROJECT_NAME)

    _app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()


@app.on_event("startup")
async def on_startup():
    await init_beanie(
        database=db,
        document_models=[
            UserDoc,
            ApplicationDoc,
        ],
    )


@app.get("/")
def root():
    return {
        "message": "Hello World",
        "latest_version": "v1",
    }


@app.get("/protected")
def protected(user: dict = Depends(auth_required)):
    return {
        "message": "Hello in Protected World",
        "latest_version": "v1",
    }


app.include_router(v1_router)
