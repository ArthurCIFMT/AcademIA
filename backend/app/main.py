from fastapi import FastAPI

from app.core.config import Settings
from app.core.health import router as health_router


def create_app() -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.include_router(health_router)
    return app
