import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from pydantic import ValidationError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.core.health import router as health_router
from app.core.http import error_schemas, install_http_contract
from app.modules.access.authorization.http import authorization_router
from app.modules.access.biometrics.http import biometrics_router
from app.modules.access.biometrics.provider import (
    CompreFace,
    CompreFaceSettings,
    FacialProvider,
)
from app.modules.access.events.contracts import AccessEventsSettings
from app.modules.access.events.http import identification_router
from app.modules.access.integrations.turnstile.contracts import AccessSettings
from app.modules.access.manual.http import manual_access_router
from app.modules.access.queries.http import access_queries_router
from app.modules.ai.chat.http import chat_router
from app.modules.ai.http import generation_router
from app.modules.ai.triage.http import triage_router
from app.modules.assignments.http import install_assignments
from app.modules.billing.payments.http import manual_payments_router
from app.modules.classes.http import classes_router
from app.modules.dashboard.http import dashboard_router
from app.modules.equipment.http import equipment_router
from app.modules.identity.composition import install_identity
from app.modules.identity.settings import AuthSettings
from app.modules.knowledge.embeddings.runtime import close_encoder
from app.modules.knowledge.http import corpus_router
from app.modules.knowledge.vector.runtime import close_vector_store
from app.modules.memberships.http import memberships_router
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
        try:
            close_vector_store()
        finally:
            close_encoder()


def create_app(
    *,
    identity_sessions: sessionmaker[Session] | None = None,
    auth_settings: AuthSettings | None = None,
    biometrics_provider: FacialProvider | None = None,
    access_events_settings: AccessEventsSettings | None = None,
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
    app.include_router(dashboard_router(get_sessions))
    app.include_router(client_router(get_sessions))
    app.include_router(onboarding_router(get_sessions))
    app.include_router(triage_router(get_sessions))
    app.include_router(generation_router(get_sessions))
    app.include_router(chat_router(get_sessions))
    app.include_router(equipment_router(get_sessions))
    app.include_router(classes_router(get_sessions))
    app.include_router(memberships_router(get_sessions))
    app.include_router(manual_payments_router(get_sessions))
    if biometrics_provider is None:
        try:
            face_settings = CompreFaceSettings()
        except ValidationError:
            logging.getLogger(__name__).warning("Configuração do CompreFace inválida.")
        else:
            if face_settings.url is not None:
                biometrics_provider = CompreFace(face_settings)
    app.include_router(biometrics_router(get_sessions, biometrics_provider))
    if access_events_settings is None:
        try:
            access_events_settings = AccessEventsSettings()
        except ValidationError:
            logging.getLogger(__name__).warning(
                "Configuração da identificação inválida."
            )
    app.include_router(
        identification_router(get_sessions, biometrics_provider, access_events_settings)
    )
    access_settings: AccessSettings | None = None
    try:
        access_settings = AccessSettings()
    except ValidationError:
        logging.getLogger(__name__).warning(
            "Configuração da autorização de acesso inválida."
        )
    app.include_router(authorization_router(get_sessions, access_settings))
    app.include_router(manual_access_router(get_sessions, access_settings))
    app.include_router(access_queries_router(get_sessions))
    app.include_router(exercise_router(get_sessions))
    app.include_router(workout_router(get_sessions))
    app.include_router(review_queue_router(get_sessions))
    install_assignments(app, get_sessions)
    return app
