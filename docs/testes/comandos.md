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

## Persistência do onboarding

A partir de `backend/`, com PostgreSQL de teste:

```powershell
uv run --locked --env-file ../.env pytest -o addopts='' tests/onboarding
```

A suíte compara o schema emitido pelo Pydantic com o contrato versionado
e executa as fixtures sintéticas aprovadas. A integração cobre rascunho
incompleto, confirmação, revisão concorrente, isolamento por cliente e
invalidação da referência de triagem. A verificação de banco exercita a
migration, o vínculo da avaliação ao cliente e a imutabilidade dos registros.

## Convite inicial de onboarding

A partir de `backend/`, com PostgreSQL de teste e Mailpit local:

```powershell
$env:ACADEMIA_TEST_MAILPIT = '1'
uv run --locked --env-file ../.env pytest -o addopts='' tests/onboarding
uv run --locked --env-file ../.env pytest -m 'database or integration'
```

O ensaio usa e-mails sintéticos e recupera o link no Mailpit. Exercita troca
única, reabertura e conclusão, rejeição de acesso externo, reenvio com
revogação, isolamento entre contas e falha SMTP com registro persistido.
O contrato OpenAPI do módulo roda junto aos testes unitários e a migration
0007 tem verificação de integridade e reversão.

## Formulário responsivo do onboarding

