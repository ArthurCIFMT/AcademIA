import hashlib
import json
import os
from pathlib import Path
from uuid import UUID

from sqlalchemy.orm import Session

from app.modules.knowledge.schemas import MAX_BYTES, Decision, ImportResult, Metadata
from app.modules.knowledge.service import CorpusError, authorize, decide, register
from app.modules.knowledge.storage import CorpusStorage, InvalidFile
from app.policies.access import Actor


def import_initial(
    session: Session,
    actor: Actor,
    storage: CorpusStorage,
    correlation: UUID,
    materials: Path | None = None,
) -> ImportResult:
    authorize(actor)
    root = (
        materials
        or Path(
            os.environ.get(
                "ACADEMIA_RAG_MATERIALS_DIR",
                str(Path(__file__).resolve().parents[4] / "materiais" / "rag"),
            )
        )
    ).resolve()
    try:
        catalog = json.loads((root / "catalogo.json").read_text(encoding="utf-8-sig"))
        selection = json.loads(
            (root / "corpus-inicial.json").read_text(encoding="utf-8-sig")
        )
        selected = {item["id"]: item for item in selection["documentos"]}
        documents = catalog["documentos"]
        if len({item["id"] for item in documents}) != len(documents) or not set(
            selected
        ) <= {item["id"] for item in documents}:
            raise ValueError()
        prepared = []
        for item in documents:
            path = (root / item["arquivo"]).resolve()
            path.relative_to((root / "documentos").resolve())
            with path.open("rb") as stream:
                content = stream.read(MAX_BYTES + 1)
            if hashlib.sha256(content).hexdigest() != item["sha256"]:
                raise ValueError()
            if (
                item["id"] in selected
                and selected[item["id"]]["sha256"] != item["sha256"]
            ):
                raise ValueError()
            reference, digest = storage.store(content, "PDF")
            metadata = Metadata.model_validate(
                {
                    "titulo": item["titulo"],
                    "origem_url": item["url"],
                    "licenca": item["licenca"],
                    "idioma": item["idioma"],
                    "autores": item.get("autores", []),
                    "ano": item.get("ano"),
                    "paginas_declaradas": item.get("paginas_pdf"),
                    "finalidades": selected[item["id"]]["finalidades"]
                    if item["id"] in selected
                    else ["DUVIDAS"],
                    "limites": selected[item["id"]]["limites"]
                    if item["id"] in selected
                    else item["limites"],
                }
            )
            prepared.append((item["id"], metadata, len(content), reference, digest))
    except (OSError, ValueError, KeyError, TypeError, InvalidFile):
        raise CorpusError(409) from None
    states = {"APROVADO": 0, "PENDENTE": 0, "REVOGADO": 0}
    created = 0
    for catalog_id, metadata, size, reference, digest in prepared:
        version, duplicate = register(
            session,
            actor,
            catalog_id,
            "LITERATURA",
            metadata,
            "PDF",
            size,
            reference,
            digest,
            correlation,
        )
        created += not duplicate
        # Seleção técnica existente; replay nunca ressuscita uma revogação.
        if catalog_id in selected and version.estado == "PENDENTE":
            version = decide(
                session,
                actor,
                version.id,
                Decision(revisao=version.revisao, estado="APROVADO"),
                storage,
                correlation,
            )
        states[version.estado] += 1
    return ImportResult(
        documentos=len(prepared),
        versoes_novas=created,
        aprovadas=states["APROVADO"],
        pendentes=states["PENDENTE"],
        revogadas=states["REVOGADO"],
    )
