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

## Banco vetorial local

A conexão Qdrant usa um único processo e diretório persistente separado do
PostgreSQL. Após uv sync --locked, com a API parada, execute a partir de backend/:

```powershell
uv run --locked --env-file ../.env python -m app.modules.knowledge.vector
```

O [guia vetorial](../docs/arquitetura/banco-vetorial.md) descreve configuração,
coleção versionada, persistência, falhas e exclusão entre processos. Não é
necessário instalar um servidor nem Docker. A API fecha a conexão no shutdown;
suas rotas manuais não dependem de abrir o índice. A [extração offline](../docs/arquitetura/extracao-documental.md)
já oferece serviço interno com proveniência e registro privado de estados.
Indexação e busca serão implementadas nos cartões seguintes.
