import hashlib
import json
from pathlib import Path

from huggingface_hub import snapshot_download

from app.modules.knowledge.embeddings.settings import FILES, EmbeddingSettings


def provision(settings: EmbeddingSettings) -> None:
    root = settings.path.resolve()
    root.mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=settings.model,
        revision=settings.revision,
        local_dir=root,
        allow_patterns=list(FILES),
        token=False,
        max_workers=2,
    )
    files = {
        name: hashlib.sha256((root / name).read_bytes()).hexdigest() for name in FILES
    }
    (root / "academia-model.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "model": settings.model,
                "revision": settings.revision,
                "files": files,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def verify(settings: EmbeddingSettings, *, full: bool = False) -> Path:
    root = settings.path.resolve()
    manifest = json.loads((root / "academia-model.json").read_text(encoding="utf-8"))
    if (
        manifest["model"] != settings.model
        or manifest["revision"] != settings.revision
        or set(manifest["files"]) != set(FILES)
    ):
        raise ValueError("Pesos incompatíveis.")
    for name in FILES:
        if not (root / name).is_file():
            raise ValueError("Pesos ausentes.")
        if (
            full
            and hashlib.sha256((root / name).read_bytes()).hexdigest()
            != manifest["files"][name]
        ):
            raise ValueError("Pesos alterados.")
    return root


if __name__ == "__main__":
    provision(EmbeddingSettings())
    print('{"status":"OK","modelo":"E5-small","dimensao":384}')