Em `frontend/`, rode `npm test -- --maxWorkers=2`, `npm run lint`,
`npm run typecheck` e `npm run build`. As verificações do formulário ficam
em `frontend/tests/onboarding/` e comparam campos e limites com o schema v1.
Em `backend/`, rode `uv run --locked pytest tests/contracts` e a suíte de
[convite inicial](#convite-inicial-de-onboarding).

Roteiro com Vite, FastAPI, PostgreSQL de teste e Mailpit em 390 px:

1. Com uma sessão administrativa ou de atendimento, use a API de emissão do
   [convite](../arquitetura/onboarding.md#convite-inicial-e-sessão-restrita)
   para um cliente sintético. Abra o link da caixa Mailpit em outra sessão.
2. Abra o formulário, tente concluir vazio, salve um rascunho incompleto e
   recarregue. Simule falha no PATCH e confira que o campo editado fica na tela.
3. Abra o convite de outro cliente em uma segunda aba do mesmo navegador.
   Confirme que a aba antiga não consegue enviar seus dados ao novo rascunho.
4. Reemita o convite original, conclua com uma resposta **Não sei**, entre
   na conta de cliente e consulte a versão salva em **Meu onboarding**.
5. Edite, salve o rascunho e recarregue. Confirme a atualização, verifique a
   nova versão e consulte a antiga pela API. A API deve recusar o mesmo UUID
   histórico quando consultado com a sessão de outro cliente.

O ensaio no Edge confirmou os cinco passos. Também verificou que o link
reenviado abre na mesma aba após a recusa do link anterior. O schema
sintético do ensaio foi removido ao final.

## Avaliação profissional por designação

Rode `npm test -- --maxWorkers=2`, lint, tipos e build em `frontend/`.
Em `backend/`, rode BE, API e a suíte com PostgreSQL do
[onboarding](#persistência-do-onboarding), com o Mailpit habilitado conforme
o roteiro de [convite inicial](#convite-inicial-de-onboarding).

A integração testa leitura e registro pelo instrutor, recusa a atendentes,
tentativa de vincular snapshot de outro cliente, revisão desatualizada,
repetição sem duplicar e histórico após troca de responsável. A porta
interna da IA é testada com dois clientes, snapshots distintos e
avaliações opcionais. A verificação de banco reutiliza os testes da
migration 0006 para a chave estrangeira composta e imutabilidade.

Para conferir na SPA, designe um instrutor a um cliente sintético com
onboarding concluído. Registre uma avaliação em **Meus clientes**.
Transfira a designação e atualize a página do primeiro instrutor.
Entre como sucessor, consulte a avaliação original e registre outra.

O ensaio passou no Edge a 390 px com Vite, FastAPI e PostgreSQL de teste.
O schema sintético foi removido ao final.

## Inventário e catálogo de equipamentos

No backend, rode as suites BE, API e o ensaio abaixo com PostgreSQL de teste.
A suite cobre a migration 0008, validação e armazenamento da foto, permissões,
controle de revisão e revalidação de disponibilidade.

```powershell
uv run --locked --env-file ../.env pytest -o addopts='' tests/equipment
```

No frontend, rode `npm test -- --maxWorkers=2`, `npm run lint`,
`npm run typecheck` e `npm run build`. Para o ensaio no navegador, cadastre
um equipamento sintético com foto em **Gerenciar equipamentos**. Abra o
catálogo público em 390 px e confira nome, descrição e foto. Desmarque
**Operacional** no painel, atualize o catálogo e verifique a retirada da oferta.
Inative o mesmo registro e confira que ele permanece no inventário.

O ensaio no Edge a 390 px passou com Vite, FastAPI e PostgreSQL de teste.
O schema e as fotos sintéticas do ensaio foram removidos ao final.

## Catálogo de exercícios

Em `backend/`, rode BE, API e a suíte do catálogo com PostgreSQL de teste:

```powershell
uv run --locked --env-file ../.env pytest -o addopts='' tests/training
```

Os testes carregam e repetem o
[seed sintético](../../database/seeds/catalogo_exercicios_sintetico.sql)
dentro da transação de teste. Eles verificam permissões, auditoria, unicidade
concorrente, reativação, alternativas completas, falta de equipamento e migration.

Em `frontend/`, rode `npm test -- --maxWorkers=2`, `npm run lint`,
`npm run typecheck` e `npm run build`. Para o ensaio no navegador, entre como
instrutor, cadastre um exercício com duas alternativas e altere a disponibilidade
do inventário como administrador. Confira a elegibilidade após cada mudança.

O ensaio passou no Edge a 390 px com Vite, FastAPI e PostgreSQL de teste.
O schema sintético foi removido ao final.

## Editor de ficha manual

Em `backend/`, rode BE, API e a suíte de treino com PostgreSQL:

```powershell
uv run --locked --env-file ../.env pytest -o addopts='' tests/training
```

A suite verifica rascunho e repetição idempotente, autoria, designação,
snapshots, atualização concorrente de revisão e numeração serializada.
Os testes de banco usam publicação controlada pela fixture para verificar
imutabilidade e expurgo de conteúdo. O seletor do limite de quinze
desconsidera rascunhos e preserva a vigente.

Em `frontend/`, rode `npm test -- --maxWorkers=2`, lint, tipos e build.
No ensaio de navegador em 390 px, entre como instrutor designado a cliente
com onboarding concluído, monte um dia com exercício e prescrição, salve
e recarregue. Reabra, altere e salve. Troque o responsável e confira que
o anterior perdeu acesso e o sucessor pode copiar a versão com sua autoria.

O ensaio passou no Edge a 390 px com Vite, FastAPI e PostgreSQL de teste.
A troca de instrutor preservou a autoria e a prescrição anteriores.
O schema sintético foi removido ao final.

## Publicação e parecer posterior

Em `backend/`, rode BE, API e DB/INT com o PostgreSQL de teste:

```powershell
uv run --locked pytest
uv run --locked pytest tests/contracts
uv run --locked --env-file ../.env pytest -m 'database or integration'
uv run --locked --env-file ../.env pytest -o addopts='' tests/training
```

Para incluir o ensaio de e-mail já existente, mantenha Mailpit local ativo e
defina `ACADEMIA_TEST_MAILPIT=1`. Os testes desta entrega também simulam falha SMTP
controlada, verificando persistência da ficha, fila e estado/reenvio do aviso.

TRN-03 verifica publicação com PENDENTE, isolamento, troca/ausência de instrutor,
revisão/snapshot/catálogo/inventário superados, motivo obrigatório, replay, parecer
imutável e rejeição fora de ordem. A retenção cruza 15 → 16 com primeira versão
aceita ou rejeitada. Falhas injetadas após expurgo demonstram rollback da
publicação e do parecer. Concorrência usa conexões PostgreSQL independentes em
schema sintético, enquanto a suite de migrations verifica os gatilhos reais.
O schema temporário é removido e os testes transacionais revertem seus dados.

Em `frontend/`, rode `npm test -- --maxWorkers=2`, lint, tipos e build.
Os testes cobrem publicação, parecer, falha de rede com repetição da mesma chave,
perda de acesso, conteúdo expirado, fila e estado vazio.

Ensaio Edge a 390 px com Vite, FastAPI, PostgreSQL de teste e Mailpit local:
instrutor designado monta/salva/publica, cliente consulta a API ainda com PENDENTE,
instrutor rejeita A, copia e publica B, confere que A continua visível e rejeita B.
A API passa a retornar dias vazios de A, conserva seu motivo/auditoria e mantém
B rejeitada consultável. Fila fica vazia depois dos pareceres. Não houve
transbordamento horizontal. O schema sintético foi removido ao final.

Resultado local desta entrega: 78 BE, 9 API, 67 DB/INT, 36 testes de treino e
55 FE aprovados. Ruff, mypy, lint, tipos, build, verificador documental e
ensaio no Edge aprovados. As duas linhas longas antigas nas migrations 0004 e
0006 permanecem fora da alteração; o lint cobre backend e migration 0011.

## Consulta móvel e exportação do treino

Em `backend/`, rode BE, API e os testes do módulo com PostgreSQL:

```powershell
uv run --locked pytest
uv run --locked pytest tests/contracts
uv run --locked --env-file ../.env pytest -o addopts='' tests/training
```

TRN-04 verifica estado vazio, rascunho invisível, ficha PENDENTE/ACEITA/REJEITADA,
dois dias de prescrição, recursos indisponíveis sem alterar snapshots,
exportação JSON/headers, histórico limitado e conteúdo expirado por ambas as
regras. Dois clientes reais de teste comprovam recusa ao trocar cliente ou
versão na consulta/exportação. Instrutor sem designação perde acesso e
o próprio cliente continua consultando.

Em `frontend/`, rode `npm test -- --maxWorkers=2`, `npm run lint`,
`npm run typecheck` e `npm run build`. Os testes cobrem o fluxo de consulta,
parecer independente, estados vazio/erro, histórico removido, download com
sessão/no-store, cancelamento e limpeza após recusa.

Ensaio Edge a 390 px com Vite, FastAPI e PostgreSQL de teste: abrir **Meus
treinos** vazio, publicar como instrutor, consultar como cliente com PENDENTE,
baixar e ler o JSON, mudar um equipamento para não operacional e conferir
o aviso sem trocar a prescrição. Depois, rejeitar A, publicar B e consultar
A histórica; rejeitar B retira A do seletor e recusa sua exportação direta.
O esquema temporário foi removido. A interface não apresentou transbordamento
horizontal; o snapshot visual foi inspecionado.

Resultado: 79 BE, 9 API, 43 testes de treino (42 na rodada completa e 1 caso
adicional de isolamento) e 64 FE aprovados. Ruff, formato, mypy, lint,
tipos, build, verificação documental e ensaio Edge aprovados.
Schema permanece na migration 0011. Não houve integração LLM/RAG neste cartão.


## SPEC portátil e sincronização das fontes

A partir da raiz, com Python 3.10+ e sem dependências externas:

```text
python scripts/gerar_spec.py --write
python scripts/gerar_spec.py --check
python scripts/verificar_documentacao.py
```

O primeiro comando monta somente SPEC.md a partir das fontes explícitas em
docs/especificacao/compilacao-spec.json. O modo --check é somente leitura e
falha quando a cópia diverge. Os hashes de texto normalizado e o plano de
compilação permitem identificar o instantâneo usado.

A verificação desta entrega inclui geração determinística, recusa de cópia
desatualizada sem escrever, conferência do conteúdo em arquivo portátil isolado,
schemas/configurações JSON íntegros e preservação dos requisitos/critério,
modelo de dados, corpus e sequência de cartões. O compilador não lê .env real,
baixa arquivos ou altera código, banco, materiais e migrations.

A alteração é documental e adiciona apenas o compilador reutilizável.
Testes funcionais de backend/frontend e ensaios de IA não são reexecutados para
validar esta consolidação; os resultados dessas entregas permanecem históricos.

## Corpus documental

RAG-01 implementa [curadoria e proveniência](../arquitetura/corpus.md), sem
extração/indexação/busca antecipadas. A partir de backend/, com PostgreSQL de teste:

```powershell
uv run --locked --env-file ../.env pytest -o addopts='' tests/knowledge
uv run --locked pytest
uv run --locked pytest tests/contracts
$env:ACADEMIA_TEST_MAILPIT = '1'
uv run --locked --env-file ../.env pytest -m 'database or integration'
uv run --locked ruff check . ../database/migrations/env.py ../database/migrations/versions/0012_corpus.py
uv run --locked ruff format --check . ../database/migrations/env.py ../database/migrations/versions/0012_corpus.py
uv run --locked mypy app tests ../database/migrations/env.py ../database/migrations/versions/0012_corpus.py
```

Na raiz: python scripts/gerar_spec.py --check e
python scripts/verificar_documentacao.py. No frontend/: npm test, npm run lint,
npm run typecheck e npm run build. Os ambientes/lockfiles seguem os guias existentes.
O Mailpit de loopback estava ativo para incluir os cenários SMTP de regressão.

Evidência de 2026-11-11: 14 testes específicos, 87 BE, 9 API, 79 DB/INT e
69 FE passaram; Ruff/formato, mypy (101 arquivos), lint, tipos e build passaram.
A migration foi aplicada/revertida em teste e conferida com Alembic check.
Metadados, quarentena, isolamento, concorrência e proteção do histórico foram
verificados. A importação dos 18 PDFs reais manteve os sete selecionados aprovados
e os 11 de reserva pendentes; repetição não duplicou nem removeu revogações.
Arquivo alterado abortou o lote sem cadastros parciais; autoria completa foi preservada.

Ensaio Edge headless com viewport de 390 px, Vite, FastAPI e PostgreSQL reais:
login sintético → cadastro TXT UTF-8 em TESTE → aprovação → download → revogação →
importação dos PDFs locais → filtro de literatura e conferência da persistência.
Sem transbordamento horizontal. Schema e conta sintéticos removidos ao final.
Esse ensaio não usa LLM, embeddings, busca vetorial nem produz evidência de qualidade
RAG: são etapas posteriores. Importação na aplicação de uso é ação explícita do
administrador pela tela; os testes não alteram o corpus do banco de desenvolvimento.
