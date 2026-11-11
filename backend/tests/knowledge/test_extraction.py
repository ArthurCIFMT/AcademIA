import hashlib
import json
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from app.modules.knowledge.ingestion.contracts import (
    ExtractionPolicy,
    Reason,
    State,
)
from app.modules.knowledge.ingestion.parser import failed, parse
from app.modules.knowledge.ingestion.process import run_parser
from app.modules.knowledge.ingestion.service import ExtractionError, Extractor
from app.modules.knowledge.schemas import MAX_BYTES, Metadata
from app.modules.knowledge.service import ApprovedReference
from app.modules.knowledge.storage import CorpusStorage

FIXTURES = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[3]
META = Metadata(
    titulo="Fixture sintética",
    origem_url="https://example.test/literatura",
    licenca="Fixture de teste",
    idioma="pt-BR",
    finalidades=["DUVIDAS"],
    limites="Não é evidência científica.",
)


def reference(storage: CorpusStorage, name: str = "simbolos.pdf") -> ApprovedReference:
    format = "PDF" if name.endswith(".pdf") else "TXT"
    ref, digest = storage.store((FIXTURES / name).read_bytes(), format)
    return ApprovedReference(uuid4(), 2, digest, ref, format, META)


def test_fixture_pdf_preserves_pages_bookmarks_negation_symbols_and_units() -> None:
    result = parse(
        (FIXTURES / "simbolos.pdf").read_bytes(),
        "PDF",
        "Seção declarada",
        ExtractionPolicy(),
    )
    assert result.estado == State.CONCLUIDA
    assert [p.numero for p in result.paginas] == [1, 2]
    expected = json.loads((FIXTURES / "expectativas.json").read_text(encoding="utf-8"))
    for page, phrases in zip(result.paginas, expected["simbolos.pdf"], strict=True):
        normalized = " ".join(page.texto.split())
        for phrase in phrases:
            assert phrase in normalized
        assert page.texto_sha256 == hashlib.sha256(page.texto.encode()).hexdigest()
        assert any(s.origem == "MARCADOR_PDF" for s in page.secoes)
        assert any(s.titulo == "Seção declarada" for s in page.secoes)


def test_utf8_bom_crlf_txt_preserves_content_and_exact_line_numbers() -> None:
    content = (
        b"\xef\xbb\xbf"
        + (
            "\r\n".join(
                (FIXTURES / "simbolos.txt").read_text(encoding="utf-8").splitlines()
            )
            + "\r\n"
        ).encode()
    )
    result = parse(content, "TXT", None, ExtractionPolicy())
    assert result.estado == State.CONCLUIDA
    page = result.paginas[0]
    assert page.numero is None
    assert page.texto == content.decode("utf-8-sig")
    assert (page.linha_inicio, page.linha_fim) == (1, 5)
    assert [(s.titulo, s.linha) for s in page.secoes] == [
        ("Medidas sintéticas", 1),
        ("Restrições", 4),
    ]
    assert "não prosseguir" in page.texto and "≥" in page.texto and "≤" in page.texto


@pytest.mark.parametrize(
    "name,state,reason",
    [
        ("escaneado.pdf", State.OCR_NECESSARIO, Reason.PAGINA_SEM_CAMADA_TEXTUAL),
        ("misto.pdf", State.OCR_NECESSARIO, Reason.PAGINA_SEM_CAMADA_TEXTUAL),
        ("vazio.pdf", State.FALHA, Reason.SEM_CONTEUDO_TEXTUAL),
        ("protegido.pdf", State.FALHA, Reason.PDF_PROTEGIDO),
    ],
)
def test_scan_mixed_blank_and_protected_are_not_false_success(
    name: str, state: State, reason: Reason
) -> None:
    result = parse((FIXTURES / name).read_bytes(), "PDF", None, ExtractionPolicy())
    assert result.estado == state and reason in result.motivos
    if name == "misto.pdf":
        assert [(p.numero, p.situacao) for p in result.paginas] == [
            (1, "TEXTO"),
            (2, "OCR_NECESSARIO"),
            (3, "EM_BRANCO"),
        ]


