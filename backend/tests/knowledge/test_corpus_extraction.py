import hashlib
import json
from pathlib import Path
from uuid import uuid4

import pytest

from app.modules.knowledge.ingestion.service import Extractor
from app.modules.knowledge.schemas import Metadata
from app.modules.knowledge.service import ApprovedReference
from app.modules.knowledge.storage import CorpusStorage

ROOT = Path(__file__).resolve().parents[3]
REPORT = json.loads(
    (ROOT / "docs/testes/extracao-corpus-rag03.json").read_text(encoding="utf-8")
)


@pytest.mark.integration
@pytest.mark.parametrize("catalog_id", [item["id"] for item in REPORT["documentos"]])
def test_selected_real_corpus_keeps_pages_and_explicit_quality_state(
    catalog_id: str, tmp_path: Path
) -> None:
    catalog = json.loads(
        (ROOT / "materiais/rag/catalogo.json").read_text(encoding="utf-8-sig")
    )
    selected = json.loads(
        (ROOT / "materiais/rag/corpus-inicial.json").read_text(encoding="utf-8-sig")
    )
    selection = next(
        item for item in selected["documentos"] if item["id"] == catalog_id
    )
    document = next(item for item in catalog["documentos"] if item["id"] == catalog_id)
    expected = next(item for item in REPORT["documentos"] if item["id"] == catalog_id)
    content = (ROOT / "materiais/rag" / document["arquivo"]).read_bytes()
    assert (
        hashlib.sha256(content).hexdigest()
        == document["sha256"]
        == selection["sha256"]
        == expected["sha256"]
    )
    storage = CorpusStorage(tmp_path / "originais")
    reference, sha = storage.store(content, "PDF")
    metadata = Metadata(
        titulo=document["titulo"],
        origem_url=document["url"],
        licenca=document["licenca"],
        idioma=document["idioma"],
        autores=document.get("autores", []),
        ano=document.get("ano"),
        paginas_declaradas=document["paginas_pdf"],
        finalidades=selection["finalidades"],
        limites=selection["limites"],
    )
    # IDs e aprovação de teste isolados; a seleção/hash vêm do corpus técnico aceito.
    ref = ApprovedReference(uuid4(), 2, sha, reference, "PDF", metadata)
    extractor = Extractor(storage, root=tmp_path / "extracoes")
    result = extractor.extract(ref, approval_check=lambda *_: True)
    assert result.resultado.estado.value == expected["estado"]
    assert [reason.value for reason in result.resultado.motivos] == expected["motivos"]
    assert len(result.resultado.paginas) == document["paginas_pdf"]
    assert [page.numero for page in result.resultado.paginas] == list(
        range(1, document["paginas_pdf"] + 1)
    )
    assert (
        sum(bool(page.texto.strip()) for page in result.resultado.paginas)
        == expected["paginas_com_texto"]
    )
    assert sum(len(page.texto) for page in result.resultado.paginas) > 1000
    assert extractor.extract(ref, approval_check=lambda *_: True) == result
