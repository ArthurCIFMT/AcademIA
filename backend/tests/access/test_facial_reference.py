import os
from base64 import b64encode
from datetime import UTC, date, datetime, timedelta
from io import BytesIO
from pathlib import Path
from uuid import UUID, uuid4

import httpx
import pytest
from PIL import Image
from sqlalchemy import Connection, select, text

from app.contracts.time import academy_date
from app.database.connection import create_session_factory
from app.main import create_app
from app.modules.access.biometrics.images import clean_face_image
from app.modules.access.biometrics.models import FacialReference
from app.modules.access.biometrics.provider import (
    CompreFace,
    CompreFaceSettings,
    FaceCandidate,
    FacialProvider,
    FacialProviderError,
    RejectedFace,
)
from app.modules.access.biometrics.service import active_client_for_subject
from app.modules.audit.models import AuditRecord
from app.modules.identity.accounts import create_account
from app.modules.identity.models import AccountState, Role, UserRole
from app.modules.identity.passwords import Passwords
from app.modules.identity.settings import AuthSettings
from app.modules.memberships.schemas import CreateMembership, CreatePlan
from app.modules.memberships.service import create_plan, enroll
from app.modules.people.profiles import ClientProfile, EmployeeProfile

_ROOT = Path(__file__).resolve().parents[3]
_ORIGIN = "https://academia.example.test"
_PASSWORD = "segredo-sintetico-acs01"
_NOW = datetime.now(UTC)


def _jpeg(image: Image.Image) -> str:
    out = BytesIO()
    image.save(out, "JPEG")
    return b64encode(out.getvalue()).decode("ascii")


def _solid() -> str:
    with Image.new("RGB", (200, 200), "navy") as image:
        return _jpeg(image)


def test_image_removes_metadata_and_rejects_unreadable_data() -> None:
    with Image.new("RGB", (240, 320), "navy") as source:
        data = BytesIO()
        exif = source.getexif()
        exif[271] = "camera fictícia"
        source.save(data, "JPEG", exif=exif)
    clean = clean_face_image(
        b64encode(data.getvalue()).decode("ascii"), max_bytes=100_000
    )
    with Image.open(BytesIO(clean)) as photo:
        assert photo.size == (240, 320)
        assert not photo.getexif()
    with pytest.raises(ValueError):
        clean_face_image("dGVzdA==", max_bytes=100_000)


