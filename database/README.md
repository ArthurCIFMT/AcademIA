# Banco do AcademIA

## PostgreSQL local

Use PostgreSQL 17 nativo no Windows, em `127.0.0.1:5432`. Crie os bancos
`academia_dev` e `academia_test` com proprietários distintos. Na sessão
administrativa do `psql`, conectada ao banco `postgres`, execute:

```sql
CREATE ROLE academia_dev_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
CREATE ROLE academia_test_app LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE;
\password academia_dev_app
\password academia_test_app
CREATE DATABASE academia_dev OWNER academia_dev_app;
CREATE DATABASE academia_test OWNER academia_test_app;
REVOKE CONNECT ON DATABASE academia_dev FROM PUBLIC;
REVOKE CONNECT ON DATABASE academia_test FROM PUBLIC;
```

Copie `.env.example` para `.env` na raiz e preencha cada URL no formato
`postgresql+psycopg://usuario:senha@127.0.0.1:5432/nome_do_banco`.
Use o respectivo proprietário e codifique caracteres reservados da senha
como percent encoding. As duas variáveis são `ACADEMIA_DATABASE_URL` e
`ACADEMIA_TEST_DATABASE_URL`. O arquivo local `.env` fica fora do Git.

## Migrations

A partir de `backend/`, com Python 3.12 e uv:

```powershell
uv sync --locked
uv run --locked --env-file ../.env alembic -c ../database/alembic.ini upgrade head
uv run --locked --env-file ../.env alembic -c ../database/alembic.ini current
```

A revisão `0001` cria o schema `academia`. A revisão `0002` cria
as tabelas de [auditoria e eventos](../docs/arquitetura/auditoria-e-eventos.md).
A revisão `0003` cria usuários, papéis, perfis, sessões e tokens de acesso.
A revisão `0004` cria [notificações](../docs/arquitetura/notificacoes.md) e estados de entrega.
A revisão `0005` cria [designações](../docs/arquitetura/designacoes.md) e seu histórico.
A revisão `0006` cria [versões de onboarding e avaliações](../docs/arquitetura/onboarding.md).
A revisão `0007` cria os [convites e sessões restritas](../docs/arquitetura/onboarding.md#convite-inicial-e-sessão-restrita).
A revisão `0008` cria o [inventário de equipamentos](../docs/arquitetura/equipamentos.md).
A revisão `0009` cria o [catálogo de exercícios](../docs/arquitetura/catalogo-exercicios.md).
A revisão `0010` cria as [fichas manuais e invariantes de versões](../docs/arquitetura/fichas-manuais.md).
A revisão `0011` registra a [validação de publicação e os pareceres imutáveis](../docs/arquitetura/publicacao-e-parecer.md).
A revisão `0012` cria [documentos, versões e decisões de curadoria](../docs/arquitetura/corpus.md), com proveniência protegida.
A revisão `0013` cria [ingestões, fragmentos e checkpoints de indexação](../docs/arquitetura/indexacao-documental.md), com proveniência imutável e ativação completa.
Veja a [instalação do primeiro administrador](../docs/instalacao/primeiro-administrador.md).
As tabelas dos módulos seguem as migrations das suas entregas. Modelos relacionais herdam de `app.database.base.Base`.
Ao usar autogeração, importe os modelos no ambiente Alembic e revise o SQL da
nova revisão antes de aplicá-la.

Em um banco descartável com apenas a revisão inicial, `alembic -c
../database/alembic.ini downgrade base` reverte a revisão. Execute com o mesmo
`uv run --locked --env-file ../.env` e uma URL de desenvolvimento dedicada
ao ensaio. O PostgreSQL recusa remover o schema se ainda houver objetos nele.

## Transações e testes

Crie o engine uma vez por processo. A fábrica de sessões usa
`with sessions.begin() as session` para confirmar a unidade de trabalho ao
sair normalmente ou desfazê-la se houver exceção. As conexões usam UTC.

Use um `academia_test` dedicado e vazio. As fixtures verificam o nome do banco
na conexão e revertem a transação externa, inclusive o DDL. As sessões nos
testes usam savepoints dentro dessa transação.

```powershell
uv run --locked --env-file ../.env pytest -m database
uv run --locked --env-file ../.env pytest -m integration
```

[Comandos de verificação](../docs/testes/comandos.md) · [Binários PostgreSQL para Windows](https://www.enterprisedb.com/download-postgresql-binaries)

## Marco AI-03 — migration 0014

Acrescenta execucao_ia, triagem, etapa_ia e evidencia_execucao; constraints de
idempotência, contexto e consumo, índices e explicacao expurgável da versao_ficha.
[Contrato](../docs/arquitetura/geracao-persistente.md). Nenhuma migration anterior
foi alterada. Upgrade/downgrade e comparação ORM/schema são testados em PostgreSQL.
