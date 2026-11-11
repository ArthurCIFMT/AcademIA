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
RAG-04 entrega [chunking e indexação com E5 CPU](../docs/arquitetura/indexacao-documental.md).
RAG-05 entrega [recuperação semântica/citações](../docs/arquitetura/recuperacao-semantica.md),
sem LLM; geração/triagem/chat serão integrados pelos cartões AI.

## Embeddings e indexação offline

Com `.env` configurado, migration 0013 aplicada e a API parada, em `backend/`:

```powershell
uv sync --locked
uv run --locked --env-file ../.env python -m app.modules.knowledge.embeddings.provision
uv run --locked --env-file ../.env python -m app.modules.knowledge.ingestion --actor UUID_CURADOR --version UUID_VERSAO --selection CAMINHO_JSON
```

O provisionamento obtém os pesos fixados do E5 (internet, aproximadamente 470 MB),
sem chave de LLM. A inferência depois é local CPU/offline. Pesos ficam em
`backend/models/multilingual-e5-small` e fora do Git; configure caminho absoluto
por ACADEMIA_EMBEDDING_PATH se necessário. Modelo e SHA-256 estão no
[manifesto](../docs/requisitos/schemas/embedding-e5-v1.json).

A seleção JSON segue o [schema](../docs/requisitos/schemas/selecao-indexacao-v1.schema.json)
e usa offsets do artefato extraído, não texto copiado manualmente do PDF. Exige
curador administrador ativo e versão aprovada. Não indexar páginas com qualidade
pendente. Um único processo por diretório Qdrant; manutenção e API não abrem o
mesmo diretório simultaneamente. A coleção v2 preserva a v1 sem revisão de pesos.
O guia detalha retomada, falhas e quatro documentos ainda pendentes de extração.

## Recuperação técnica local

Com .env configurado, modelo provisionado e API parada, em backend/:

~~~powershell
uv run --locked --env-file ../.env python -m app.modules.knowledge.retrieval --request CAMINHO_JSON
~~~

Entrada segue o [schema](../docs/requisitos/schemas/recuperacao-v1.schema.json).
contexto_id é um UUID do contexto autorizado; em futura rota pública o backend
deve resolvê-lo pela sessão. A CLI é ferramenta do operador local e não substitui
a autorização REST. Coleção vazia resulta em SEM_EVIDENCIAS. Não há chamada LLM.
O guia detalha aprovação/revogação, saúde, cache e inicialização fria do modelo.

## Preparação de triagem

AI-01 entrega GET /api/v1/ia/triagem/preparacao para cliente autenticado, usando
o snapshot próprio mais recente, sem body ou seleção de outro titular. O
[contrato](../docs/arquitetura/triagem-academica.md) descreve estados, códigos,
limites e revalidação. A resposta não inclui anamnese ou resumo completo.
Sem adaptador LLM (AI-02), caso não bloqueado fica AGUARDANDO_ANALISE, sem geração
permitida. O serviço interno já recebe porta assistida tipada para composição;
não habilitar doubles por variável de ambiente ou entrada do cliente.

## Orquestrador fixo AI-02

[Contrato e limites](../docs/arquitetura/orquestracao-ia.md). Schemas e prompts
versionados, adaptador HTTP Groq e pontes de contexto/RAG estão implementados.
A composição exige StatePort explícito, implementado com PostgreSQL no AI-03.
Não há armazenamento volátil de produção; a API de execução está descrita abaixo.
GET de preparação continua sem LLM. Testes AI-02 usam MockTransport, sem chave
pessoal/rede Groq; qualidade e latência reais serão avaliadas em AI-06.
HTTPX passou de dependência de teste a runtime, sem alterar sua versão.

## Geração persistente AI-03

[Contrato, rotas e limites](../docs/arquitetura/geracao-persistente.md). Aplicar
a migration 0014 conforme database/README.md. POST autenticado em
/api/v1/ia/fichas/execucoes, com solicitacao_id UUID e CSRF, gera para o titular.
GET/DELETE da própria solicitação consultam/cancelam sem repetir LLM.
Publicação cria origem IA/parecer PENDENTE e aplica retenção pelo MOD-04.
Requer configuração local do corpus/embeddings e GROQ_API_KEY para uso real;
sem evidência pertinente, abster-se. Sem tela nova até AI-04. Testes controlados
não representam aceite de qualidade/latência da Groq, que permanece em AI-06.
