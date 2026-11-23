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
A revisão `0014` cria execução, triagem, etapas e evidências de IA; `0015` entrega
mensagens de chat. A revisão `0016` normaliza as fontes de pergunta, triagem e
consumo. A revisão `0017` acrescenta CPF opcional e único ao
[cadastro de clientes](../docs/arquitetura/clientes.md). Registros anteriores
mantêm seus dados e começam com CPF nulo. O downgrade 0017 → 0016 remove
essa coluna e os CPFs preenchidos.
A revisão `0018` cria a tabela da [agenda de aulas](../docs/arquitetura/agenda.md).
O downgrade 0018 → 0017 remove a tabela e as ocorrências nela cadastradas.
Veja a [instalação do primeiro administrador](../docs/instalacao/primeiro-administrador.md).
As tabelas dos módulos seguem as migrations das suas entregas. Modelos relacionais herdam de `app.database.base.Base`.
Ao usar autogeração, importe os modelos no ambiente Alembic e revise o SQL da
nova revisão antes de aplicá-la.

Em um banco descartável com apenas a revisão inicial, `alembic -c
../database/alembic.ini downgrade base` reverte a revisão. Execute com o mesmo
`uv run --locked --env-file ../.env` e uma URL de desenvolvimento dedicada
ao ensaio. O PostgreSQL recusa remover o schema se ainda houver objetos nele.

## Transações e testes

Para preencher o ambiente de revisão manual com dados sintéticos, consulte a
[carga explícita de equipamentos e exercícios](seeds/README.md).
Ela preserva o que já foi cadastrado em desenvolvimento.

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

## Marco AI-05 — migration 0015

0014 → 0015 acrescenta conversa (PK/FK do cliente) e mensagem por turno
(entrada privada, estado, pedido congelado e versão de contexto).
Unicidade conversa/solicitação e FK composta cliente/versão impedem mistura
de contextos. Resposta fica na execução IA existente; ficha não é duplicada.
A manutenção de AI-03 remove mensagens após 90 dias e preserva recibos.
Upgrade/downgrade e comparação ORM/schema integram os testes relacionados.
MER original e migrations anteriores preservados; modelo lógico/dicionário
registram essa normalização. [Contrato](../docs/arquitetura/chat-e-adaptacao.md).

## Revisão 0016 — fontes canônicas de IA e chat

0015 → 0016 remove o marcador conversa e liga mensagem diretamente ao cliente.
Pergunta vem do pedido JSON congelado; a triagem completa permanece somente em
execucao_ia.resultado.triagem e o consumo é hidratado das colunas de etapa_ia,
sem cópias JSON redundantes. DTOs, hashes, estados, orçamento, histórico e limpeza
privada de 90 dias permanecem. FKs compostas de titularidade continuam protegidas.
[Decisão](../docs/arquitetura/decisoes/ADR-013-normalizacao-persistencia-ia-chat.md).

Após a revisão 0016, o MVP físico tinha 31 tabelas/258 colunas/51 FKs. O modelo lógico de 42 tabelas
também descreve onze tabelas futuras. Não confundir o escopo lógico completo com
objetos já instalados. Nenhuma tabela financeira ou biométrica foi antecipada.
O [relatório de migração/regressão](../docs/testes/otimizacao-modelagem-20261119.md)
registra resultados novos; testes antigos conservam sua identidade histórica.

A migration interrompe antes do descarte quando as cópias legadas de pergunta,
triagem ou consumo de etapa divergem. Não corrigir isso apagando dados ou
silenciando a validação: preservar o backup e investigar a divergência.

## Backup e restauração da revisão 0016

Antes de migrar o desenvolvimento, parar API/frontend para manter fontes e banco
compatíveis. Guardar em diretório privado fora do Git: cópia dos fontes/estado Git,
dump PostgreSQL em formato custom, hashes e manifesto sem segredos. O dump contém
dados privados, portanto não deve ser anexado à documentação ou ao repositório.

1. Com credenciais carregadas localmente, gerar dump por pg_dump em formato custom.
   Não copiar senhas ou URLs com senha para comandos públicos, logs ou histórico.
2. Conferir tamanho/hash e leitura por pg_restore --list. Restaurar o dump em um
   banco novo, isolado e dedicado à verificação; conferir a revisão Alembic e os
   dados esperados. Não usar restauração sobre o banco ativo como teste.
3. Aplicar upgrade head pelos comandos acima somente com backup verificado.
   Preservar o dump original; registrar revisão, contagens e resultado da migration.
4. Se precisar voltar, encerrar a aplicação, restaurar a cópia dos fontes
   compatíveis e o dump em banco dedicado, configurar a URL local e verificar
   antes de retomar. Não sobrescrever o banco original sem conferir o destino.

O downgrade 0016 → 0015 é exercitado em banco isolado e recompõe campos duplicados
e conversas com mensagens a partir das fontes canônicas. Para recuperação exata,
inclusive marcadores vazios anteriores, usar o backup completo. Datas, UUIDs e
conteúdo de mensagens não devem ser reconstruídos com contexto atualizado.
Os [passos/evidências desta execução](../docs/testes/otimizacao-modelagem-20261119.md)
indicam o diretório privado do backup, a verificação de restauração e os limites
do teste. O projeto não acrescenta backups privados nem scripts pontuais ao Git.
