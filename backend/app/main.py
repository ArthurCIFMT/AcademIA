from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.health import router as health_router
from app.core.http import error_schemas, install_http_contract
from app.modules.identity.composition import install_identity
from app.modules.identity.settings import AuthSettings
from app.modules.notifications.http import notification_router
from app.modules.people.clients_http import client_router
from app.modules.people.staff_http import staff_router


def create_app(
    *,
    identity_sessions: sessionmaker[Session] | None = None,
    auth_settings: AuthSettings | None = None,
) -> FastAPI:
    settings = Settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", responses=error_schemas())
    install_http_contract(app)
    app.include_router(health_router)
    get_sessions = install_identity(
        app, settings=auth_settings, sessions=identity_sessions
    )
    app.include_router(notification_router(get_sessions))
    app.include_router(staff_router(get_sessions))
    app.include_router(client_router(get_sessions))
    return app
