from beanie import init_beanie
from fastapi import Depends, FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware


from app.core.config import settings
from app.core.database import db
from v1.models.application import ApplicationDoc
from v1.models.authorized_device import AuthorizedDevice
from v1.models.notification import Notification
from v1.models.user import UserDoc, StaffMembership
from v1.models.document import ApexDocument, ConfrimationToken, ServiceDocument
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
            AuthorizedDevice,
            StaffMembership,
            Notification,
            ApexDocument,
            ServiceDocument,
            ConfrimationToken,
        ],
    )


@app.get("/")
def root():
    return {
        "message": "Hello World",
        "latest_version": "v1",
    }


api_router = APIRouter(prefix="/api")

api_router.include_router(v1_router)

app.include_router(api_router)
