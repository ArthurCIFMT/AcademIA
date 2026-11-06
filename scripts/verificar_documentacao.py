#!/usr/bin/env python3
"""Verifica a documentação local sem rede, dependências externas ou escrita.

Uso: python scripts/verificar_documentacao.py [--json] [--root DIRETORIO]
O comando valida estrutura e referências; não aprova conteúdo clínico, não conta
páginas lendo o formato PDF e não executa testes da aplicação ainda não criada.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import html
import json
import os
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit


MER_PATH = "docs/arquitetura/modelo-de-dados/original/MER_Academia_Completo_v4.drawio.png"
MER_SHA256 = "5b57634d6936bc76c82e3f85bfa45a91626ec734af77b45e0a083e2990c1df93"
MANIFEST_PATH = "docs/prompts/README.md"
TRACE_PATH = "docs/arquitetura/rastreabilidade-prompts.md"
CATALOG_PATH = "materiais/rag/catalogo.json"
CASES_PATH = "docs/testes/casos-documentais-rag-2026-11-04.json"
CASE_REPORT_PATH = "docs/testes/avaliacao-documental-rag-2026-11-04.md"
IGNORED_DIRS = {
    ".git", ".codex", ".agents", ".aws", ".venv", "venv", "node_modules",
    "tmp", "temp", "dist", "build", ".cache", "__pycache__",
}
REQ_PATTERN = r"(?:CA-MRF\d+\.\d+|CA-\d+\.\d+|RNF-\d+|RF-\d+|RN-\d+|MRF\d+)"
REQ_RE = re.compile(r"(?<![\w-])" + REQ_PATTERN + r"(?![\w.])")
NODE_PATTERN = r"(?:P00|(?:[A-Z]{2,})-\d{2}[A-Z]?)"
NODE_RE = re.compile(r"(?<![\w-])" + NODE_PATTERN + r"(?![\w-])")
EXCLUSION_RE = re.compile(
    r"\b(?:exclui|excluem|excluindo|exceto|sem incluir|não inclui|não incluem|"
    r"não depende de|não dependem de|sem depender de)\b", re.IGNORECASE,
)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8-sig")


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def cells(line: str) -> list[str]:
    return [part.strip() for part in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def no_code(text: str) -> str:
    """Remove código preservando linhas para não validar exemplos futuros em crases."""
    lines = []
    fence = None
    for line in text.splitlines(keepends=True):
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker and fence is None:
            fence = marker.group(1)
            lines.append("\n" if line.endswith("\n") else "")
        elif fence is not None:
            if marker and marker.group(1)[0] == fence[0] and len(marker.group(1)) >= len(fence):
                fence = None
            lines.append("\n" if line.endswith("\n") else "")
        else:
            lines.append(re.sub(r"(`+)([^\n]*?)\1", lambda m: " " * len(m.group(0)), line))
    return "".join(lines)


def link_targets(text: str):
    """Lê destinos inline e definições de referência, incluindo parênteses balanceados."""
    text = no_code(text)
    for match in re.finditer(r"!?\[[^\]\n]*\]\(\s*", text):
        start = match.end()
        if start >= len(text):
            continue
        if text[start] == "<":
            end = text.find(">", start + 1)
            if end >= 0:
                yield text[start + 1:end], text.count("\n", 0, match.start()) + 1
            continue
        end = start
        depth = 0
        while end < len(text):
            char = text[end]
            if char == "\\" and end + 1 < len(text):
                end += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                if depth == 0:
                    break
                depth -= 1
            elif char.isspace() and depth == 0:
                break
            end += 1
        target = text[start:end]
        if target:
            yield re.sub(r"\\([() <>])", r"\1", target), text.count("\n", 0, match.start()) + 1
    for match in re.finditer(r"^\s{0,3}\[[^\]\n]+\]:\s*(<[^>]+>|\S+)", text, re.MULTILINE):
        yield match.group(1).strip("<>"), text.count("\n", 0, match.start()) + 1


def id_parts(identifier: str):
    match = re.fullmatch(r"(CA-MRF|CA-)(\d+)\.(\d+)", identifier)
    if match:
        return match.group(1), int(match.group(2)), int(match.group(3))
    match = re.fullmatch(r"([A-Z]+-?|MRF)(\d+)([A-Z]?)", identifier)
    if not match:
        raise ValueError(f"Identificador inválido: {identifier}")
    return match.group(1), int(match.group(2)), match.group(3)


def range_ids(first: str, last: str, known: set[str]) -> set[str]:
    a, b = id_parts(first), id_parts(last)
    if a[0] != b[0] or a[1:] > b[1:]:
        raise ValueError(f"Intervalo inválido: {first}–{last}")
    if a[0].startswith("CA-"):
        # Critérios de requisitos diferentes têm quantidades variáveis.
        return {key for key in known if id_parts(key)[0] == a[0] and a[1:] <= id_parts(key)[1:] <= b[1:]} | {first, last}
    if a[2] or b[2]:
        if a[1] != b[1] or not a[2] or not b[2]:
            raise ValueError(f"Intervalo com sufixos ambíguo: {first}–{last}")
        return {f"{a[0]}{a[1]:02d}{chr(letter)}" for letter in range(ord(a[2]), ord(b[2]) + 1)}
    return {f"{a[0]}{number:02d}" for number in range(a[1], b[1] + 1)}


def identifiers(text: str, pattern: re.Pattern, known: set[str]) -> set[str]:
    matches = list(pattern.finditer(text))
    result = set()
    index = 0
    while index < len(matches):
        first = matches[index]
        if index + 1 < len(matches):
            last = matches[index + 1]
            middle = text[first.end():last.start()].strip()
            if middle in {"-", "–", "—"}:
                result.update(range_ids(first.group(0), last.group(0), known))
                index += 2
                continue
        result.add(first.group(0))
        index += 1
    return result


class Audit:
    def __init__(self, root: Path):
        self.root = root
        self.errors = []
        self.warnings = []
        self.metrics = {}
        self.requirements = set()
        self.acceptance = set()
        self.cards = {}
        self.catalog = {}

    def relative(self, path: Path) -> str:
        try:
            return path.relative_to(self.root).as_posix()
        except ValueError:
            return str(path)

    def issue(self, code: str, message: str, path: str | Path = "", line: int | None = None):
        self.errors.append({"codigo": code, "arquivo": self.relative(path) if isinstance(path, Path) else path,
                            "linha": line, "mensagem": message})

    def checked_refs(self, text: str, path: Path, line=None):
        try:
            refs = identifiers(text, REQ_RE, self.requirements | self.acceptance)
        except ValueError as exc:
            self.issue("INTERVALO_REQUISITO", str(exc), path, line)
            return set()
        for identifier in sorted(refs - self.requirements - self.acceptance):
            self.issue("REQUISITO_INEXISTENTE", identifier, path, line)
        return refs

    def local_path(self, value: str, base: Path, source: Path) -> Path | None:
        candidate = (base / value).resolve()
        try:
            candidate.relative_to(self.root)
        except ValueError:
            self.issue("CAMINHO_FORA_REPOSITORIO", value, source)
            return None
        if not candidate.is_file():
            self.issue("ARQUIVO_AUSENTE", value, source)
            return None
        return candidate

    def check_links(self):
        count = 0
        files = 0
        for folder, dirs, names in os.walk(self.root, followlinks=False):
            dirs[:] = [name for name in dirs if name not in IGNORED_DIRS]
            for name in names:
                if not name.lower().endswith(".md"):
                    continue
                path = Path(folder) / name
                files += 1
                for raw, line in link_targets(read_text(path)):
                    raw = html.unescape(raw)
                    if raw.startswith("#") or raw.startswith("//"):
                        continue
                    parsed = urlsplit(raw)
                    if parsed.scheme:
                        continue
                    target = unquote(parsed.path)
                    if not target:
                        continue
                    # Um / inicial em link do repositório aponta à sua raiz.
                    dest = self.root / target.lstrip("/") if target.startswith("/") else path.parent / target
                    count += 1
                    if not dest.resolve().exists():
                        self.issue("LINK_LOCAL_QUEBRADO", raw, path, line)
        self.metrics.update(arquivos_markdown=files, links_locais=count)

    def check_requirements(self):
        definitions = {}
        specs = [
            ("RF", "docs/requisitos/requisitos-funcionais.md", r"^#{2,6}\s+(RF-\d+)\b"),
            ("RN", "docs/requisitos/regras-de-negocio.md", r"^\|\s*(RN-\d+)\s*\|"),
            ("RNF", "docs/requisitos/requisitos-nao-funcionais.md", r"^\|\s*(RNF-\d+)\s*\|"),
            ("MRF", "docs/requisitos/macrorequisitos-ia-rag.md", r"^\|\s*(MRF\d+)\s*\|"),
        ]
        ca_by_owner = defaultdict(list)
        for kind, relative, pattern in specs:
            path = self.root / relative
            text = read_text(path)
            ids = re.findall(pattern, text, re.MULTILINE)
            counts = Counter(ids)
            if not ids:
                self.issue("REQUISITOS_AUSENTES", f"Nenhum {kind} definido", path)
            for key, amount in counts.items():
                if amount > 1:
                    self.issue("ID_DUPLICADO", f"{key}: {amount} definições", path)
            if ids:
                maximum = max(id_parts(key)[1] for key in ids)
                prefix = "MRF" if kind == "MRF" else kind + "-"
                missing = {f"{prefix}{number:02d}" for number in range(1, maximum + 1)} - set(ids)
                for key in sorted(missing):
                    self.issue("ID_FALTANTE", key, path)
            self.requirements.update(ids)
            definitions[kind] = len(ids)
            if kind == "RF":
                criteria = re.findall(r"^\s*-\s+(?:\*\*)?(CA-\d+\.\d+):", text, re.MULTILINE)
            elif kind == "MRF":
                criteria = re.findall(r"\*\*(CA-MRF\d+\.\d+):\*\*", text)
            else:
                criteria = []
            for criterion in criteria:
                parts = id_parts(criterion)
                owner = f"MRF{parts[1]:02d}" if parts[0] == "CA-MRF" else f"RF-{parts[1]:02d}"
                ca_by_owner[owner].append(criterion)
                if owner not in ids:
                    self.issue("CA_SEM_REQUISITO", criterion, path)
            duplicate_ca = [key for key, amount in Counter(criteria).items() if amount > 1]
            for key in duplicate_ca:
                self.issue("CA_DUPLICADO", key, path)
            self.acceptance.update(criteria)
            for owner in ids if kind in {"RF", "MRF"} else []:
                owned = ca_by_owner[owner]
                if not owned:
                    self.issue("REQUISITO_SEM_CA", owner, path)
                    continue
                maximum = max(id_parts(key)[2] for key in owned)
                actual = {id_parts(key)[2] for key in owned}
                for number in sorted(set(range(1, maximum + 1)) - actual):
                    self.issue("CA_FALTANTE", f"{owner}, critério {number}", path)
        self.metrics.update(
            requisitos=definitions, criterios_aceite=len(self.acceptance),
            criterios_aceite_por_tipo={
                "RF": sum(key.startswith("CA-") and not key.startswith("CA-MRF") for key in self.acceptance),
                "MRF": sum(key.startswith("CA-MRF") for key in self.acceptance),
            },
        )
        summary_path = self.root / "docs/arquitetura/funcionamento-ia-rag.md"
        if summary_path.is_file():
            summary = read_text(summary_path)
            macro_count = re.search(r"tabela completa dos\s+(\d+)\s+macrorequisitos", summary)
            criterion_count = re.search(r"(\d+)\s+critérios\s+identificados", summary)
            if macro_count and int(macro_count.group(1)) != definitions["MRF"]:
                self.issue("CONTAGEM_MRF_DIVERGENTE", "Resumo de arquitetura diverge da tabela canônica", summary_path)
            actual = self.metrics["criterios_aceite_por_tipo"]["MRF"]
            if criterion_count and int(criterion_count.group(1)) != actual:
                self.issue("CONTAGEM_CA_DIVERGENTE", f"Resumo declara {criterion_count.group(1)}; tabela define {actual}", summary_path)

    def check_cards(self):
        prompts = self.root / "docs/prompts"
        manifest_path = self.root / MANIFEST_PATH
        manifest = read_text(manifest_path)
        manifest_cards = {}
        gates = {}
        for line_no, line in enumerate(manifest.splitlines(), 1):
            if not line.startswith("|"):
                continue
            row = cells(line)
            linked = re.match(r"\[([A-Z]+-\d{2}[A-Z]?)\]\(([^)]+)\)", row[0])
            if linked and len(row) >= 5:
                key = linked.group(1)
                if key in manifest_cards:
                    self.issue("CARTAO_DUPLICADO_MANIFESTO", key, manifest_path, line_no)
                manifest_cards[key] = {"target": linked.group(2), "modules": row[2], "deps": row[3], "line": line_no}
            elif re.fullmatch(r"(?:GATE|PG)-\d+", row[0]) and len(row) >= 4:
                if row[0] in gates:
                    self.issue("GATE_DUPLICADO", row[0], manifest_path, line_no)
                gates[row[0]] = {"condition": row[1], "evidence": row[2], "line": line_no}

        for path in sorted(prompts.rglob("*.md")):
            if path.parent == prompts or "templates" in path.parts:
                continue
            text = read_text(path)
            first = text.splitlines()[0] if text else ""
            heading = re.match(r"# ([A-Z]+-\d{2}[A-Z]?)\b", first)
            if not heading:
                if re.match(r"[A-Z]+-\d{2}", path.stem):
                    self.issue("CARTAO_SEM_ID", "Título inicial sem ID operacional", path, 1)
                continue
            key = heading.group(1)
            if key in self.cards:
                self.issue("CARTAO_DUPLICADO", key, path, 1)
            metadata = {}
            for field in ("Dependências", "Requisitos", "Módulos"):
                match = re.search(r"^- " + field + r":\s*(.+)$", text, re.MULTILINE)
                if not match:
                    self.issue("METADADO_AUSENTE", field, path)
                metadata[field] = match.group(1).rstrip(".") if match else ""
            self.cards[key] = {"path": path, "text": text, **metadata}

        declared = re.search(r"(?:Foram\s+redigidos|Existem)\s+(\d+)\s+(?:prompts|cartões)", manifest, re.IGNORECASE)
        if not declared:
            self.issue("CONTAGEM_NAO_DECLARADA", "Manifesto não declara quantidade de cartões", manifest_path)
        elif int(declared.group(1)) != len(self.cards):
            self.issue("CONTAGEM_CARTOES", f"Manifesto: {declared.group(1)}; arquivos: {len(self.cards)}", manifest_path)
        for key in sorted(set(self.cards) ^ set(manifest_cards)):
            self.issue("CARTAO_SEM_CORRESPONDENCIA", key, manifest_path)

        nodes = set(self.cards) | set(gates) | {"P00"}
        graph = {key: set() for key in nodes}
        for key, card in self.cards.items():
            try:
                deps = identifiers(card["Dependências"], NODE_RE, nodes)
            except ValueError as exc:
                self.issue("INTERVALO_DEPENDENCIA", str(exc), card["path"])
                deps = set()
            graph[key] = deps
            card["requirement_ids"] = self.checked_refs(card["Requisitos"], card["path"])
            if key not in manifest_cards:
                continue
            row = manifest_cards[key]
            expected = identifiers(row["deps"], NODE_RE, nodes)
            if deps != expected:
                self.issue("DEPENDENCIAS_DIVERGENTES", f"{key}: cartão={sorted(deps)}, manifesto={sorted(expected)}", manifest_path, row["line"])
            if (manifest_path.parent / unquote(row["target"])).resolve() != card["path"].resolve():
                self.issue("CAMINHO_CARTAO_DIVERGENTE", key, manifest_path, row["line"])
            module_re = re.compile(r"(?<![\w-])MOD-\d+(?![\w-])")
            if identifiers(row["modules"], module_re, set()) != identifiers(card["Módulos"], module_re, set()):
                self.issue("MODULOS_DIVERGENTES", key, manifest_path, row["line"])

        pg_deps = {}
        for key, gate in gates.items():
            if not key.startswith("PG-"):
                continue
            positive = []
            for clause in re.split(r";|\n", gate["condition"] + ";" + gate["evidence"]):
                exclusion = EXCLUSION_RE.search(clause)
                positive.append(clause[:exclusion.start()] if exclusion else clause)
            refs = identifiers(";".join(positive), NODE_RE, nodes)
            # Requisitos/módulos citados na condição são evidência, não nós de execução.
            refs = {ref for ref in refs if not ref.startswith(("RF-", "RN-", "RNF-", "MOD-"))}
            graph[key] = refs
            pg_deps[key] = sorted(refs)
        for key, deps in graph.items():
            for dep in sorted(deps - nodes):
                self.issue("DEPENDENCIA_INEXISTENTE", f"{key} -> {dep}", manifest_path)
        visiting = []
        done = set()

        def visit(key):
            if key in visiting:
                cycle = visiting[visiting.index(key):] + [key]
                self.issue("CICLO_DEPENDENCIAS", " -> ".join(cycle), manifest_path)
                return
            if key in done or key not in graph:
                return
            visiting.append(key)
            for dep in sorted(graph[key]):
                visit(dep)
            visiting.pop()
            done.add(key)

        for key in sorted(graph):
            visit(key)
        self.metrics.update(cartoes=len(self.cards), gates=len(gates), dependencias_marcos=pg_deps)

    def check_traceability(self):
        path = self.root / TRACE_PATH
        rows = {}
        for line_no, line in enumerate(read_text(path).splitlines(), 1):
            if not line.startswith("|"):
                continue
            row = cells(line)
            match = re.match(r"\[([A-Z]+-\d{2}[A-Z]?)\]\(([^)]+)\)", row[0])
            if not match or len(row) < 3:
                continue
            key = match.group(1)
            if key in rows:
                self.issue("RASTREABILIDADE_DUPLICADA", key, path, line_no)
            rows[key] = True
            refs = self.checked_refs(row[2], path, line_no)
            if key not in self.cards:
                self.issue("RASTREABILIDADE_SEM_CARTAO", key, path, line_no)
                continue
            card = self.cards[key]
            if refs != card.get("requirement_ids", set()):
                self.issue("RASTREABILIDADE_DIVERGENTE", f"{key}: requisitos diferem do cartão", path, line_no)
            module_re = re.compile(r"(?<![\w-])MOD-\d+(?![\w-])")
            if identifiers(row[1], module_re, set()) != identifiers(card["Módulos"], module_re, set()):
                self.issue("RASTREABILIDADE_MODULOS", key, path, line_no)
            if (path.parent / unquote(match.group(2))).resolve() != card["path"].resolve():
                self.issue("RASTREABILIDADE_CAMINHO", key, path, line_no)
        for key in sorted(set(self.cards) - set(rows)):
            self.issue("CARTAO_SEM_RASTREABILIDADE", key, path)
        self.metrics["cartoes_rastreados"] = len(rows)

    def check_materials(self):
        path = self.root / CATALOG_PATH
        catalog = json.loads(read_text(path))
        docs = catalog.get("documentos", [])
        ids = [doc["id"] for doc in docs]
        files = [doc["arquivo"] for doc in docs]
        for label, values in (("IDs", ids), ("arquivos", files)):
            if len(values) != len(set(values)):
                self.issue("CATALOGO_DUPLICADO", label, path)
        if catalog.get("quantidade_pdfs") != len(docs):
            self.issue("CATALOGO_QUANTIDADE", "Quantidade declarada difere dos documentos", path)
        pages = 0
        total_bytes = 0
        for doc in docs:
            self.catalog[doc["id"]] = doc
            page_count = doc.get("paginas_pdf")
            if type(page_count) is not int or page_count < 1:
                self.issue("CATALOGO_PAGINAS", doc["id"], path)
            else:
                pages += page_count
            source = self.local_path(doc["arquivo"], path.parent, path)
            if source:
                total_bytes += source.stat().st_size
                if source.stat().st_size != doc.get("tamanho_bytes"):
                    self.issue("PDF_TAMANHO", doc["id"], source)
                if file_hash(source) != str(doc.get("sha256", "")).lower():
                    self.issue("PDF_HASH", doc["id"], source)
                with source.open("rb") as stream:
                    if b"%PDF-" not in stream.read(1024):
                        self.issue("PDF_ASSINATURA", doc["id"], source)
            if doc.get("metadados_distribuicao"):
                metadata = self.local_path(doc["metadados_distribuicao"], path.parent, path)
                if metadata:
                    json.loads(read_text(metadata))
        if pages != catalog.get("paginas_pdf_total"):
            self.issue("CATALOGO_TOTAL_PAGINAS", "Soma de páginas declaradas divergente", path)
        actual = {item.resolve() for item in (path.parent / "documentos").glob("*.pdf")}
        listed = {(path.parent / name).resolve() for name in files}
        for extra in sorted(actual - listed):
            self.issue("PDF_SEM_CATALOGO", self.relative(extra), path)
        mer = self.root / MER_PATH
        if not mer.is_file() or file_hash(mer) != MER_SHA256:
            self.issue("MER_ORIGINAL_ALTERADO", "SHA-256 diverge da origem preservada", mer)
        self.metrics.update(pdfs_catalogados=len(docs), paginas_catalogadas=pages, bytes_pdfs=total_bytes, mer_preservado=mer.is_file() and file_hash(mer) == MER_SHA256)

    def check_preparation(self):
        """Confere referências do modelo gerado e seleção do corpus, sem serviços."""
        model_path = self.root / "docs/arquitetura/modelo-de-dados/modelo-logico.json"
        dbml_path = model_path.with_suffix(".dbml")
        model = json.loads(read_text(model_path))
        tables = model["tables"]
        names = [table["name"] for table in tables]
        if len(names) != len(set(names)):
            self.issue("MODELO_TABELA_DUPLICADA", "Nomes de tabelas repetidos", model_path)
        columns = {}
        expected_columns = {}
        expected_refs = set()
        for table in tables:
            fields = table["columns"]
            field_names = [field["name"] for field in fields]
            columns[table["name"]] = set(field_names)
            if len(field_names) != len(set(field_names)):
                self.issue("MODELO_COLUNA_DUPLICADA", table["name"], model_path)
            if not any("pk" in field.get("flags", "").split() for field in fields):
                self.issue("MODELO_SEM_PK", table["name"], model_path)
            for group in table.get("unique", []):
                if not group or not set(group).issubset(field_names):
                    self.issue("MODELO_UNICIDADE_INVALIDA", table["name"], model_path)
            expected_columns[table["name"]] = {
                field["name"]: (field["type"], frozenset(field.get("flags", "").split()))
                for field in fields
            }
            for field in fields:
                if field.get("ref"):
                    expected_refs.add((table["name"] + "." + field["name"], field["ref"]))
        for origin, target in sorted(expected_refs):
            target_table, separator, target_column = target.partition(".")
            if not separator or target_column not in columns.get(target_table, set()):
                self.issue("MODELO_REFERENCIA_INVALIDA", f"{origin} > {target}", model_path)
        # Apenas o subconjunto DBML emitido pelo modelo; o parser oficial é separado.
        dbml = read_text(dbml_path)
        blocks = re.findall(r"^Table (\w+) \{\n(.*?)^\}", dbml, re.MULTILINE | re.DOTALL)
        actual_columns = {}
        for name, body in blocks:
            fields = re.findall(r"^  ([a-z_]\w*) ([\w(),]+)(?: \[([^\]]+)\])?$", body, re.MULTILINE)
            actual_columns[name] = {
                field: (kind, frozenset(flag.strip().replace("not null", "required")
                                       for flag in flags.split(",") if flag.strip()))
                for field, kind, flags in fields
            }
        if len(blocks) != len(tables) or actual_columns != expected_columns:
            self.issue("MODELO_DBML_DIVERGENTE", "Tabelas, campos, tipos ou flags diferem do JSON", dbml_path)
        refs = re.findall(r"^Ref: (\w+\.\w+) > (\w+\.\w+)$", dbml, re.MULTILINE)
        if len(refs) != len(expected_refs) or set(refs) != expected_refs:
            self.issue("MODELO_DBML_REFERENCIAS", "Referências diferem do JSON", dbml_path)
        corpus_path = self.root / "materiais/rag/corpus-inicial.json"
        selected = json.loads(read_text(corpus_path))["documentos"]
        ids = [doc["id"] for doc in selected]
        approved = {key for key, doc in self.catalog.items() if doc.get("aprovado_para_rag") is True}
        if len(ids) != len(set(ids)) or set(ids) != approved:
            self.issue("CORPUS_SELECAO_DIVERGENTE", "Seleção inicial difere dos IDs aprovados no catálogo", corpus_path)
        for doc in selected:
            registered = self.catalog.get(doc["id"], {})
            if doc.get("sha256") != registered.get("sha256"):
                self.issue("CORPUS_HASH_DIVERGENTE", doc["id"], corpus_path)
            if not doc.get("finalidades"):
                self.issue("CORPUS_FINALIDADE_AUSENTE", doc["id"], corpus_path)
        self.metrics.update(tabelas_logicas=len(tables), colunas_logicas=sum(len(t["columns"]) for t in tables),
                            referencias_logicas=len(expected_refs), corpus_inicial=len(selected),
                            documentos_reserva=len(self.catalog) - len(approved))

    def check_cases(self):
        path = self.root / CASES_PATH
        data = json.loads(read_text(path))
        cases = data.get("casos", [])
        ids = [case["id"] for case in cases]
        if not cases or len(ids) != len(set(ids)):
            self.issue("CASOS_IDS", "Casos ausentes ou IDs duplicados", path)
        if ids:
            expected = {f"QD-{number:02d}" for number in range(1, max(int(value.split("-")[1]) for value in ids) + 1)}
            if set(ids) != expected:
                self.issue("CASOS_IDS_FALTANTES", "Numeração QD possui lacunas", path)
        if Counter(case.get("cobertura") for case in cases) != Counter(data.get("resumo", {})):
            self.issue("CASOS_RESUMO", "Classes e contagens divergem do resumo", path)
        snapshots = {}
        for doc in data.get("documentos", []):
            key = doc["id"]
            if key in snapshots:
                self.issue("CASOS_FONTE_DUPLICADA", key, path)
            snapshots[key] = doc
            source = self.catalog.get(key)
            if not source:
                self.issue("CASOS_FONTE_AUSENTE", key, path)
                continue
            if doc.get("sha256") != source.get("sha256") or doc.get("paginas_pdf") != source.get("paginas_pdf"):
                self.issue("CASOS_FONTE_DIVERGENTE", key, path)
            if doc.get("arquivo") != "materiais/rag/" + source["arquivo"]:
                self.issue("CASOS_CAMINHO_DIVERGENTE", key, path)
        references = 0
        for case in cases:
            for field in ("pergunta", "resposta_referencia", "cobertura", "limite"):
                if not isinstance(case.get(field), str) or not case[field].strip():
                    self.issue("CASO_CAMPO_AUSENTE", f"{case['id']}: {field}", path)
            if case.get("cobertura") not in data.get("legenda", {}):
                self.issue("CASO_COBERTURA", case["id"], path)
            for evidence in case.get("evidencias", []):
                source = snapshots.get(evidence.get("documento_id"))
                if not source:
                    self.issue("CASO_EVIDENCIA_SEM_FONTE", case["id"], path)
                    continue
                pages = evidence.get("paginas_pdf", [])
                if not pages or any(type(page) is not int or not 1 <= page <= source["paginas_pdf"] for page in pages):
                    self.issue("CASO_PAGINA_INVALIDA", case["id"], path)
                references += len(pages)
            for source_path in case.get("fontes_sistema", []):
                self.local_path(source_path, self.root, path)
        report_path = self.root / CASE_REPORT_PATH
        report = read_text(report_path)
        report_ids = re.findall(r"^###\s+(QD-\d+)\b", report, re.MULTILINE)
        if Counter(report_ids) != Counter(ids):
            self.issue("CASOS_RELATORIO", "IDs do relatório e JSON diferem", report_path)
        declared = re.search(r"com\s+(\d+)\s+perguntas", report, re.IGNORECASE)
        if declared and int(declared.group(1)) != len(cases):
            self.issue("CASOS_QUANTIDADE", "Quantidade declarada no relatório diverge do JSON", report_path)
        self.metrics.update(casos_documentais=len(cases), referencias_paginas=references)

    def run(self):
        for name, method in (
            ("links", self.check_links), ("requisitos", self.check_requirements),
            ("cartoes", self.check_cards), ("rastreabilidade", self.check_traceability),
            ("materiais", self.check_materials), ("preparacao", self.check_preparation),
            ("casos", self.check_cases),
        ):
            try:
                method()
            except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
                self.issue("LEITURA_OU_ESTRUTURA", f"{name}: {type(exc).__name__}: {exc}")
        return {"ok": not self.errors, "raiz": str(self.root), "verificacoes": self.metrics,
                "erros": self.errors, "avisos": self.warnings,
                "limite": "Verificação documental local; sem internet, sem escrita, sem aprovação clínica ou testes da aplicação. Páginas PDF são referências declaradas no catálogo."}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emite resultado estruturado em JSON")
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1], help="Raiz do repositório (padrão: diretório acima de scripts/)")
    args = parser.parse_args()
    result = Audit(args.root.resolve()).run()
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print("OK: documentação verificada." if result["ok"] else "FALHA: inconsistências documentais encontradas.")
        for name, value in result["verificacoes"].items():
            print(f"- {name}: {json.dumps(value, ensure_ascii=False) if isinstance(value, (dict, list)) else value}")
        for issue in result["erros"]:
            location = issue["arquivo"] + (f":{issue['linha']}" if issue["linha"] else "")
            print(f"ERRO {issue['codigo']} {location}: {issue['mensagem']}")
        print(result["limite"])
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
