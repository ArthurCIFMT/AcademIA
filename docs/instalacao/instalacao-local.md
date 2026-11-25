# Instalação local do AcademIA no Windows

Prepare o ambiente uma vez. Depois use [Iniciar AcademIA e Encerrar
AcademIA](iniciar-com-dois-cliques.md) na raiz do projeto.

## Pré-requisitos

| Ferramenta | Uso no projeto |
|---|---|
| Python 3.12 com Tcl/Tk | API e ambiente `backend/.venv`. O painel de dois cliques usa Tkinter. |
| uv | Instala e verifica as dependências Python registradas em `backend/uv.lock`. |
| Node.js 24 LTS e npm 11 | O Node executa o frontend. O projeto registra npm 11.6.2 em `frontend/package.json` e usa `package-lock.json` para instalar as dependências. |
| PostgreSQL 17 nativo | Bancos `academia_dev` e `academia_test`, com usuários próprios, no loopback. |
| Mailpit nativo para Windows | SMTP e caixa web de teste, ambos locais. |

## Preparação inicial

1. Na raiz, copie `.env.example` para `.env` e
   `iniciador.local.example.json` para `iniciador.local.json`. Em `frontend/`,
   copie `.env.example` para `.env.local`. Preserve os arquivos privados que
   já existirem. Informe no JSON os quatro caminhos de ferramentas e do
   cluster inicializado. Ele deve apontar à pasta que contém `PG_VERSION`.