@pytest.mark.parametrize("scores", [[], [0.99, 0.90], [0.79]])
def test_detection_rejects_invalid_number_or_confidence(scores: list[float]) -> None:
    def respond(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/detection/detect"
        assert request.headers["x-api-key"] == "chave-deteccao"
        assert entry(request, "limit") == "0"
        assert entry(request, "det_prob_threshold") == "0.8"
        return httpx.Response(
            200, json={"result": [{"box": {"probability": score}} for score in scores]}
        )

    with pytest.raises(RejectedFace):
        _provider(httpx.MockTransport(respond)).validate_photo(b"imagem de teste")


def entry(request: httpx.Request, name: str) -> str:
    return request.url.params[name]


def _provider(transport: httpx.MockTransport) -> CompreFace:
    return CompreFace(
        CompreFaceSettings.model_validate(
            {
                "url": "http://127.0.0.1:18080",
                "detection_key": "chave-deteccao",
                "recognition_key": "chave-reconhecimento",
            }
        ),
        transport=transport,
    )


def test_provider_uses_recognition_key_and_confirms_already_removed_example() -> None:
    image_id = uuid4()
    requests = []

    def respond(request: httpx.Request) -> httpx.Response:
        assert request.headers["x-api-key"] == "chave-reconhecimento"
        requests.append(request.method)
        if request.method == "POST":
            assert entry(request, "subject") == "subject"
            return httpx.Response(
                201, json={"subject": "subject", "image_id": str(image_id)}
            )
        if request.method == "DELETE":
            assert request.url.path.endswith(str(image_id))
            return httpx.Response(404)
        return httpx.Response(200, json={"faces": [], "total_elements": 0})

    provider = _provider(httpx.MockTransport(respond))
    assert provider.add_example("subject", b"jpeg") == image_id
    provider.delete_example("subject", image_id)
    assert requests == ["POST", "DELETE", "GET"]


def test_openapi_describes_protected_json_upload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Testes")
    spec = create_app().openapi()
    path = "/api/v1/atendimento/clientes/{client_id}/biometria"
    assert set(spec["paths"][path]) == {"get", "post"}
    assert "application/json" in spec["paths"][path]["post"]["requestBody"]["content"]
    assert "503" in spec["paths"][path]["post"]["responses"]
    assert set(spec["components"]["schemas"]["ReferenceStatus"]["properties"]) == {
        "cadastrada",
        "elegivel",
        "disponivel",
        "atualizada_em",
        "pendencia",
    }


class ProviderDouble:
    max_image_bytes = 4 * 1024 * 1024

    def __init__(self) -> None:
        self.examples: dict[str, UUID] = {}
        self.fail_delete = False
        self.fail_after_create = False
        self.reject = False

    def validate_photo(self, image: bytes) -> None:
        if self.reject:
            raise RejectedFace

    def recognize(self, image: bytes) -> list[FaceCandidate]:
        self.validate_photo(image)
        return []

    def add_example(self, subject: str, image: bytes) -> UUID:
        self.examples[subject] = uuid4()
        if self.fail_after_create:
            raise FacialProviderError
        return self.examples[subject]

    def list_examples(self, subject: str) -> list[UUID]:
        return [self.examples[subject]] if subject in self.examples else []

    def delete_example(self, subject: str, image_id: UUID) -> None:
        if self.fail_delete:
            raise FacialProviderError
        if self.examples.get(subject) == image_id:
            del self.examples[subject]


def _sample(
    box: tuple[float, float, float, float], filename: str = "accessories_id1.jpg"
) -> str:
    location = (
        _ROOT / "backend/data/compreface-v1.2.0/amostras-sinteticas" / Path(filename)
    )
    with Image.open(location) as panel:
        x, y = panel.size
        with panel.crop(
            (int(box[0] * x), int(box[1] * y), int(box[2] * x), int(box[3] * y))
        ) as crop:
            return _jpeg(crop)


async def _login(api: httpx.AsyncClient, role: Role) -> dict[str, str]:
    api.cookies.clear()
    response = await api.post(
        "/api/v1/auth/login",
        json={
            "email": "acs01-" + role.value.lower() + "@example.test",
            "senha": _PASSWORD,
        },
    )
    assert response.status_code == 200
    return {"X-CSRF-Token": response.json()["csrf_token"]}


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.parametrize("mode", ["double", "real"])
async def test_register_replace_and_preserve_consistency(
    mode: str,
    migration: Connection,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider: FacialProvider
    double = None
    if mode == "real":
        if os.getenv("ACADEMIA_TEST_COMPREFACE") != "1":
            pytest.skip("Ensaio real do CompreFace é uma execução explícita.")
        provider = CompreFace(CompreFaceSettings())
        reference = _sample((0.253, 0.002, 0.493, 0.487))
        replacement = _sample((0.505, 0.002, 0.745, 0.487))
        multiple = _sample((0.504, 0.002, 0.998, 0.487))
    else:
        double = ProviderDouble()
        provider = double
        reference = replacement = multiple = _solid()

    monkeypatch.setenv("ACADEMIA_APP_NAME", "AcademIA Testes")
    sessions = create_session_factory(migration)
    password = Passwords().hash(_PASSWORD)
    people: dict[Role, UUID] = {}
    with sessions.begin() as db:
        for role in (Role.CLIENTE, Role.ATENDENTE, Role.ADMINISTRADOR):
            user = create_account(
                db,
                "acs01-" + role.value.lower() + "@example.test",
                state=AccountState.ATIVO,
                password_hash=password,
                now=_NOW,
            )
            people[role] = user
            db.add(UserRole(id=uuid4(), usuario_id=user, papel=role))
            if role == Role.CLIENTE:
                db.add(
                    ClientProfile(
                        usuario_id=user,
                        nome="Aluno de teste",
                        data_nascimento=date(1999, 4, 1),
                        ativo=True,
                    )
                )
            else:
                db.add(
                    EmployeeProfile(
                        usuario_id=user,
                        nome="Funcionário de teste",
                        cargo=role.value,
                        data_admissao=date(2026, 1, 1),
                        ativo=True,
                    )
                )

    client = people[Role.CLIENTE]
    path = f"/api/v1/atendimento/clientes/{client}/biometria"
    app = create_app(
        identity_sessions=sessions,
        auth_settings=AuthSettings(origin=_ORIGIN),
        biometrics_provider=provider,
    )

    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url=_ORIGIN,
        headers={"Origin": _ORIGIN},
    ) as api:
        try:
            assert (await api.get(path)).status_code == 401
            for role in (Role.CLIENTE, Role.ADMINISTRADOR):
                headers = await _login(api, role)
                assert (await api.get(path)).status_code == 403
                response = await api.post(
                    path, json={"imagem_base64": reference}, headers=headers
                )
                assert response.status_code == 403
            attendant = await _login(api, Role.ATENDENTE)
            assert (await api.get(path)).json()["elegivel"] is False
            assert (
                await api.post(path, json={"imagem_base64": reference})
            ).status_code == 403
            response = await api.post(
                path, json={"imagem_base64": reference}, headers=attendant
            )
            assert response.status_code == 409

            with sessions.begin() as db:
                plan_id = uuid4()
                create_plan(
                    db,
                    CreatePlan(
                        solicitacao_id=plan_id,
                        nome="Plano teste",
                        modalidade="Musculação",
                        duracao_dias=30,
                        ativo=True,
                    ),
                    actor_id=people[Role.ADMINISTRADOR],
                    correlation=uuid4(),
                )
                enroll(
                    db,
                    client,
                    CreateMembership(
                        solicitacao_id=uuid4(),
                        plano_id=plan_id,
                        plano_revisao=1,
                        inicio=academy_date(_NOW) + timedelta(days=1),
                    ),
                    attendant_id=people[Role.ATENDENTE],
                    correlation=uuid4(),
                    now=_NOW,
                )

            if double:
                double.reject = True
            for invalid in (multiple, _solid()):
                response = await api.post(
                    path, json={"imagem_base64": invalid}, headers=attendant
                )
                assert response.status_code == 422, response.text
            if double:
                double.reject = False
            assert (await api.get(path)).json()["cadastrada"] is False

            added = await api.post(
                path, json={"imagem_base64": reference}, headers=attendant
            )
            assert added.status_code == 200, added.text
            assert added.json()["cadastrada"] and not added.json()["pendencia"]
            assert added.headers["cache-control"] == "no-store"
            assert (await api.get("/api/v1/meu-perfil/foto")).status_code == 404
            await _login(api, Role.CLIENTE)
            photo = await api.get("/api/v1/meu-perfil/foto")
            assert photo.status_code == 200
            assert photo.headers["content-type"] == "image/jpeg"
            assert photo.headers["cache-control"] == "no-store"
            assert photo.content.startswith(b"\xff\xd8")
            assert (await api.get("/api/v1/meu-perfil")).json()["foto_disponivel"]
            attendant = await _login(api, Role.ATENDENTE)
            old = migration.execute(
                select(FacialReference.subject_externo, FacialReference.image_id)
            ).one()
            assert provider.list_examples(old.subject_externo) == [UUID(old.image_id)]

            if double:
                double.fail_after_create = True
                response = await api.post(
                    path, json={"imagem_base64": replacement}, headers=attendant
                )
                assert response.status_code == 503
                summary = (await api.get(path)).json()
                assert summary["cadastrada"] and summary["pendencia"] == "ENVIO"
                double.fail_after_create = False
                double.fail_delete = True
                response = await api.post(path + "/pendencia", headers=attendant)
                assert response.status_code == 503
                summary = (await api.get(path)).json()
                assert summary["cadastrada"] and summary["pendencia"] == "TROCA"
                with sessions.begin() as db:
                    pending = db.scalars(
                        select(FacialReference).where(
                            FacialReference.estado == "PRONTA"
                        )
                    ).one()
                    assert (
                        active_client_for_subject(db, pending.subject_externo) is None
                    )
                    assert active_client_for_subject(db, old.subject_externo) == client
                double.fail_delete = False
                replaced = await api.post(path + "/pendencia", headers=attendant)
            else:
                replaced = await api.post(
                    path, json={"imagem_base64": replacement}, headers=attendant
                )
            assert replaced.status_code == 200, replaced.text
            assert (
                replaced.json()["cadastrada"] and replaced.json()["pendencia"] is None
            )
            assert provider.list_examples(old.subject_externo) == []
            await _login(api, Role.CLIENTE)
            updated_photo = await api.get("/api/v1/meu-perfil/foto")
            if double:
                assert updated_photo.status_code == 404
            else:
                assert updated_photo.status_code == 200
                assert updated_photo.content != photo.content
            with sessions.begin() as db:
                current = db.scalars(select(FacialReference)).one()
                assert current.subject_externo != old.subject_externo
                assert current.cadastrada_por == people[Role.ATENDENTE]
                assert active_client_for_subject(db, current.subject_externo) == client
                assert active_client_for_subject(db, old.subject_externo) is None
                events = set(
                    db.scalars(
                        select(AuditRecord.acao).where(
                            AuditRecord.recurso_tipo == "biometria"
                        )
                    )
                )
                assert {"biometria.cadastrada", "biometria.substituida"} <= events
                if double:
                    assert "biometria.falha_externa" in events

            await _login(api, Role.ADMINISTRADOR)
            notices = (await api.get("/api/v1/notificacoes/pendentes")).json()
            assert sum(item["tipo"] == "ALTERACAO_CRITICA" for item in notices) == 2
        finally:
            rows = migration.execute(
                text("SELECT subject_externo FROM academia.biometria")
            ).scalars()
            for subject in rows.all():
                for image_id in provider.list_examples(subject):
                    provider.delete_example(subject, image_id)
                assert provider.list_examples(subject) == []
