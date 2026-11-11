import hashlib
from collections.abc import Sequence
from typing import Annotated, Literal
from uuid import UUID, uuid5

from pydantic import Field, model_validator

from app.modules.knowledge.embeddings.encoder import Encoder
from app.modules.knowledge.ingestion.contracts import (
    ExtractionResult,
    State,
    StrictModel,
    digest,
)


class ChunkingError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


class Span(StrictModel):
    pagina: int | None
    inicio: Annotated[int, Field(ge=0)]
    fim: Annotated[int, Field(gt=0)]
    secao: str | None = None
    tipo: Literal["PARAGRAFO", "TABELA"] = "PARAGRAFO"


class Selection(StrictModel):
    schema_version: Literal[1] = 1
    finalidade: Literal["DUVIDAS", "GERACAO_GERAL", "TRIAGEM", "DUVIDAS_SAUDE_GERAL"]
    motivo_curadoria: Annotated[str, Field(min_length=1, max_length=1000)]
    trechos: Annotated[list[Span], Field(min_length=1, max_length=10000)]

    @model_validator(mode="after")
    def nonoverlapping(self) -> "Selection":
        occupied: dict[int | None, int] = {}
        for span in self.trechos:
            if span.fim <= span.inicio or span.inicio < occupied.get(span.pagina, 0):
                raise ValueError("Trechos sobrepostos ou fora de ordem.")
            occupied[span.pagina] = span.fim
        return self


class Chunk(StrictModel):
    id: UUID
    ordinal: int
    pagina: int | None
    linha_inicio: int | None
    linha_fim: int | None
    secao: str | None
    inicio: int
    fim: int
    texto: str
    texto_hash: str
    embedding_text: str
    tokens: int
    input_tokens: int


def make_chunks(
    extraction: ExtractionResult,
    selection: Selection,
    encoder: Encoder,
    ingestion_id: UUID,
) -> list[Chunk]:
    if extraction.resultado.estado != State.CONCLUIDA:
        raise ChunkingError("EXTRACAO_NAO_CONCLUIDA")
    if selection.finalidade not in extraction.metadados.finalidades:
        raise ChunkingError("FINALIDADE_NAO_APROVADA")
    pages = {p.numero: p for p in extraction.resultado.paginas}
    atoms: list[tuple[Span, str]] = []
    for span in selection.trechos:
        page = pages.get(span.pagina)
        if page is None or page.situacao != "TEXTO" or span.fim > len(page.texto):
            raise ChunkingError("TRECHO_FORA_DA_ORIGEM")
        text = page.texto[span.inicio : span.fim]
        if not text.strip():
            raise ChunkingError("TRECHO_VAZIO")
        if (
            span.inicio and page.texto[span.inicio - 1].isalnum() and text[0].isalnum()
        ) or (
            span.fim < len(page.texto)
            and text[-1].isalnum()
            and page.texto[span.fim].isalnum()
        ):
            raise ChunkingError("LIMITE_CORTA_PALAVRA")
        if encoder.tokens(text) > 300:
            raise ChunkingError(
                "TABELA_EXCEDE_LIMITE"
                if span.tipo == "TABELA"
                else "PARAGRAFO_EXCEDE_LIMITE"
            )
        atoms.append((span, text))
    groups: list[list[tuple[Span, str]]] = []
    current: list[tuple[Span, str]] = []
    for atom in atoms:
        candidate = current + [atom]
        same = not current or (
            current[-1][0].pagina == atom[0].pagina
            and current[-1][0].secao == atom[0].secao
            and not pages[atom[0].pagina]
            .texto[current[-1][0].fim : atom[0].inicio]
            .strip()
        )
        if current and (
            not same or encoder.tokens("\n\n".join(x[1] for x in candidate)) > 300
        ):
            groups.append(current)
            overlap: list[tuple[Span, str]] = []
            if same:
                for previous in reversed(current):
                    trial = [previous] + overlap
                    if encoder.tokens("\n\n".join(x[1] for x in trial + [atom])) > 300:
                        break
                    overlap = trial
                    if encoder.tokens("\n\n".join(x[1] for x in overlap)) >= 48:
                        break
            current = overlap
        current.append(atom)
    if current:
        groups.append(current)
    chunks = []
    for ordinal, group in enumerate(groups, 1):
        first, last = group[0][0], group[-1][0]
        text = "\n\n".join(x[1] for x in group)
        title = extraction.metadados.titulo + (
            " / " + first.secao if first.secao else ""
        )
        embedding_text = title + "\n" + text
        count = encoder.tokens("passage: " + embedding_text)
        if count > 512:
            raise ChunkingError("TITULO_E_CONTEXTO_EXCEDEM_LIMITE")
        page = pages[first.pagina]
        start_line = (
            page.texto.count("\n", 0, first.inicio) + 1
            if first.pagina is None
            else None
        )
        end_line = (
            page.texto.count("\n", 0, last.fim) + 1 if first.pagina is None else None
        )
        sha = hashlib.sha256(text.encode()).hexdigest()
        chunks.append(
            Chunk(
                id=uuid5(ingestion_id, f"{ordinal}:{sha}"),
                ordinal=ordinal,
                pagina=first.pagina,
                linha_inicio=start_line,
                linha_fim=end_line,
                secao=first.secao,
                inicio=first.inicio,
                fim=last.fim,
                texto=text,
                texto_hash=sha,
                embedding_text=embedding_text,
                tokens=encoder.tokens(text),
                input_tokens=count,
            )
        )
    return chunks


def plan_hash(chunks: Sequence[Chunk]) -> str:
    return digest([chunk.model_dump(mode="json") for chunk in chunks])
