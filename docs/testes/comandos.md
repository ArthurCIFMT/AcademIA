# Registro de comandos de verificação

BE, DB e INT cobrem a base do backend e do banco. DOC verifica os artefatos
do repositório. As demais suites serão configuradas nos prompts indicados.
As siglas são referências para os prompts e não devem ser executadas no terminal.
Suíte significa conjunto organizado de testes. IA inclui dúvidas, resumo/triagem e geração LLM;
RAG verifica ferramentas/recuperação sem exigir o orquestrador LLM.

| Suite | Estado | Prompt que registra o comando real |
|---|---|---|
| DOC | `python scripts/verificar_documentacao.py` na raiz + `git diff --check` | Disponível; FND-01 mantém o verificador |
| BE | `uv run --locked pytest` em `backend/` | Disponível no FND-04 |
| INT | `uv run --locked --env-file ../.env pytest -m integration` em `backend/` | Disponível no FND-05 com PostgreSQL de teste |
| API | `uv run --locked pytest tests/contracts` em `backend/` | Disponível no FND-06 |
| FE | `npm test` em `frontend/` | Disponível no FND-07 |
| E2E | PENDENTE | TST-01 |
| DB | `uv run --locked --env-file ../.env pytest -m database` em `backend/` | Disponível no FND-05 com PostgreSQL de teste |
| RAG | PENDENTE | RAG-05 |
| IA | PENDENTE | AI-06 |
| INF | PENDENTE | INF-01 configura build/smoke; INF-04 amplia integração |

Após cada configuração, substituir PENDENTE por comando exato, diretório de execução
e requisitos de ambiente. Atualizar a seção Comandos de AGENTS.md.
Na execução de um cartão, resolver as siglas primeiro. Se o próprio cartão cria
a suite, configurar e rodar o comando nessa entrega. Caso contrário, ausência do
comando é pendência de dependência, não resultado aprovado.

## Verificação documental disponível

Requer Python 3.10+ no ambiente, sem pacotes externos. Executar na raiz:

```text
python scripts/verificar_documentacao.py
python scripts/verificar_documentacao.py --json
git diff --check
```

O verificador é somente leitura: confere referências, IDs, grafo, manifesto,
rastreabilidade e integridade dos materiais. Não executa testes clínicos, aplicação
ou URLs externas. Se `python` for apenas um alias de instalação no Windows, usar
o executável real de Python do ambiente. As siglas de outros conjuntos continuam
sem comandos até seus cartões de configuração; não substituí-los por este DOC.

## Verificações do backend

Usar Python 3.12 e uv. A partir de `backend/`, executar:

