import os
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, date, datetime
from threading import Event
from uuid import UUID, uuid4

import httpx
import pytest
from sqlalchemy import Connection, func, select
from sqlalchemy.schema import CreateSchema, DropSchema

from app.database.base import Base
from app.database.connection import (
    check_database,
    create_database_engine,
    create_session_factory,
)
from app.main import create_app
from app.modules.access.biometrics.images import clean_face_image
from app.modules.access.biometrics.models import FacialReference
from app.modules.access.biometrics.provider import (
    CompreFace,
    CompreFaceSettings,
    FaceCandidate,
    FacialProvider,
    FacialProviderError,
)
from app.modules.access.events.contracts import AccessEventsSettings
from app.modules.access.events.models import AccessEvent
from app.modules.access.events.service import (
    EventRequest,
    Identification,
    classify,
    receive,
)
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.settings import AuthSettings
from app.modules.people.profiles import ClientProfile, EmployeeProfile
from tests.access.test_facial_reference import (
    ProviderDouble,
    _provider,
    _sample,
    _solid,
)

_CAPTURE = "/api/v1/atendimento/reconhecimento"
_EXTERNAL = "/api/v1/acesso/identificacoes"
_TOKEN = "synthetic_token_acs02_not_for_development"
_ORIGIN = "https://academia.example.test"
_PASSWORD = "senha-sintetica-reconhecimento"
_NOW = datetime(2026, 11, 24, 12, tzinfo=UTC)


def test_uses_two_predictions_and_keeps_similarity_separate() -> None:
    paths = []

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        face: dict[str, object] = {"box": {"probability": 0.99}}
        if request.url.path.endswith("/recognize"):
            assert request.headers["x-api-key"] == "chave-reconhecimento"
            assert request.url.params["prediction_count"] == "2"
            assert request.url.params["limit"] == "0"
            face["subjects"] = [{"subject": "key", "similarity": 0.94}]
        return httpx.Response(200, json={"result": [face]})

    result = _provider(httpx.MockTransport(handler)).recognize(b"imagem")
    assert paths == ["/api/v1/detection/detect", "/api/v1/recognition/recognize"]
    assert classify(result, 0.95, lambda _: uuid4()).status == "PONTUACAO_BAIXA"


@pytest.mark.parametrize(
    ("candidates", "expected"),
    [
        ([], "DESCONHECIDO"),
        ([("valid", 0.94999)], "PONTUACAO_BAIXA"),
        ([("old", 0.99)], "DESCONHECIDO"),
        ([("valid", 0.95)], "IDENTIFICADO"),
        ([("valid", 0.98), ("old", 0.96)], "AMBIGUO"),
        ([("valid", 0.98), ("other", 0.94)], "IDENTIFICADO"),
    ],
)
def test_classification_is_conservative(
    candidates: list[tuple[str, float]], expected: str
) -> None:
    client_id = uuid4()
    result = classify(
        [
            FaceCandidate(subject=subject, similarity=score)
            for subject, score in candidates
        ],
        0.95,
        {"valid": client_id}.get,
    )
    assert result.status == expected
    assert result.client_id == (client_id if expected == "IDENTIFICADO" else None)


