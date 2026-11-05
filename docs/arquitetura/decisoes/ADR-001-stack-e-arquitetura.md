# ADR-001 — Stack e arquitetura

Status: ACEITA
Data: 2026-11-04
Origem: responsável delegou a seleção de frameworks, campos e regras técnicas;
academia única foi escolhida expressamente. Escolhas registradas sem exigir nova aprovação.

Decisão: monólito modular em Python 3.12, FastAPI, Pydantic 2, SQLAlchemy 2.x,
Alembic e psycopg 3; uv para ambiente/lockfile; Ruff e mypy; pytest + HTTPX.
Frontend: Node 24 LTS, npm, React + TypeScript estrito + Vite, React Router,
React Hook Form + Zod para formulários; Vitest/Testing Library e Playwright.
Fixar versões exatas compatíveis nos lockfiles durante FND-04/FND-07; não instalar
nada nem inventar comandos de teste executados nesta preparação documental.

Módulos se comunicam por interfaces de aplicação tipadas. REST/eventos usam JSON
versionado. Repositórios internos não são compartilhados. Um processo backend no
MVP; acesso ao banco por unidade de trabalho curta. Chamadas LLM não mantêm transação.
HTTPX async para integrações; serviços SQLAlchemy síncronos executados sem bloquear
o event loop. Sem broker/Redis/LangChain/LangGraph obrigatórios.

Pedidos de geração: POST aceita pedido idempotente e devolve 202 + ID; trabalho
durável em PostgreSQL, consumidor no processo da aplicação e consulta de estado.
Reinício com etapa LLM em andamento deixa tentativa INTERROMPIDA, sem replay
automático dessa etapa. Nova tentativa é explícita, novo ID. Publicação única.
Outbox para avisos duráveis; notificação idempotente por evento/destinatário.

Alternativas: Django (mais componentes prontos, menos alinhado à API proposta),
Flask (mais montagem manual), microserviços (complexidade desnecessária).
Escolha privilegia separação didática e contratos explícitos.
Fontes: [FastAPI](https://fastapi.tiangolo.com/),
[SQLAlchemy](https://docs.sqlalchemy.org/en/20/),
[uv](https://docs.astral.sh/uv/), [Vite](https://vite.dev/guide/).