@pytest.mark.parametrize(
    "content,format,reason",
    [
        (b"%PDF-1.4\ncorrompido", "PDF", Reason.PDF_CORROMPIDO),
        (b"nao-pdf", "PDF", Reason.TIPO_OU_TAMANHO_INVALIDO),
        (b"", "TXT", Reason.TIPO_OU_TAMANHO_INVALIDO),
        (b"a", "PNG", Reason.TIPO_OU_TAMANHO_INVALIDO),
        (b"\xff", "TXT", Reason.TEXTO_INVALIDO),
        (b" \n", "TXT", Reason.SEM_CONTEUDO_TEXTUAL),
        (b"x" * (MAX_BYTES + 1), "TXT", Reason.TIPO_OU_TAMANHO_INVALIDO),
    ],
)
def test_invalid_inputs_record_failure(
    content: bytes, format: str, reason: Reason
) -> None:
    result = parse(content, format, None, ExtractionPolicy())
    assert result.estado == State.FALHA and result.motivos == [reason]
    assert not result.paginas


@pytest.mark.parametrize(
    "change",
    [
        {"max_pages": 1},
        {"max_page_chars": 20},
        {"max_total_chars": 30},
        {"max_stream_bytes": 20},
    ],
)
def test_parser_budgets_never_truncate_into_success(change: dict[str, int]) -> None:
    result = parse(
        (FIXTURES / "simbolos.pdf").read_bytes(),
        "PDF",
        None,
        ExtractionPolicy(**change),
    )
    assert result.estado != State.CONCLUIDA
    assert result.motivos


def test_invalid_glyphs_need_review_instead_of_generic_cleaning() -> None:
    result = parse("não ≥ 10 kg\x00\ufffd".encode(), "TXT", None, ExtractionPolicy())
    assert result.estado == State.REVISAO_NECESSARIA
    assert result.motivos == [Reason.CARACTERES_ILEGIVEIS]
    assert result.paginas[0].texto == "não ≥ 10 kg\x00\ufffd"


