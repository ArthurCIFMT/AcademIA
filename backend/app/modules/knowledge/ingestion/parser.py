import hashlib
import logging
import re
from collections.abc import Sequence
from io import BytesIO

from pypdf import PdfReader, apply_configuration
from pypdf.errors import LimitReachedError, PdfReadError
from pypdf.generic import Destination

from app.modules.knowledge.ingestion.contracts import (
    ExtractionPolicy,
    Page,
    ParsedDocument,
    Reason,
    Section,
    State,
)
from app.modules.knowledge.schemas import MAX_BYTES


class WarningCounter(logging.Handler):
    def __init__(self) -> None:
        super().__init__(logging.WARNING)
        self.count = 0
        self.structural_count = 0

    def emit(self, record: logging.LogRecord) -> None:
        # Conteúdo bruto dos avisos nunca vira log técnico ou mensagem pública.
        self.count += 1
        if record.getMessage().casefold().startswith("xref table not zero-indexed."):
            self.structural_count += 1


def failed(reason: Reason) -> ParsedDocument:
    return ParsedDocument(estado=State.FALHA, motivos=[reason])


def page(number: int | None, text: str, status: str, sections: list[Section]) -> Page:
    return Page.model_validate(
        {
            "numero": number,
            "texto": text,
            "texto_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "situacao": status,
            "secoes": sections,
        }
    )


def illegible(text: str) -> bool:
    return any(c == "\ufffd" or (ord(c) < 32 and c not in "\n\r\t") for c in text)


def parse_txt(
    content: bytes, declared: str | None, policy: ExtractionPolicy
) -> ParsedDocument:
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return failed(Reason.TEXTO_INVALIDO)
    if not text.strip():
        return failed(Reason.SEM_CONTEUDO_TEXTUAL)
    if len(text) > policy.max_total_chars:
        return failed(Reason.LIMITE_EXCEDIDO)
    # Preservar o texto original, exceto o BOM de transporte UTF-8.
    sections = [Section(titulo=declared, origem="DECLARADA")] if declared else []
    lines = text.splitlines()
    for index, line in enumerate(lines, 1):
        match = re.match(r"^#{1,6} +(.+?) *$", line)
        if match:
            sections.append(
                Section(titulo=match[1], origem="CABECALHO_TXT", linha=index)
            )
    bad = illegible(text)
    entry = page(None, text, "REVISAO_NECESSARIA" if bad else "TEXTO", sections)
    entry = entry.model_copy(update={"linha_inicio": 1, "linha_fim": len(lines)})
    return ParsedDocument(
        estado=State.REVISAO_NECESSARIA if bad else State.CONCLUIDA,
        motivos=[Reason.CARACTERES_ILEGIVEIS] if bad else [],
        paginas=[entry],
    )