def test_openapi_requires_distinct_trusted_input(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Testes")
    spec = create_app().openapi()
    assert spec["paths"][_EXTERNAL]["post"]["security"] == [{"IdentificacaoFacial": []}]
    schemas = spec["components"]["schemas"]
    assert set(schemas["CaptureRequest"]["properties"]) == {
        "imagem_base64",
        "evento_id",
        "direcao",
    }
    assert "cliente_id" not in schemas["ExternalIdentification"]["properties"]
    assert {"201", "200", "409"} <= set(spec["paths"][_EXTERNAL]["post"]["responses"])


class RecognitionDouble(ProviderDouble):
    def __init__(self) -> None:
        super().__init__()
        self.candidates: list[FaceCandidate] = []
        self.unavailable = False
        self.calls = 0

    def recognize(self, image: bytes) -> list[FaceCandidate]:
        self.calls += 1
        if self.unavailable:
            raise FacialProviderError
        self.validate_photo(image)
        return self.candidates


def _require_empty_collection(settings: CompreFaceSettings) -> None:
    assert settings.url is not None and settings.recognition_key is not None
    with httpx.Client(timeout=settings.timeout_seconds, trust_env=False) as client:
        response = client.get(
            str(settings.url).rstrip("/") + "/api/v1/recognition/faces",
            headers={"x-api-key": settings.recognition_key.get_secret_value()},
        )
        assert response.is_success
        assert response.json()["total_elements"] == 0, (
            "Use uma coleção de ensaio vazia."
        )


async def _login(api: httpx.AsyncClient, role: Role) -> dict[str, str]:
    api.cookies.clear()
    response = await api.post(
        "/api/v1/auth/login",
        json={
            "email": f"acs02-{role.value.lower()}@example.test",
            "senha": _PASSWORD,
        },
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["double", "real"])
async def test_capture_and_authenticated_replay(
    mode: str,
    migration: Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider: FacialProvider
    double = None
    settings = None
    if mode == "real":
        if os.getenv("ACADEMIA_TEST_COMPREFACE") != "1":
            pytest.skip("Ensaio real do CompreFace é uma execução explícita.")
        settings = CompreFaceSettings()
        _require_empty_collection(settings)
        provider = CompreFace(settings)
        reference = _sample((0.253, 0.002, 0.493, 0.487))
        capture = _sample((0.758, 0.002, 0.998, 0.487))
        stranger = _sample((0.0, 0.0, 0.326, 1.0), "variety_id1.jpg")
    else:
        double = RecognitionDouble()
        provider = double
        reference = capture = stranger = _solid()

    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Testes")
    sessions = create_session_factory(migration)
    subject = str(uuid4())
    image_id = provider.add_example(
        subject, clean_face_image(reference, max_bytes=provider.max_image_bytes)
    )
    try:
        passwords = Passwords().hash(_PASSWORD)
        people = {}
        pending = str(uuid4())
        with sessions.begin() as db:
            for role in (Role.CLIENTE, Role.ATENDENTE):
                person = create_account(
                    db,
                    f"acs02-{role.value.lower()}@example.test",
                    state=AccountState.ATIVO,
                    password_hash=passwords,
                    now=_NOW,
                )
                people[role] = person
                db.add(UserRole(id=uuid4(), usuario_id=person, papel=role))
                if role == Role.CLIENTE:
                    db.add(
                        ClientProfile(
                            usuario_id=person,
                            nome="Cliente sintético",
                            data_nascimento=date(1999, 4, 1),
                            ativo=True,
                        )
                    )
                else:
                    db.add(
                        EmployeeProfile(
                            usuario_id=person,
                            nome="Atendente sintético",
                            cargo="Atendente",
                            data_admissao=date(2026, 1, 1),
                            ativo=True,
                        )
                    )
            db.flush()
            for state, reference_subject, external_image in (
                ("ATIVA", subject, image_id),
                ("PRONTA", pending, uuid4()),
            ):
                db.add(
                    FacialReference(
                        id=uuid4(),
                        cliente_id=people[Role.CLIENTE],
                        subject_externo=reference_subject,
                        image_id=str(external_image),
                        estado=state,
                        cadastrada_por=people[Role.ATENDENTE],
                        criada_em=_NOW,
                    )
                )

        if double:
            double.candidates = [FaceCandidate(subject=subject, similarity=0.97)]
        app = create_app(
            identity_sessions=sessions,
            auth_settings=AuthSettings(origin=_ORIGIN),
            biometrics_provider=provider,
            access_events_settings=AccessEventsSettings.model_validate(
                {"identification_token": _TOKEN}
            ),
        )
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app),
            base_url=_ORIGIN,
            headers={"Origin": _ORIGIN},
        ) as api:
            payload = {
                "evento_id": str(uuid4()),
                "direcao": "ENTRADA",
                "imagem_base64": capture,
            }
            assert (await api.post(_CAPTURE, json=payload)).status_code == 401
            client_session = await _login(api, Role.CLIENTE)
            assert (
                await api.post(_CAPTURE, json=payload, headers=client_session)
            ).status_code == 403
            attendant = await _login(api, Role.ATENDENTE)
            assert (await api.post(_CAPTURE, json=payload)).status_code == 403
            for extra in (
                {"similaridade": 1.0},
                {"cliente_id": str(people[Role.CLIENTE])},
            ):
                forged = await api.post(
                    _CAPTURE, json=payload | extra, headers=attendant
                )
                assert forged.status_code == 422
            response = await api.post(_CAPTURE, json=payload, headers=attendant)
            assert response.status_code == 201, response.text
            recognized = response.json()
            assert recognized["resultado"] == "IDENTIFICADO", recognized
            assert recognized["cliente_id"] == str(people[Role.CLIENTE])
            assert recognized["cliente_nome"] == "Cliente sintético"
            assert recognized["similaridade"] >= 0.95
            assert recognized["origem"] == "ACADEMIA"
            assert "subject" not in recognized and "autorizado" not in recognized
            repeated = await api.post(_CAPTURE, json=payload, headers=attendant)
            assert repeated.status_code == 200 and repeated.json() == recognized
            if double:
                assert double.calls == 1
            conflict = await api.post(
                _CAPTURE, json=payload | {"direcao": "SAIDA"}, headers=attendant
            )
            assert conflict.status_code == 409

            if double:
                double.candidates = [FaceCandidate(subject=subject, similarity=0.31)]
            distinct = await api.post(
                _CAPTURE,
                json=payload
                | {
                    "evento_id": str(uuid4()),
                    "imagem_base64": stranger,
                },
                headers=attendant,
            )
            assert (
                distinct.status_code == 201
                and distinct.json()["resultado"] == "PONTUACAO_BAIXA"
            )
            assert distinct.json()["cliente_id"] is None

            if double:
                double.reject = True
            invalid = await api.post(
                _CAPTURE,
                json=payload
                | {
                    "evento_id": str(uuid4()),
                    "imagem_base64": _solid(),
                },
                headers=attendant,
            )
            assert (
                invalid.status_code == 201
                and invalid.json()["resultado"] == "CAPTURA_INVALIDA"
            )
            if double:
                double.reject = False
                double.unavailable = True
                outage = await api.post(
                    _CAPTURE,
                    json=payload | {"evento_id": str(uuid4())},
                    headers=attendant,
                )
                assert outage.status_code == 201
                assert outage.json()["resultado"] == "FALHA_PROVEDOR"
                assert outage.json()["cliente_id"] is None

            auth = {"Authorization": "Bearer " + _TOKEN}
            external = {
                "schema_version": 1,
                "evento_id": payload["evento_id"],
                "ocorrido_em": "2026-11-24T12:00:00Z",
                "direcao": "SAIDA",
                "resultado": "CORRESPONDENCIA",
                "subject": subject,
                "similaridade": 0.95,
            }
            assert (await api.post(_EXTERNAL, json=external)).status_code == 401
            malformed = await api.post(
                _EXTERNAL,
                content="{",
                headers=auth | {"Content-Type": "application/json"},
            )
            assert malformed.status_code == 400
            for invalid_field in (
                {"similaridade": 1.1},
                {"ocorrido_em": 1795521600},
                {"subject": None},
                {"schema_version": 2},
                {"origem": "ACADEMIA"},
                {"cliente_id": str(people[Role.CLIENTE])},
            ):
                assert (
                    await api.post(
                        _EXTERNAL, json=external | invalid_field, headers=auth
                    )
                ).status_code == 422

            received = await api.post(_EXTERNAL, json=external, headers=auth)
            assert received.status_code == 201, received.text
            assert received.json()["origem"] == "INTEGRACAO_FACIAL"
            assert received.json()["resultado"] == "IDENTIFICADO"
            assert received.json()["id"] != recognized["id"]
            replay = await api.post(
                _EXTERNAL,
                json=external | {"ocorrido_em": "2026-11-24T09:00:00-03:00"},
                headers=auth,
            )
            assert replay.status_code == 200 and replay.json() == received.json()
            assert (
                await api.post(
                    _EXTERNAL, json=external | {"similaridade": 0.96}, headers=auth
                )
            ).status_code == 409
            pending_event = await api.post(
                _EXTERNAL,
                json=external | {"evento_id": str(uuid4()), "subject": pending},
                headers=auth,
            )
            assert (
                pending_event.status_code == 201
                and pending_event.json()["resultado"] == "DESCONHECIDO"
            )

        assert migration.scalar(select(func.count()).select_from(AccessEvent)) == (
            6 if double else 5
        )
    finally:
        provider.delete_example(subject, image_id)
        assert provider.list_examples(subject) == []
        if settings is not None:
            _require_empty_collection(settings)


