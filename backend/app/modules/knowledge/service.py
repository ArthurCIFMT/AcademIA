from dataclasses import dataclass
from uuid import UUID, uuid4, uuid5

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.events.contracts import AuditEvent
from app.modules.audit.service import record_audit
from app.modules.identity.service import utc_now
from app.modules.knowledge.models import Document, DocumentVersion
from app.modules.knowledge.schemas import Decision, Metadata, Page, VersionView
from app.modules.knowledge.storage import CorpusStorage, InvalidFile
from app.policies.access import Actor, Operation, allows


class CorpusError(Exception):
    def __init__(self, status: int) -> None:
        self.status = status


def authorize(actor: Actor) -> None:
    if not allows(actor, Operation.MANAGE_CORPUS):
        raise CorpusError(403)


def view(session: Session, row: DocumentVersion) -> VersionView:
    document = session.get(Document, row.documento_id)
    assert document
    return VersionView(
        id=row.id,
        documento_id=row.documento_id,
        catalogo_id=document.catalogo_id,
        ambiente=row.ambiente,
        numero=row.numero,
        sha256=row.sha256,
        formato=row.formato,
        tamanho_bytes=row.tamanho_bytes,
        metadados=Metadata.model_validate(row.metadados),
        estado=row.estado,
        criado_por=row.criado_por,
        criado_em=row.criado_em,
        aprovado_por=row.aprovado_por,
        aprovado_em=row.aprovado_em,
        revogado_por=row.revogado_por,
        revogado_em=row.revogado_em,
        motivo_revogacao=row.motivo_revogacao,
        revisao=row.revision,
    )


def row_by_id(
    session: Session, version_id: UUID, *, lock: bool = False
) -> DocumentVersion:
    query = (
        select(DocumentVersion)
        .where(DocumentVersion.id == version_id)
        .execution_options(populate_existing=True)
    )
    if lock:
        query = query.with_for_update()
    row = session.scalar(query)
    if row is None:
        raise CorpusError(404)
    return row


def _audit(
    session: Session, actor: Actor, row: DocumentVersion, action: str, correlation: UUID
) -> None:
    record_audit(
        session,
        AuditEvent(
            id=uuid5(row.id, f"{action}:{row.revision}"),
            actor_id=actor.user_id,
            action=action,
            resource_type="documento_versao",
            resource_id=row.id,
            correlation_id=correlation,
            occurred_at=utc_now(),
        ),
    )


def register(
    session: Session,
    actor: Actor,
    catalog_id: str,
    scope: str,
    metadata: Metadata,
    format: str,
    size: int,
    reference: str,
    digest: str,
    correlation: UUID,
) -> tuple[VersionView, bool]:
    authorize(actor)
    # Serializa duplicatas, inclusive em conexões independentes.
    key = int.from_bytes(bytes.fromhex(digest[:16]), "big", signed=True)
    session.execute(text("SELECT pg_advisory_xact_lock(:key)"), {"key": key})
    existing = session.scalar(
        select(DocumentVersion).where(
            DocumentVersion.sha256 == digest, DocumentVersion.ambiente == scope
        )
    )
    if existing is not None:
        return view(session, existing), True
    session.execute(
        insert(Document)
        .values(
            id=uuid4(),
            ambiente=scope,
            catalogo_id=catalog_id,
            titulo=metadata.titulo,
            origem_url=str(metadata.origem_url),
            licenca=metadata.licenca,
        )
        .on_conflict_do_nothing(constraint="uq_documento_catalogo")
    )
    doc = session.scalar(
        select(Document)
        .where(Document.ambiente == scope, Document.catalogo_id == catalog_id)
        .with_for_update()
    )
    assert doc
    number = (
        session.scalar(
            select(func.max(DocumentVersion.numero)).where(
                DocumentVersion.documento_id == doc.id
            )
        )
        or 0
    )
    row = DocumentVersion(
        id=uuid4(),
        documento_id=doc.id,
        ambiente=scope,
        numero=number + 1,
        sha256=digest,
        idioma=metadata.idioma,
        arquivo_ref=reference,
        formato=format,
        tamanho_bytes=size,
        metadados=metadata.model_dump(mode="json"),
        criado_por=actor.user_id,
        criado_em=utc_now(),
        estado="PENDENTE",
        revision=1,
    )
    session.add(row)
    session.flush()
    _audit(session, actor, row, "corpus.registered", correlation)
    return view(session, row), False


def decide(
    session: Session,
    actor: Actor,
    version_id: UUID,
    data: Decision,
    storage: CorpusStorage,
    correlation: UUID,
) -> VersionView:
    authorize(actor)
    row = row_by_id(session, version_id, lock=True)
    if row.estado == data.estado and row.revision == data.revisao + 1:
        owner = row.aprovado_por if data.estado == "APROVADO" else row.revogado_por
        if owner == actor.user_id and (
            data.estado != "REVOGADO" or row.motivo_revogacao == data.motivo
        ):
            return view(session, row)
    if row.revision != data.revisao:
        raise CorpusError(409)
    allowed = (row.estado, data.estado) in {
        ("PENDENTE", "APROVADO"),
        ("APROVADO", "REVOGADO"),
    }
    if not allowed:
        raise CorpusError(409)
    if data.estado == "APROVADO":
        try:
            storage.read(row.arquivo_ref, row.sha256)
        except InvalidFile:
            raise CorpusError(409) from None
        row.aprovado_por = actor.user_id
        row.aprovado_em = utc_now()
    else:
        row.revogado_por = actor.user_id
        row.revogado_em = utc_now()
        row.motivo_revogacao = data.motivo
    row.estado = data.estado
    row.revision += 1
    session.flush()
    _audit(
        session,
        actor,
        row,
        "corpus.approved" if data.estado == "APROVADO" else "corpus.revoked",
        correlation,
    )
    return view(session, row)


def history(
    session: Session, actor: Actor, page: int, limit: int, scope: str | None
) -> Page:
    authorize(actor)
    query = select(DocumentVersion)
    if scope:
        query = query.where(DocumentVersion.ambiente == scope)
    total = session.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = session.scalars(
        query.order_by(DocumentVersion.criado_em.desc(), DocumentVersion.id)
        .offset((page - 1) * limit)
        .limit(limit)
    )
    return Page(
        itens=[view(session, row) for row in rows],
        pagina=page,
        limite=limit,
        total=total,
    )


@dataclass(frozen=True)
class ApprovedReference:
    version_id: UUID
    revision: int
    sha256: str
    reference: str
    format: str
    metadata: Metadata


def approved_references(session: Session) -> list[ApprovedReference]:
    """Autorização documental; extração/indexação ainda são pré-condições futuras."""
    rows = session.scalars(
        select(DocumentVersion)
        .where(
            DocumentVersion.ambiente == "LITERATURA",
            DocumentVersion.estado == "APROVADO",
        )
        .order_by(DocumentVersion.id)
        .execution_options(populate_existing=True)
    )
    return [
        ApprovedReference(
            row.id,
            row.revision,
            row.sha256,
            row.arquivo_ref,
            row.formato,
            Metadata.model_validate(row.metadados),
        )
        for row in rows
    ]


def is_approved(session: Session, version_id: UUID, revision: int) -> bool:
    """Revalidar em cada novo uso/cache, mesmo que o vetor ainda exista."""
    return (
        session.scalar(
            select(DocumentVersion.id).where(
                DocumentVersion.id == version_id,
                DocumentVersion.revision == revision,
                DocumentVersion.ambiente == "LITERATURA",
                DocumentVersion.estado == "APROVADO",
            )
        )
        is not None
    )