def parse_pdf(
    content: bytes, declared: str | None, policy: ExtractionPolicy
) -> ParsedDocument:
    counter = WarningCounter()
    logger = logging.getLogger("pypdf")
    old_handlers, old_level, old_propagate = (
        logger.handlers[:],
        logger.level,
        logger.propagate,
    )
    logger.handlers, logger.propagate = [counter], False
    logger.setLevel(logging.WARNING)
    try:
        with apply_configuration(
            maximum_declared_stream_length=policy.max_stream_bytes,
            zlib_maximum_output_length=policy.max_stream_bytes,
            lzw_maximum_output_length=policy.max_stream_bytes,
            run_length_maximum_output_length=policy.max_stream_bytes,
            stream_decoding_work_maximum_length=policy.max_stream_bytes * 4,
            outline_maximum_entries=10000,
            page_tree_maximum_page_entries=policy.max_pages * 100,
            page_tree_maximum_entries=policy.max_pages * 10,
        ):
            reader = PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted:
                return failed(Reason.PDF_PROTEGIDO)
            if not 1 <= len(reader.pages) <= policy.max_pages:
                return failed(Reason.LIMITE_EXCEDIDO)
            if policy.selected_pages and policy.selected_pages[-1] > len(reader.pages):
                return failed(Reason.LIMITE_EXCEDIDO)
            bookmarks: dict[int, list[Section]] = {}

            def walk(items: Sequence[object]) -> None:
                for item in items:
                    if isinstance(item, list):
                        walk(item)
                    elif isinstance(item, Destination):
                        destination = reader.get_destination_page_number(item)
                        if destination is not None:
                            bookmarks.setdefault(destination + 1, []).append(
                                Section(titulo=item.title, origem="MARCADOR_PDF")
                            )

            walk(reader.outline)
            pages, total = [], 0
            reasons: list[Reason] = []
            selected = set(policy.selected_pages) if policy.selected_pages else None
            for number, source in enumerate(reader.pages, 1):
                if selected is not None and number not in selected:
                    continue
                stream = source.get_contents()
                if (
                    stream is not None
                    and len(stream.get_data()) > policy.max_stream_bytes
                ):
                    return failed(Reason.LIMITE_EXCEDIDO)
                text = source.extract_text(
                    extraction_mode="layout", layout_mode_strip_rotated=False
                )
                if (
                    len(text) > policy.max_page_chars
                    or total + len(text) > policy.max_total_chars
                ):
                    return failed(Reason.LIMITE_EXCEDIDO)
                total += len(text)
                status = "TEXTO"
                if not text.strip():
                    if len(source.images):
                        status = "OCR_NECESSARIO"
                        reasons.append(Reason.PAGINA_SEM_CAMADA_TEXTUAL)
                    elif stream is None or not any(
                        op
                        in {
                            b"Do",
                            b"Tj",
                            b"TJ",
                            b"'",
                            b'"',
                            b"f",
                            b"F",
                            b"f*",
                            b"S",
                            b"s",
                            b"B",
                            b"B*",
                            b"b",
                            b"b*",
                            b"sh",
                            b"INLINE IMAGE",
                        }
                        for _, op in stream.operations
                    ):
                        status = "EM_BRANCO"
                    else:
                        status = "REVISAO_NECESSARIA"
                        reasons.append(Reason.SEM_CONTEUDO_TEXTUAL)
                elif illegible(text):
                    status = "REVISAO_NECESSARIA"
                    reasons.append(Reason.CARACTERES_ILEGIVEIS)
                sections = bookmarks.get(number, [])[:]
                if declared:
                    sections.append(Section(titulo=declared, origem="DECLARADA"))
                pages.append(page(number, text, status, sections))
            if counter.count > counter.structural_count:
                reasons.append(Reason.AVISOS_DO_PARSER)
            if any(p.situacao == "OCR_NECESSARIO" for p in pages):
                state = State.OCR_NECESSARIO
            elif reasons:
                state = State.REVISAO_NECESSARIA
            elif not any(p.texto.strip() for p in pages):
                return failed(Reason.SEM_CONTEUDO_TEXTUAL)
            else:
                state = State.CONCLUIDA
            return ParsedDocument(
                estado=state,
                motivos=list(dict.fromkeys(reasons)),
                paginas=pages,
                avisos_parser=counter.count,
                avisos_estruturais=counter.structural_count,
            )
    except LimitReachedError:
        return failed(Reason.LIMITE_EXCEDIDO)
    except (
        PdfReadError,
        ValueError,
        TypeError,
        KeyError,
        IndexError,
        RecursionError,
        OSError,
    ):
        return failed(Reason.PDF_CORROMPIDO)
    finally:
        logger.handlers, logger.propagate = old_handlers, old_propagate
        logger.setLevel(old_level)


def parse(
    content: bytes, format: str, declared: str | None, policy: ExtractionPolicy
) -> ParsedDocument:
    if not content or len(content) > MAX_BYTES or format not in {"PDF", "TXT"}:
        return failed(Reason.TIPO_OU_TAMANHO_INVALIDO)
    if format == "PDF":
        if not content.startswith(b"%PDF-"):
            return failed(Reason.TIPO_OU_TAMANHO_INVALIDO)
        return parse_pdf(content, declared, policy)
    if policy.selected_pages is not None:
        return failed(Reason.TIPO_OU_TAMANHO_INVALIDO)
    return parse_txt(content, declared, policy)
