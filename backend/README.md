# Backend do AcademIA

O FastAPI é montado por `app.main:create_app`. `app/core/` contém a configuração
e a rota técnica. A fábrica valida `ACADEMIA_APP_NAME` na inicialização e usa
seu valor como título da documentação OpenAPI.

## Execução local

Com [uv](https://docs.astral.sh/uv/getting-started/installation/) e Python 3.12
disponíveis, execute a partir da raiz do repositório:

```powershell
Set-Location backend
uv sync --locked
uv run --locked --env-file ../.env.example uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

O exemplo fornece o nome padrão. Para usar configuração local própria, copie
`.env.example` para `.env` na raiz e troque a opção para `--env-file ../.env`.
A aplicação lê as variáveis do processo. Nome ausente ou em branco interrompe
a inicialização com erro de validação.

- `GET /health` responde HTTP 200 com JSON `{"status":"ok"}` quando a API atende requisições.
- A documentação interativa está em <http://127.0.0.1:8000/docs>.
- O contrato gerado está em <http://127.0.0.1:8000/openapi.json>.

Os erros seguem o [contrato REST](../docs/arquitetura/contratos-rest.md). A
inicialização acima desabilita o log bruto de acesso do Uvicorn.

## Verificações

A partir de `backend/`:

```powershell
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

`uv.lock` fixa versões diretas e transitivas. Uvicorn executa a API e
Pydantic Settings valida o ambiente. Pytest e HTTPX exercitam a aplicação,
enquanto Ruff e mypy verificam estilo e tipos.
