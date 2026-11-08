from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.health import router as health_router
from app.core.http import error_schemas, install_http_contract
from app.modules.identity.composition import install_identity
from app.modules.identity.settings import AuthSettings


def create_app(
    *,
    identity_sessions: sessionmaker[Session] | None = None,
    auth_settings: AuthSettings | None = None,
) -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", responses=error_schemas())
    install_http_contract(app)
    app.include_router(health_router)
    install_identity(app, settings=auth_settings, sessions=identity_sessions)
    return app