@pytest.mark.integration
def test_concurrent_delivery_calls_identification_once() -> None:
    engine = create_database_engine("test")
    schema = "acs02_" + uuid4().hex
    with engine.begin() as conn:
        check_database(conn, "test")
        conn.execute(CreateSchema(schema))
    try:
        scoped = engine.execution_options(schema_translate_map={"academia": schema})
        with scoped.begin() as conn:
            Base.metadata.create_all(
                conn,
                tables=[
                    Base.metadata.tables[f"academia.{table}"]
                    for table in ("usuario", "cliente", "evento_acesso")
                ],
            )
        sessions = create_session_factory(scoped)
        request = EventRequest("ACADEMIA", uuid4(), "ENTRADA", _NOW, "a" * 64)
        started = Event()
        second_entered = Event()
        release = Event()
        calls = []

        def identify() -> Identification:
            calls.append(1)
            started.set()
            assert release.wait(10)
            return Identification("DESCONHECIDO")

        def deliver(is_second: bool = False) -> tuple[UUID, bool]:
            with sessions.begin() as db:
                if is_second:
                    second_entered.set()
                receipt, created = receive(db, request, identify)
                return receipt.id, created

        with ThreadPoolExecutor(max_workers=2) as pool:
            first = pool.submit(deliver)
            try:
                assert started.wait(10)
                second = pool.submit(deliver, True)
                assert second_entered.wait(10)
            finally:
                release.set()
            original, created = first.result(timeout=10)
            replay, duplicated = second.result(timeout=10)
        assert original == replay and created and not duplicated and calls == [1]
    finally:
        try:
            with engine.begin() as conn:
                conn.execute(DropSchema(schema, cascade=True))
        finally:
            engine.dispose()
