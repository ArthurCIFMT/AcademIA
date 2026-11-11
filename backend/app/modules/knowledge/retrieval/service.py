import hashlib
import time
from collections import OrderedDict
from collections.abc import Callable
from threading import RLock
from uuid import UUID

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.modules.knowledge.embeddings.encoder import EmbeddingError, validate_vectors
from app.modules.knowledge.ingestion.index_models import Fragment, Ingestion
from app.modules.knowledge.ingestion.indexing import available_ingestions
from app.modules.knowledge.models import DocumentVersion
from app.modules.knowledge.retrieval.contracts import (
    Annotation,
    Evidence,
    Hit,
    Request,
    Result,
)
from app.modules.knowledge.retrieval.ports import QueryEncoder, SearchIndex
from app.modules.knowledge.vector.contracts import VectorError


class Retriever:
    def __init__(
        self,
        sessions: sessionmaker[Session],
        index: SearchIndex,
        encoder: QueryEncoder,
        *,
        annotations: tuple[Annotation, ...] = (),
        min_score: float = 0.8,
        budget: float = 60,
        cache_size: int = 128,
        clock: Callable[[], float] = time.perf_counter,
    ) -> None:
        if not 0 <= min_score <= 1 or budget <= 0 or not 0 <= cache_size <= 1024:
            raise ValueError("Limites de recuperação inválidos.")
        self.sessions, self.index, self.encoder = sessions, index, encoder
        self.annotations, self.min_score, self.budget = annotations, min_score, budget
        self.cache_size, self.clock = cache_size, clock
        self._cache: OrderedDict[
            tuple[UUID, str, str, str], tuple[float, list[float]]
        ] = OrderedDict()
        self._lock = RLock()

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def _query(self, request: Request, remaining: float) -> list[float]:
        key = (
            request.contexto_id,
            request.finalidade,
            self.encoder.space.fingerprint,
            hashlib.sha256(request.consulta.encode()).hexdigest(),
        )
        with self._lock:
            cached = self._cache.get(key)
            if cached and self.clock() - cached[0] < 300:
                self._cache.move_to_end(key)
                return list(cached[1])
        if self.encoder.tokens("query: " + request.consulta) > 512:
            raise EmbeddingError("CONTEXTO_EXCEDIDO")
        vectors = self.encoder.queries([request.consulta], remaining)
        validate_vectors(vectors, 1, self.encoder.space.dimension)
        if self.cache_size:
            with self._lock:
                self._cache[key] = (self.clock(), list(vectors[0]))
                while len(self._cache) > self.cache_size:
                    self._cache.popitem(last=False)
        return vectors[0]

    def _verify(
        self, session: Session, hit: Hit, allowed: set[UUID], request: Request
    ) -> tuple[Evidence, str]:
        p = hit.payload
        p.check()
        if (
            hit.id != p.fragmento_id
            or p.ingestao_id not in allowed
            or p.finalidade != request.finalidade
        ):
            raise ValueError("Resultado fora do escopo.")
        fragment = session.get(Fragment, hit.id)
        ingestion = session.get(Ingestion, p.ingestao_id)
        source = session.get(DocumentVersion, p.documento_versao_id)
        if not fragment or not ingestion or not source:
            raise ValueError("Proveniência ausente.")
        if (
            fragment.ingestao_id != ingestion.id
            or fragment.vetor_id != hit.id
            or fragment.indexado_em is None
            or fragment.texto_hash != p.texto_hash
            or fragment.colecao != ingestion.colecao
            or fragment.inicio != p.inicio
            or fragment.fim != p.fim
            or fragment.pagina_inicio != p.pagina
            or fragment.linha_inicio != p.linha_inicio
            or fragment.linha_fim != p.linha_fim
            or fragment.secao != p.secao
            or fragment.tokens != p.tokens
            or fragment.input_tokens != p.input_tokens
            or ingestion.documento_versao_id != source.id
            or ingestion.aprovacao_revisao != p.aprovacao_revisao
            or ingestion.config_hash != p.config_hash
            or p.space_sha256 != self.encoder.space.fingerprint
            or source.metadados != p.metadados.model_dump(mode="json")
        ):
            raise ValueError("Proveniência divergente.")
        return Evidence(
            fragmento_id=hit.id,
            ingestao_id=ingestion.id,
            documento_versao_id=source.id,
            aprovacao_revisao=p.aprovacao_revisao,
            titulo=p.metadados.titulo,
            origem_url=str(p.metadados.origem_url),
            idioma=p.metadados.idioma,
            pagina=p.pagina,
            linha_inicio=p.linha_inicio,
            linha_fim=p.linha_fim,
            secao=p.secao,
            texto=p.texto,
            texto_hash=p.texto_hash,
            score=hit.score,
        ), source.sha256

    def retrieve(self, request: Request) -> Result:
        start, search_ms = self.clock(), 0.0
        support = "NAO_SOLICITADO" if request.escopo_saude is None else "NAO_VERIFICADO"

        def result(
            state: str,
            reason: str,
            evidence: list[Evidence] | None = None,
            health: str | None = None,
        ) -> Result:
            return Result.model_validate(
                {
                    "estado": state,
                    "motivo": reason,
                    "evidencias": evidence or [],
                    "suporte_saude": health or support,
                    "busca_ms": search_ms,
                    "total_ms": (self.clock() - start) * 1000,
                }
            )

        try:
            status = self.index.check()
            if status.space_sha256 != self.encoder.space.fingerprint:
                return result("SERVICO_INDISPONIVEL", "ESPACO_INCOMPATIVEL")
            with self.sessions.begin() as session:
                allowed = available_ingestions(
                    session, status.collection, status.space_sha256
                )
            if not allowed:
                return result("SEM_EVIDENCIAS", "SEM_INGESTAO_APROVADA")
            vector = self._query(request, self.budget)
            if self.clock() - start >= self.budget:
                return result("SERVICO_INDISPONIVEL", "ORCAMENTO_EXCEDIDO")
            tick = self.clock()
            hits = self.index.search(vector, allowed, request.finalidade, 40)
            search_ms = (self.clock() - tick) * 1000
            if self.clock() - start >= self.budget:
                return result("SERVICO_INDISPONIVEL", "ORCAMENTO_EXCEDIDO")
            with self.sessions.begin() as session:
                current = set(
                    available_ingestions(
                        session, status.collection, status.space_sha256
                    )
                )
                verified = [
                    self._verify(session, hit, current, request)
                    for hit in hits
                    if hit.payload.ingestao_id in current
                ]
            if self.clock() - start >= self.budget:
                return result("SERVICO_INDISPONIVEL", "ORCAMENTO_EXCEDIDO")
            if not verified:
                return result("SEM_EVIDENCIAS", "SEM_RESULTADO_VIGENTE")
            candidates: list[tuple[Evidence, str]] = []
            seen: set[tuple[UUID, str]] = set()
            for evidence, sha in sorted(
                verified, key=lambda pair: (-pair[0].score, str(pair[0].fragmento_id))
            ):
                key = (evidence.documento_versao_id, evidence.texto_hash)
                if evidence.score < self.min_score or key in seen:
                    continue
                seen.add(key)
                candidates.append((evidence, sha))
            if not candidates:
                return result("EVIDENCIA_INSUFICIENTE", "SIMILARIDADE_ABAIXO_DO_LIMIAR")
            if request.escopo_saude is not None:
                relevant = []
                positions: set[str] = set()
                for evidence, sha in candidates:
                    labels = [
                        a
                        for a in self.annotations
                        if a.arquivo_sha256 == sha
                        and a.texto_hash == evidence.texto_hash
                        and a.escopo == request.escopo_saude
                    ]
                    if labels:
                        positions.update(a.posicao for a in labels)
                        relevant.append(evidence)
                if len(positions) > 1:
                    return result(
                        "CONFLITO",
                        "FONTES_DIVERGENTES",
                        relevant[: request.top_k],
                        "CONFLITANTE",
                    )
                if positions != {"SUPORTE"}:
                    return result(
                        "EVIDENCIA_INSUFICIENTE", "SEM_SUPORTE_CURADO_PARA_O_ESCOPO"
                    )
                return result(
                    "EVIDENCIAS_ENCONTRADAS",
                    "ESCOPO_CURADO_PERTINENTE",
                    relevant[: request.top_k],
                    "PERTINENTE",
                )
            return result(
                "EVIDENCIAS_ENCONTRADAS",
                "TRECHOS_CANDIDATOS",
                [e for e, _ in candidates[: request.top_k]],
            )
        except (EmbeddingError, VectorError, SQLAlchemyError):
            return result("SERVICO_INDISPONIVEL", "FALHA_DO_SERVICO")
        except (ValueError, KeyError, TypeError):
            return result("SERVICO_INDISPONIVEL", "PROVENIENCIA_INVALIDA")
