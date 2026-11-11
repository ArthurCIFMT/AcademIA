from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.health import router as health_router
from app.core.http import error_schemas, install_http_contract
from app.modules.assignments.http import install_assignments
from app.modules.equipment.http import equipment_router
from app.modules.identity.composition import install_identity
from app.modules.identity.settings import AuthSettings
from app.modules.knowledge.http import corpus_router
from app.modules.knowledge.vector.runtime import close_vector_store
from app.modules.notifications.http import notification_router
from app.modules.onboarding.http import onboarding_router
from app.modules.people.clients_http import client_router
from app.modules.people.staff_http import staff_router
from app.modules.training.http import exercise_router
from app.modules.training.review_http import review_queue_router
from app.modules.training.workout_http import workout_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        yield
    finally:
        close_vector_store()


def create_app(
    *,
    identity_sessions: sessionmaker[Session] | None = None,
    auth_settings: AuthSettings | None = None,
) -> FastAPI:
    settings = Settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        responses=error_schemas(),
        lifespan=lifespan,
    )
    install_http_contract(app)
    app.include_router(health_router)
    get_sessions = install_identity(
        app, settings=auth_settings, sessions=identity_sessions
    )
    app.include_router(notification_router(get_sessions))
    app.include_router(corpus_router(get_sessions))
    app.include_router(staff_router(get_sessions))
    app.include_router(client_router(get_sessions))
    app.include_router(onboarding_router(get_sessions))
    app.include_router(equipment_router(get_sessions))
    app.include_router(exercise_router(get_sessions))
    app.include_router(workout_router(get_sessions))
    app.include_router(review_queue_router(get_sessions))
    install_assignments(app, get_sessions)
    return app