def test_timeout_and_invalid_worker_output_are_not_retried(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    call = MagicMock(side_effect=subprocess.TimeoutExpired("worker", 1))
    monkeypatch.setattr("app.modules.knowledge.ingestion.process.subprocess.run", call)
    assert run_parser(b"texto", "TXT", None, ExtractionPolicy()).motivos == [
        Reason.TIMEOUT
    ]
    call.assert_called_once()
    call.side_effect = None
    call.return_value = subprocess.CompletedProcess(
        [], 0, b"nao-json", b"detalhe privado"
    )
    result = run_parser(b"texto", "TXT", None, ExtractionPolicy())
    assert result.estado == State.FALHA and result.motivos == [
        Reason.ERRO_DO_PROCESSADOR
    ]


def test_persistent_idempotent_result_contains_real_provenance(tmp_path: Path) -> None:
    storage = CorpusStorage(tmp_path / "originais")
    ref = reference(storage)
    parser = MagicMock(side_effect=parse)
    extractor = Extractor(storage, root=tmp_path / "resultados", parser=parser)
    result = extractor.extract(ref, approval_check=lambda *_: True)
    replay = Extractor(storage, root=extractor.root, parser=parser).extract(
        ref, approval_check=lambda *_: True
    )
    assert replay == result and parser.call_count == 1
    assert (
        result.documento_versao_id == ref.version_id
        and result.arquivo_sha256 == ref.sha256
    )
    assert result.metadados == ref.metadata and result.politica.parser.startswith(
        "pypdf/"
    )
    offset = result.criado_em.utcoffset()
    assert offset is not None and offset.total_seconds() == 0
    assert len(list(extractor.root.glob("*.json"))) == 1
    later = ApprovedReference(
        uuid4(), 2, ref.sha256, ref.reference, ref.format, ref.metadata
    )
    assert extractor.extract(later, approval_check=lambda *_: True).id != result.id


def test_revocation_blocks_replay_and_revocation_during_parse_blocks_storage(
    tmp_path: Path,
) -> None:
    storage = CorpusStorage(tmp_path / "originais")
    ref = reference(storage)
    root = tmp_path / "resultados"
    extractor = Extractor(storage, root=root, parser=parse)
    with pytest.raises(ExtractionError, match="VERSAO_NAO_APROVADA"):
        extractor.extract(ref, approval_check=lambda *_: False)
    assert not root.exists()
    checks = iter([True, False])
    with pytest.raises(ExtractionError, match="VERSAO_NAO_APROVADA"):
        extractor.extract(ref, approval_check=lambda *_: next(checks))
    assert not list(root.glob("*.json"))
    extractor.extract(ref, approval_check=lambda *_: True)
    with pytest.raises(ExtractionError, match="VERSAO_NAO_APROVADA"):
        extractor.extract(ref, approval_check=lambda *_: False)


def test_failure_is_saved_and_explicit_retry_is_bounded(tmp_path: Path) -> None:
    storage = CorpusStorage(tmp_path / "originais")
    ref = reference(storage)
    parser = MagicMock(return_value=failed(Reason.TIMEOUT))
    extractor = Extractor(storage, root=tmp_path / "resultados", parser=parser)
    first = extractor.extract(ref, approval_check=lambda *_: True)
    assert first.resultado.motivos == [Reason.TIMEOUT]
    assert extractor.extract(ref, approval_check=lambda *_: True) == first
    for attempt in (2, 3, 3):
        last = extractor.extract(ref, approval_check=lambda *_: True, retry_failed=True)
        assert last.id == first.id and last.tentativa == attempt
    assert parser.call_count == 3 and len(last.historico) == 2
    assert len(list(extractor.root.glob("*.json"))) == 1


def test_corrupted_source_and_corrupted_cache_are_not_accepted(tmp_path: Path) -> None:
    storage = CorpusStorage(tmp_path / "originais")
    ref = reference(storage)
    storage.path(ref.reference).write_bytes(b"alterado")
    extractor = Extractor(storage, root=tmp_path / "resultados", parser=parse)
    result = extractor.extract(ref, approval_check=lambda *_: True)
    assert result.resultado.motivos == [Reason.ARQUIVO_AUSENTE_OU_ALTERADO]
    path = next(extractor.root.glob("*.json"))
    path.write_text('{"resultado":{},"sha256":"alterado"}')
    with pytest.raises(ExtractionError, match="ARTEFATO_INCONSISTENTE"):
        extractor.extract(ref, approval_check=lambda *_: True)


def test_concurrent_extraction_runs_once_for_same_version(tmp_path: Path) -> None:
    storage = CorpusStorage(tmp_path / "originais")
    ref = reference(storage, "simbolos.txt")
    parser = MagicMock(side_effect=parse)

    def execute(_: int) -> object:
        return Extractor(storage, root=tmp_path / "resultados", parser=parser).extract(
            ref, approval_check=lambda *_: True
        )

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(execute, range(4)))
    assert parser.call_count == 1
    assert all(r == results[0] for r in results)


@pytest.mark.integration
def test_real_worker_preserves_fixture_text_and_process_boundary(
    tmp_path: Path,
) -> None:
    storage = CorpusStorage(tmp_path / "originais")
    ref = reference(storage)
    result = Extractor(storage, root=tmp_path / "resultados").extract(
        ref, approval_check=lambda *_: True
    )
    assert result.resultado.estado == State.CONCLUIDA
    assert "≥ 10 kg" in result.resultado.paginas[0].texto
    assert result.documento_versao_id == ref.version_id