2. Instale as dependências com os lockfiles, seguindo a seção
   [Dependências e build](#dependências-e-build). A instalação em uma
   máquina nova pode requerer acesso aos repositórios de pacotes.
3. Com o PostgreSQL aberto em loopback, crie os bancos e preencha as URLs
   privadas seguindo o [guia do banco](../../database/README.md). Em
   `backend/`, siga a seção [Migrations](#migrations). Para atualizar um
   ambiente que já tem dados, encerre a aplicação e guarde um backup.
4. Crie o [primeiro administrador](primeiro-administrador.md). Para a
   demonstração, carregue o [catálogo sintético](../../database/seeds/README.md)
   em uma operação própria. Para usar as funções de IA, prepare os pesos e o
   [corpus RAG](preparar-rag-local.md) com a API parada e configure o perfil de
   provedor no `.env` privado.
5. Dê dois cliques em `Iniciar AcademIA.cmd`. O painel inicia os serviços
   preparados e abre o site. Convites e recuperação aparecem na caixa local
   do Mailpit. As integrações da [catraca fictícia](catraca-ficticia.md) e do
   [CompreFace](../arquitetura/preparacao-gate-08.md) têm preparação própria.

## Dependências e build

```powershell
# Em backend/
uv sync --locked

# Em frontend/
npm ci
npm run build
```

## Migrations

Com o PostgreSQL ativo e o `.env` configurado, execute em `backend/`:

```powershell
uv run --locked --env-file ../.env alembic -c ../database/alembic.ini upgrade head
uv run --locked --env-file ../.env alembic -c ../database/alembic.ini current
```

A abertura diária usa as dependências instaladas e confere a revisão do
PostgreSQL antes de iniciar a API. Migrations, carga de exemplo e preparo do
corpus são etapas explícitas. Configure os caminhos do PostgreSQL, do Node e
do Mailpit no JSON privado. Credenciais ficam apenas no `.env` do backend.
Os arquivos privados, os ambientes, os backups, a caixa de e-mail e os dados
locais estão excluídos pelo Git.

## Verificação em uma instalação limpa

Use outra pasta com os fontes da revisão que deseja demonstrar, sem copiar
`.venv`, `node_modules`, dados ou configuração privada de outra instalação.
Em um cluster PostgreSQL novo, mantenha bancos e usuários próprios para
`academia_dev` e `academia_test`. O último deve começar vazio e pode ficar
no mesmo cluster. Ao testar na mesma máquina, feche a instalação anterior
e use uma porta livre para o cluster novo. Preencha os arquivos privados
a partir dos exemplos.

1. Execute [a instalação dos lockfiles](#dependências-e-build). Aplique
   `upgrade head` em `academia_dev`, confira `current` e repita o
   `upgrade head`. A segunda execução deve manter a revisão e as estruturas.
2. Crie o [administrador](primeiro-administrador.md) e carregue o
   [catálogo de exemplo](../../database/seeds/README.md) explicitamente.
   Se usar a catraca fictícia, prepare seu armazenamento antes de abrir o
   iniciador. [Configuração da catraca](catraca-ficticia.md).
3. Abra o iniciador e confira o site, `/api/health` pelo proxy e o login.
   Encerre, abra novamente e confira a mesma conta e o catálogo. As etapas
   de [prontidão](#comunicação-e-prontidão-local) indicam os endereços.
4. Encerre os serviços do iniciador antes de rodar os ensaios com
   `academia_test` e uma caixa Mailpit de teste. A regressão no Edge usa
   cenários sintéticos para o LLM e o reconhecimento facial.
   [Aceitação do MVP e seus limites](../testes/aceitacao-mvp.md).

[Comandos e evidências da instalação limpa](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado).

## Verificação básica da API

Na pasta `backend/`, com configuração local e porta 8000 livre, execute:

```powershell
uv run --locked --env-file ../.env uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log
```

De outro terminal, consulte os endpoints e use Ctrl+C no terminal da API para
encerrar. O exemplo de ambiente também serve para conferir a inicialização
e as rotas técnicas. Use a configuração com PostgreSQL para verificar rotas
que dependem da sessão.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
(Invoke-RestMethod http://127.0.0.1:8000/openapi.json).info.title
```

O primeiro comando retorna `status=ok` e o segundo retorna `AcademIA` com
o nome padrão. O [registro de testes](../testes/comandos.md) reúne os comandos
e resultados de instalação, build e inicialização.

## Comunicação e prontidão local

Com a configuração de exemplo, os serviços usam estes endereços no mesmo PC.
Antes de iniciar, mantenha livres as portas do site, da API, do Mailpit e da
catraca, se habilitada. O painel pode reutilizar o PostgreSQL já aberto e
preserva esse processo ao encerrar.

| Serviço | Verificação no endereço padrão |
|---|---|
| Site e proxy | `http://127.0.0.1:5173/` abre a interface. `/api/health` no mesmo endereço confirma o proxy para a API. |
| API | `http://127.0.0.1:8000/health` retorna `status=ok`. |
| PostgreSQL | Porta `5432`. O painel verifica a conexão ao `academia_dev` e a revisão das migrations antes de abrir a API. |
| Mailpit | SMTP na porta `1025` e caixa de entrada em `http://127.0.0.1:8025/`. |
| Catraca fictícia | `http://127.0.0.1:8011/health` após a [configuração da simulação](catraca-ficticia.md). A API envia comandos e recebe confirmações em loopback. |
| Qdrant | O único processo da API abre o índice sob demanda em `ACADEMIA_VECTOR_PATH`, por padrão `backend/data/qdrant`. O diretório deve ser exclusivo do processo durante o uso. |

O endpoint `/health` confirma que a API responde. A prontidão do corpus
depende do [preparo do RAG](preparar-rag-local.md). Encerre a API antes de
rodar a CLI ou preparar o índice no mesmo diretório.

O [ensaio INF-02](../testes/comandos.md#inf-02--comunicação-e-prontidão-dos-serviços-locais)
registra verificações de inicialização, envio SMTP, retorno da catraca,
persistência do Qdrant e encerramento.

## Segurança e persistência locais

### Rede e firewall

- Use os [endereços de loopback acima](#comunicação-e-prontidão-local). O
  iniciador vincula o PostgreSQL que abre a `127.0.0.1`. Antes de reutilizar
  um servidor preexistente, verifica se ele está configurado para ouvir
  somente em loopback. Para início manual do banco, configure
  `listen_addresses = '127.0.0.1'` e autenticação local por senha
  (`scram-sha-256` no `pg_hba.conf`). Use contas sem privilégios
  administrativos e mantenha desenvolvimento e testes separados.
- Mantenha o firewall do Windows ativo e com conexões de entrada não
  solicitadas bloqueadas. As portas locais do AcademIA dispensam exceções de
  entrada, redirecionamento de portas e túneis. A aplicação usa um proxy
  local de mesma origem, com sessões e permissões validadas pelo backend.
  Mantenha as rotas de administração e curadoria sujeitas a suas
  [permissões e configurações](../arquitetura/autorizacao.md).
- O Qdrant local dispensa porta HTTP própria. O CompreFace publica apenas
  `127.0.0.1:18080` e mantém seu banco na rede interna do Docker dedicado.
  A administração dessa instância é feita localmente pelo responsável técnico.
  [Configuração do CompreFace](../arquitetura/preparacao-gate-08.md#execução-local-da-instância-dedicada).

Para conferir o host sem alterar regras, use `netsh advfirewall show
allprofiles state` e `netstat -ano` com o sistema aberto. Confira os
endereços **locais** na coluna de escuta das portas do projeto. `127.0.0.1`
e `::1` são loopback. `0.0.0.0` e `[::]` indicam escuta em todas as
interfaces. As regras do Windows são administradas fora do iniciador.

### Dados que sobrevivem à reinicialização

| Dados | Local padrão ou fonte da configuração |
|---|---|
| PostgreSQL | Cluster indicado por `postgres_data` em `iniciador.local.json`. Mantenha o `academia_dev` e suas migrations. |
| Qdrant, corpus e extrações | Caminhos `ACADEMIA_VECTOR_PATH`, `ACADEMIA_CORPUS_DIR` e `ACADEMIA_EXTRACTION_DIR` sob `backend/` quando relativos. |
| Mailpit e catraca | `backend/data/mailpit.db` e o arquivo `ACADEMIA_TURNSTILE_STORE_PATH`, relativo à raiz quando o caminho é relativo. |
| Equipamentos | `ACADEMIA_EQUIPMENT_IMAGES_DIR` sob `backend/` quando relativo. A pasta é usada quando houver imagem cadastrada. |
| CompreFace | Volume persistente do projeto Docker dedicado. Referências no PostgreSQL dependem do mesmo conjunto facial e da configuração correspondente. |

Guarde `.env`, a configuração privada, os diretórios e os backups em
locais restritos às contas que precisam acessá-los. Use as ACLs do Windows
para revisar esse acesso. O Git ignora os caminhos locais padrão.

### Backup e restauração

1. Registre a revisão do código, a revisão Alembic, a coleção do Qdrant e a
   revisão do modelo de embeddings. Encerre o iniciador e as ferramentas de
   ingestão ou manutenção. Para o dump, deixe ativo apenas o PostgreSQL.
   Trabalhe em uma pasta privada fora do Git.
2. Use os executáveis da mesma instalação do PostgreSQL. Substitua a pasta
   do exemplo por uma pasta privada existente e ajuste portas/usuário ao seu
   ambiente. Informe a senha somente quando o programa solicitar.

   ```powershell
   $arquivoAcademia = 'C:\backups-privados\academia-dev.dump'
   pg_dump --host 127.0.0.1 --port 5432 --username academia_dev_app --format custom --file $arquivoAcademia academia_dev
   pg_restore --list $arquivoAcademia
   Get-FileHash -LiteralPath $arquivoAcademia -Algorithm SHA256
   ```

   Confira o código de saída de cada comando. Guarde o hash junto ao
   inventário privado do backup.
3. Com os serviços correspondentes parados, copie o diretório inteiro do
   Qdrant, os diretórios de corpus/extrações e os arquivos de uploads,
   Mailpit e catraca. Inclua a configuração privada com acesso restrito.
   Se usar reconhecimento facial, preserve separadamente o volume e a
   configuração do CompreFace da mesma instalação.
4. Teste o dump em um banco **novo e vazio** com proprietário próprio. O
   comando a seguir usa um banco de verificação previamente criado.
   `--no-owner` atribui os objetos ao usuário que executa a restauração.

   ```powershell
   pg_restore --host 127.0.0.1 --port 5432 --username academia_dev_app --exit-on-error --no-owner --dbname academia_restore $arquivoAcademia
   ```

   Compare a revisão Alembic, o catálogo e os identificadores de referência.
   O runtime exige o nome `academia_dev`. Para testar a aplicação com uma
   restauração integral, use essa base num cluster separado, com a origem
   e o proxy configurados para a instalação de recuperação.
5. Restaure Qdrant e arquivos em **outro diretório** e confira hashes e
   referências. Com a API parada, use a
   [verificação do Qdrant](../arquitetura/banco-vetorial.md#execução-e-verificação-local)
   apontando `ACADEMIA_VECTOR_PATH` para a cópia. Compare a coleção, o
   espaço de embeddings e a contagem de pontos. Confira o acervo e os
   arquivos antes de abrir a instalação recuperada. Preserve o original
   enquanto valida a cópia.

[Procedimento de referência do banco](../../database/README.md#backup-e-restauração-da-revisão-0016).

### Diagnóstico de prontidão

No início, o painel verifica o PostgreSQL e a revisão Alembic antes de abrir
a API. Um problema de conexão, exposição ou migrations aparece nessa etapa.
As sondagens HTTP seguintes cobrem Mailpit, API, catraca configurada e o
proxy do site. Os registros ficam em `backend/data/iniciador`.

`/health` indica que a API responde. O Qdrant abre sob demanda e suas
falhas aparecem no fluxo de IA ou na verificação offline. A catraca
fictícia pode responder enquanto o CompreFace está desligado. A verificação
facial usa o [procedimento próprio](../arquitetura/preparacao-gate-08.md).

[Evidências do INF-03](../testes/comandos.md#inf-03--segurança-e-persistência-locais).
