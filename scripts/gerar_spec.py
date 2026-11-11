#!/usr/bin/env python3
"""Monta/verifica o SPEC portátil a partir de fontes versionadas, sem rede."""

from __future__ import annotations

import argparse
import hashlib
import json
import posixpath
import re
import sys
from pathlib import Path
from urllib.parse import urlsplit

CONFIG_PATH = "docs/especificacao/compilacao-spec.json"
INLINE_LINK = re.compile(r"(!?\[[^\]\n]*\]\()([^\s)]+)(\))")


def read_source(root: Path, name: str, hashes: dict[str, str]) -> str:
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts or name == "SPEC.md":
        raise ValueError(f"Fonte fora do escopo: {name}")
    allowed = relative.suffix in {".md", ".json", ".dbml", ".toml", ".py"}
    if not allowed and name not in {".env.example", "frontend/.env.example"}:
        raise ValueError(f"Tipo de fonte não permitido: {name}")
    resolved = (root / relative).resolve()
    resolved.relative_to(root.resolve())
    text = resolved.read_text(encoding="utf-8-sig").replace("\r\n", "\n")
    hashes[name] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return text


def root_target(target: str, source: str) -> str:
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc or target.startswith("#"):
        return target if not target.startswith("#") else source + target
    path = posixpath.normpath(posixpath.join(posixpath.dirname(source), parsed.path))
    if path.startswith("../") or path.startswith("/"):
        raise ValueError(f"Link local fora do projeto em {source}")
    return (
        path
        + ("?" + parsed.query if parsed.query else "")
        + ("#" + parsed.fragment if parsed.fragment else "")
    )


