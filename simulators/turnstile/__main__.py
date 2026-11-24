import argparse
from sqlite3 import Error as StoreError
from urllib.parse import urlsplit

import uvicorn
from pydantic import ValidationError

from simulators.turnstile.contracts import Settings
from simulators.turnstile.http import create_app
from simulators.turnstile.store import Store


def main() -> None:
    parser = argparse.ArgumentParser(description="Catraca fictícia do AcademIA")
    parser.add_argument(
        "--prepare", action="store_true", help="preparar o arquivo local"
    )
    args = parser.parse_args()
    try:
        settings = Settings()
        if args.prepare:
            Store(settings.store_path).prepare()
            print("Armazenamento da catraca fictícia pronto.")
            return
        app = create_app(settings)
    except (ValidationError, StoreError, ValueError):
        parser.exit(1, "Confira o ambiente privado e a preparação do simulador.\n")
    port = urlsplit(settings.url).port
    assert port is not None
    uvicorn.run(app, host="127.0.0.1", port=port, access_log=False)


if __name__ == "__main__":
    main()
