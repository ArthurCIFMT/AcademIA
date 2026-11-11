import hashlib
import json
import os
import platform
import statistics
import time
from importlib.metadata import version
from pathlib import Path
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session, sessionmaker

from app.modules.knowledge.embeddings.encoder import E5Encoder
from app.modules.knowledge.ingestion.chunking import Selection, Span
from app.modules.knowledge.ingestion.contracts import digest
from app.modules.knowledge.ingestion.indexing import Indexer
from app.modules.knowledge.ingestion.parser import parse
from app.modules.knowledge.ingestion.service import Extractor
from app.modules.knowledge.retrieval.contracts import Request
from app.modules.knowledge.retrieval.service import Retriever
from app.modules.knowledge.schemas import Decision, Metadata
from app.modules.knowledge.service import approved_references, decide, register
from app.modules.knowledge.vector.qdrant import QdrantStore
from app.modules.knowledge.vector.settings import VectorSettings
from tests.knowledge.test_indexing import migration as migration
from tests.knowledge.test_indexing import sessions as sessions
from tests.knowledge.test_indexing import setup

ROOT = Path(__file__).resolve().parents[3]


def p95(values: list[float]) -> float:
    return sorted(values)[max(0, int(len(values) * 0.95 + 0.9999) - 1)]


@pytest.mark.integration
@pytest.mark.skipif(
    os.environ.get("ACADEMIA_TEST_EMBEDDINGS_REAL") != "1",
    reason="Ensaio RAG real exige E5 local; não substituir por double.",
)
def test_real_e5_labeled_retrieval_and_latency(
    sessions: sessionmaker[Session], tmp_path: Path
) -> None:
    actor, storage, _, _, _ = setup(sessions, tmp_path)
    dataset_path = ROOT / "docs/testes/rag05-consultas-v1.json"
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    catalog = json.loads(
        (ROOT / "materiais/rag/catalogo.json").read_text(encoding="utf-8-sig")
    )
    item = next(i for i in catalog["documentos"] if i["id"] == dataset["fonte_id"])
    body = (ROOT / "materiais/rag" / item["arquivo"]).read_bytes()
    assert hashlib.sha256(body).hexdigest() == dataset["arquivo_sha256"]
    reference, sha = storage.store(body, "PDF")
    metadata = Metadata(
        titulo=item["titulo"],
        origem_url=item["url"],
        licenca=item["licenca"],
        idioma=item["idioma"],
        autores=item.get("autores", []),
        ano=item["ano"],
        paginas_declaradas=item["paginas_pdf"],
        finalidades=["DUVIDAS"],
        limites="Ensaio de recuperação de definições, sem prescrição individual.",
    )
    with sessions.begin() as session:
        row, _ = register(
            session,
            actor,
            "RAG05-REAL",
            "LITERATURA",
            metadata,
            "PDF",
            len(body),
            reference,
            sha,
            uuid4(),
        )
        decide(
            session,
            actor,
            row.id,
            Decision(revisao=1, estado="APROVADO"),
            storage,
            uuid4(),
        )
        ref = next(r for r in approved_references(session) if r.version_id == row.id)
    extraction = Extractor(storage, root=tmp_path / "pdf", parser=parse).extract(
        ref, approval_check=lambda *_: True
    )
    for spec in dataset["trechos"]:
        text = extraction.resultado.paginas[spec["pagina"] - 1].texto[
            spec["inicio"] : spec["fim"]
        ]
        assert hashlib.sha256(text.encode()).hexdigest() == spec["texto_hash"]
    selection = Selection(
        finalidade="DUVIDAS",
        motivo_curadoria=(
            "Definições introdutórias e resumo em inglês revisados para ensaio RAG-05"
        ),
        trechos=[
            Span(
                **{
                    k: v
                    for k, v in s.items()
                    if k in {"pagina", "inicio", "fim", "secao"}
                }
            )
            for s in dataset["trechos"]
        ],
    )
    encoder = E5Encoder()
    store = QdrantStore(VectorSettings(path=str(tmp_path / "qdrant")))
    try:
        cold = time.perf_counter()
        encoder.queries(["Inicialização técnica do modelo de recuperação"], 90)
        cold_seconds = time.perf_counter() - cold
        indexed = Indexer(sessions, store, encoder, lock_root=tmp_path / "locks").run(
            actor, extraction, selection
        )
        assert indexed.estado == "CONCLUIDA" and indexed.total == len(
            dataset["trechos"]
        )
        service = Retriever(sessions, store, encoder)
        context = uuid4()
        expected = {s["id"]: s["texto_hash"] for s in dataset["trechos"]}
        observations = []
        for case in dataset["consultas"]:
            result = service.retrieve(
                Request(
                    contexto_id=context, finalidade="DUVIDAS", consulta=case["consulta"]
                )
            )
            actual = {e.texto_hash for e in result.evidencias}
            correct = (
                (
                    result.estado in {"SEM_EVIDENCIAS", "EVIDENCIA_INSUFICIENTE"}
                    and not actual
                )
                if case["deve_abster"]
                else (
                    result.estado == "EVIDENCIAS_ENCONTRADAS"
                    and any(expected[i] in actual for i in case["esperados"])
                )
            )
            observations.append(
                {
                    "id": case["id"],
                    "idioma_evidencia": case["idioma_evidencia"],
                    "deve_abster": case["deve_abster"],
                    "correto": correct,
                    "estado": result.estado,
                    "gold": case["esperados"],
                    "textos_retornados": [e.texto_hash for e in result.evidencias],
                    "scores": [e.score for e in result.evidencias],
                    "busca_ms": result.busca_ms,
                    "total_ms": result.total_ms,
                }
            )
        positives = [r for r in observations if not r["deve_abster"]]
        negatives = [r for r in observations if r["deve_abster"]]
        recalls = {
            lang: sum(r["correto"] for r in positives if r["idioma_evidencia"] == lang)
            / sum(r["idioma_evidencia"] == lang for r in positives)
            for lang in {"pt", "en"}
        }
        report = {
            "schema_version": 1,
            "tipo": "RECUPERACAO_REAL_SEM_LLM",
            "dataset_sha256": hashlib.sha256(dataset_path.read_bytes()).hexdigest(),
            "fonte_sha256": sha,
            "configuracao_sha256": digest(encoder.space.model_dump(mode="json")),
            "modelo": encoder.space.model_dump(mode="json"),
            "ambiente": {
                "python": platform.python_version(),
                "sistema": platform.platform(),
                "cpu": platform.processor(),
                "cpu_threads": encoder.settings.cpu_threads,
                "qdrant_client": version("qdrant-client"),
                "sentence_transformers": version("sentence-transformers"),
            },
            "volume": {
                "documentos": 1,
                "fragmentos": indexed.total,
                "dimensoes": 384,
                "consultas": len(observations),
                "positivas": len(positives),
                "fora_escopo": len(negatives),
            },
            "limiares_pre_definidos": dataset["metas"],
            "resultados": {
                "recall_at_5": sum(r["correto"] for r in positives) / len(positives),
                "recall_por_idioma": recalls,
                "abstencao_fora_escopo": sum(r["correto"] for r in negatives)
                / len(negatives),
                "busca_p50_ms": statistics.median(
                    [r["busca_ms"] for r in observations]
                ),
                "busca_p95_ms": p95([r["busca_ms"] for r in observations]),
                "total_p50_ms": statistics.median(
                    [r["total_ms"] for r in observations]
                ),
                "total_p95_ms": p95([r["total_ms"] for r in observations]),
                "inicializacao_e5_segundos": cold_seconds,
            },
            "limites": [
                (
                    "Amostra pequena de definições e resumo original em inglês "
                    "de uma publicação brasileira."
                ),
                (
                    "Modelo aquecido antes da busca; "
                    "carga inicial informada separadamente. "
                    "Cache de consultas vazio no início."
                ),
                (
                    "Não mede resposta de LLM, dose individual, validade clínica "
                    "ou desempenho em corpus amplo."
                ),
                (
                    "Não promove fontes pendentes nem publica dados "
                    "no banco de desenvolvimento."
                ),
            ],
            "casos": observations,
        }
        report_file = os.environ.get("ACADEMIA_RAG_REPORT")
        if report_file:
            Path(report_file).write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
        assert report["resultados"]["recall_at_5"] >= dataset["metas"]["recall_at_5"]
        assert all(v >= dataset["metas"]["recall_por_idioma"] for v in recalls.values())
        assert (
            report["resultados"]["abstencao_fora_escopo"]
            >= dataset["metas"]["abstencao_fora_escopo"]
        )
        assert (
            report["resultados"]["busca_p95_ms"]
            <= dataset["metas"]["p95_busca_segundos"] * 1000
        )
    finally:
        encoder.close()
        store.close()