```text
uv sync --locked
uv run --locked pytest
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

O [guia do backend](../../backend/README.md) documenta a inicialização local
e o contrato do healthcheck.

O [guia do banco](../../database/README.md) registra o provisionamento, os
comandos de migration e a execução de DB e INT em PostgreSQL real. Para incluir
os scripts de migration na análise estática, execute a partir de `backend/`:

```text
uv run --locked ruff check --config pyproject.toml . ../database/migrations
uv run --locked ruff format --check --config pyproject.toml . ../database/migrations
uv run --locked mypy app tests ../database/migrations
```

## Verificações de identidade

A partir de `backend/`, use `uv run --locked pytest tests/identity` para
testes unitários e `uv run --locked pytest -m integration tests/identity`
para o fluxo HTTP com Argon2id e repositórios de teste de IAM-01, passando
`tests/identity/test_identity.py` no lugar do diretório. Os ensaios
persistentes de IAM-02 usam `uv run --locked --env-file ../.env pytest -m
integration tests/identity` e o PostgreSQL de teste.

## Verificações de autorização

A partir de `backend/`, `uv run --locked pytest tests/authorization` executa
os testes unitários da matriz. Para o ensaio HTTP com contas e sessões no
PostgreSQL de teste, execute:

```text
uv run --locked --env-file ../.env pytest -m integration tests/authorization
```

[Política de autorização](../arquitetura/autorizacao.md).

## Verificações do frontend

Com Node 24 e npm 11, em `frontend/`, execute `npm ci`, `npm test`,
`npm run lint`, `npm run typecheck` e `npm run build`. O
[guia do frontend](../../frontend/README.md) descreve a execução local.

## Preparação técnica documental

DBML foi validado com @dbml/core 11.0.1 e o JSON Schema com Ajv 8.20.0 em
diretório temporário externo ao repositório; 10 casos de contrato passaram.
Scaffolds registrarão comandos reproduzíveis dos conjuntos BE/FE/API/DB.
A validação documental dos exemplos do onboarding é separada das suites da aplicação.

## Notificações

A integração PostgreSQL do NTF-01 está em `backend/tests/notifications/`.
No diretório `backend/`, execute:

```powershell
uv run --locked --env-file ../.env pytest -m 'database or integration' tests/notifications
```

Para habilitar o cenário SMTP, inicie o sink local e configure
`ACADEMIA_TEST_MAILPIT=1` conforme o [roteiro](../arquitetura/notificacoes.md).
O teste de sink é opt-in porque os demais testes de integração não exigem
um serviço de e-mail.

## Recuperação de acesso

A partir de `backend/`, com o PostgreSQL de teste configurado e o
[Mailpit local](../arquitetura/notificacoes.md#ensaio-local-com-mailpit) ativo:

```powershell
$env:ACADEMIA_TEST_MAILPIT = '1'
uv run --locked --env-file ../.env pytest -m integration tests/identity/test_recovery.py
```

O teste usa endereços sintéticos e busca o link por destinatário no Mailpit.
Ele confirma o uso único do token, a troca de senha, a revogação de sessões
e a resposta pública igual para contas conhecidas e desconhecidas. Testes
separados cobrem concorrência, expiração e falha observável de SMTP.
Para conferir no navegador, inicie a aplicação, use **Esqueci minha senha**
com uma conta sintética ativa e abra a mensagem na caixa do Mailpit.

O ensaio em Microsoft Edge headless com viewport de 390 px usou Vite, FastAPI,
PostgreSQL de teste e Mailpit. Verificou o pedido, o link, a retirada do fragmento
da URL, a confirmação e o login com a senha nova. O schema de teste foi removido
ao final.

## Cadastro e manutenção de funcionários

A partir de `backend/`, com PostgreSQL de teste e
[Mailpit local](../arquitetura/notificacoes.md#ensaio-local-com-mailpit):

```powershell
$env:ACADEMIA_TEST_MAILPIT = '1'
uv run --locked --env-file ../.env pytest -m integration tests/people/test_staff.py
```

Na interface, entre como administrador, abra **Gerenciar funcionários** e
cadastre uma conta sintética. Consulte os dados e o estado do convite. Abra
o link recebido no Mailpit em outra janela, defina a senha e entre nessa
janela com a conta convidada. Inative o perfil pelo painel administrativo
e confirme que o acesso operacional foi retirado.

O ensaio no Microsoft Edge com viewport de 390 px usou Vite, FastAPI, PostgreSQL
de teste e Mailpit. Confirmou cadastro, convite, primeiro login e perda da
área de instrutor após a inativação. O schema sintético foi removido ao final.

## Cadastro e manutenção de clientes

A partir de `backend/`, com PostgreSQL de teste e
[Mailpit local](../arquitetura/notificacoes.md#ensaio-local-com-mailpit):

```powershell
$env:ACADEMIA_TEST_MAILPIT = '1'
uv run --locked --env-file ../.env pytest -m integration tests/people/test_clients.py
```

Na área de atendimento ou administrativa, abra **Gerenciar clientes**,
cadastre uma conta sintética e consulte o estado do convite. Abra o link
recebido no Mailpit em outra janela e faça o primeiro login. Busque pelo
nome ou e-mail e inative o perfil. Se a identidade também tiver um perfil
de funcionário ativo, confirme que ele conserva as permissões operacionais.

O ensaio no Edge com viewport de 390 px usou Vite, FastAPI, PostgreSQL de
teste e Mailpit. Confirmou cadastro, busca por e-mail, primeiro login e
bloqueio da área de cliente após inativação. O schema de teste foi removido.

## Designação de instrutor

A partir de `backend/`, com PostgreSQL de teste:

```powershell
uv run --locked --env-file ../.env pytest -o addopts='' tests/assignments
```

O teste de API usa sessões reais e uma rota de prova registrada apenas no
ensaio. Confere a perda do acesso do instrutor anterior após a troca e a
concessão para o novo responsável, sem usar dados de saúde reais. O teste
concorrente disputa a mesma revisão e verifica que o banco guarda apenas um
vínculo vigente.

Para conferir na SPA, entre como administrador, consulte um cliente e abra
**Gerenciar instrutor responsável**. Designar e trocar o instrutor deve exibir
o novo responsável e o vínculo anterior no histórico. Entre com a conta
de cada instrutor e consulte **Meus clientes**.

O ensaio no Edge com viewport de 390 px usou Vite, FastAPI e PostgreSQL de
teste. Confirmou a troca, o histórico e a atualização das listas dos dois
instrutores. O schema temporário foi removido ao final.