def markdown(text: str, source: str, *, overview: bool = False) -> str:
    output = []
    fence: str | None = None
    removed_title = False
    for line in text.splitlines():
        marker = re.match(r"^\s*(`{3,}|~{3,})", line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            output.append(line)
            continue
        if fence is not None:
            output.append(line)
            continue
        if not overview and not removed_title and line.startswith("# "):
            removed_title = True
            continue
        heading = re.match(r"^(#{1,6})\s+", line)
        if heading and not overview:
            line = (
                "#" * min(6, len(heading.group(1)) + 2) + line[len(heading.group(1)) :]
            )
        line = INLINE_LINK.sub(
            lambda match: (
                match.group(1)
                + (
                    match.group(2)
                    if overview and match.group(2).startswith("#")
                    else root_target(match.group(2), source)
                )
                + match.group(3)
            ),
            line,
        )
        output.append(line)
    if fence is not None:
        raise ValueError(f"Bloco de código não fechado em {source}")
    return "\n".join(output).strip()


def clipped(text: str, part: dict[str, object]) -> str:
    start = part.get("inicio")
    end = part.get("fim")
    if start:
        if str(start) not in text:
            raise ValueError(f"Marcador inicial ausente: {start}")
        text = text[text.index(str(start)) :]
    if end:
        if str(end) not in text:
            raise ValueError(f"Marcador final ausente: {end}")
        text = text[: text.index(str(end))]
    return text


def slug(title: str) -> str:
    return re.sub(r"\s+", "-", re.sub(r"[^\w\s-]", "", title.lower()).strip())


def build(root: Path) -> tuple[str, int]:
    hashes: dict[str, str] = {}
    config = json.loads(read_source(root, CONFIG_PATH, hashes))
    read_source(root, "scripts/gerar_spec.py", hashes)
    overview = markdown(
        read_source(root, config["visao_geral"], hashes),
        config["visao_geral"],
        overview=True,
    )
    # O resumo foi escrito com destinos relativos à raiz para a saída portátil.
    sections = config["secoes"]
    navigation = [
        "## Navegação do documento completo",
        "",
        "Visão geral e coordenação: capítulos 1–11.",
        "",
    ]
    navigation += [
        f"- [{item['titulo']}](#{slug(item['titulo'])})" for item in sections
    ]
    navigation += ["- [Fontes e integridade](#fontes-e-integridade)", ""]
    if overview.count("<!-- SUMARIO_SPEC -->") != 1:
        raise ValueError("Resumo precisa de exatamente um marcador de sumário")
    overview = overview.replace("<!-- SUMARIO_SPEC -->", "\n".join(navigation))
    output = [
        "<!-- Gerado por python scripts/gerar_spec.py --write. "
        "Edite as fontes versionadas; use --check para detectar divergência. -->",
        overview.rstrip(),
    ]
    for section in sections:
        output += ["", "## " + section["titulo"], ""]
        if section.get("nota"):
            output += [section["nota"], ""]
        for index, part in enumerate(section["fontes"], 1):
            name = part["arquivo"]
            text = clipped(read_source(root, name, hashes), part)
            output += [
                f"### {index}. {part['titulo']}",
                "",
                f"Fonte versionada: [{name}]({name}).",
                "",
            ]
            kind = part.get("tipo", "markdown")
            if kind == "markdown":
                output.append(markdown(text, name))
            elif kind == "codigo":
                language = part.get("linguagem", "")
                output += ["````" + language, text.rstrip(), "````"]
            elif kind == "corpus":
                selection_name = part["selecao"]
                selection = json.loads(read_source(root, selection_name, hashes))
                catalog = json.loads(text)
                selected = {item["id"]: item for item in selection["documentos"]}
                documents = [
                    item for item in catalog["documentos"] if item["id"] in selected
                ]
                if len(documents) != len(selected) or any(
                    item["sha256"] != selected[item["id"]]["sha256"]
                    for item in documents
                ):
                    raise ValueError("Seleção inicial e catálogo divergem")
                payload = {"selecao": selection, "documentos_selecionados": documents}
                output += [
                    "````json",
                    json.dumps(payload, ensure_ascii=False, indent=2),
                    "````",
                ]
            else:
                raise ValueError(f"Tipo de inclusão desconhecido: {kind}")
    output += [
        "",
        "## Fontes e integridade",
        "",
        "Instantâneo composto por fontes locais versionadas, com SHA-256 do texto",
        "UTF-8 após normalização de quebras de linha. Não contém credenciais reais,",
        "pesos de modelos nem arquivos PDF/imagem. Links são navegação/proveniência;",
        "as especificações essenciais selecionadas estão incorporadas neste arquivo.",
        "",
        "| Fonte | SHA-256 |",
        "|---|---|",
    ]
    output += [f"| `{name}` | `{digest}` |" for name, digest in sorted(hashes.items())]
    output += [
        "",
        "Manutenção no projeto: `python scripts/gerar_spec.py --write` atualiza",
        "a cópia completa; `python scripts/gerar_spec.py --check` verifica",
        "equivalência sem escrever.",
        "Atualize fontes e cópia no mesmo commit. Para transporte,",
        "entregue SPEC.md; para reprodução exata do código, forneça o repositório",
        "no commit desejado, lockfiles, recursos externos e configuração local.",
        "",
    ]
    return "\n".join(output), len(hashes)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true", help="Atualiza somente SPEC.md")
    mode.add_argument("--check", action="store_true", help="Verifica sem escrever")
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[1]
    )
    args = parser.parse_args()
    try:
        content, count = build(args.root)
        target = args.root / "SPEC.md"
        if args.check:
            if (
                not target.is_file()
                or target.read_text(encoding="utf-8-sig") != content
            ):
                print(
                    "ERRO: SPEC.md desatualizado; execute gerar_spec.py --write.",
                    file=sys.stderr,
                )
                return 1
            print(f"OK: SPEC.md corresponde a {count} fontes versionadas.")
        else:
            with target.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(content)
            size = len(content.encode("utf-8"))
            print(f"OK: SPEC.md gerado de {count} fontes; {size} bytes.")
        return 0
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"ERRO: não foi possível compilar o SPEC ({error}).", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
