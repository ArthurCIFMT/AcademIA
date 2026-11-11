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
| RAG | `uv run --locked --env-file ../.env pytest -o addopts='' tests/knowledge/test_retrieval.py tests/knowledge/test_retrieval_evaluation.py` em backend/; exige flag E5 real e pesos locais | Disponível no RAG-05; configuração abaixo |
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

## Conexão vetorial local

RAG-02 usa o [Qdrant local persistente](../arquitetura/banco-vetorial.md).
A partir de backend/, sem servidor Qdrant, Docker, PostgreSQL ou pesos de embeddings
para os testes específicos deste adaptador:

```powershell
uv sync --locked
uv run --locked pytest tests/knowledge/test_vector.py
uv run --locked pytest -m integration tests/knowledge/test_vector.py
uv run --locked pytest -o addopts='' tests/knowledge/test_vector.py
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

O primeiro pytest seleciona unitários (doubles); o segundo integra o engine real;
o terceiro executa os dois conjuntos. Cada integração usa diretório temporário
exclusivo, sem compartilhar índices locais do projeto. O ensaio entre processos
abre subprocessos Python e confirma recusa por lock, liberação e reabertura.
Vetores são sintéticos de dimensão 384; não são embeddings E5 nem literatura.
A persistência foi comprovada com um ponto e sua busca técnica após reabrir o engine.
A consulta de teste não é aceite de relevância/latência de RAG-05.

Verificação manual, com a API parada, em backend/:

```powershell
uv run --locked --env-file ../.env python -m app.modules.knowledge.vector
```

Resultado esperado: status OK, modelo intfloat/multilingual-e5-small,
dimensão 384, Cosine, nome versionado e fingerprint. Execução seguinte preserva
a coleção. Falha retorna JSON com código técnico e exit code 1, sem caminho/segredo.
Não usar a CLI na mesma pasta enquanto outro processo mantém o engine aberto.

Evidência de 2026-11-11: 32 testes específicos (24 unitários e 8 integrações reais)
aprovados; regressão com 111 BE, 9 API e 87 DB/INT, incluindo PostgreSQL e Mailpit
locais, aprovada. Ruff/formato, mypy em 106 arquivos, SPEC e DOC aprovados.
Verificados metadados persistidos, rejeição de dimensão/métrica/modelo/revisão
incompatíveis, preservação de dados, erro de armazenamento, singleton/threads,
lock entre processos e liberação no shutdown. API continua disponível sem abrir
o índice, inclusive com configuração vetorial inválida.

Frontend e schema PostgreSQL não foram alterados; não há nova migration ou rota
vetorial REST. A dependência qdrant-client e suas transitivas foram travadas sem
atualizar versões preexistentes. Extração/indexação/busca e fixação da revisão dos
pesos ficam para RAG-03–RAG-05; sem novo ensaio de qualidade de IA nesta entrega.

## Extração PDF e TXT

RAG-03 oferece [serviço interno de extração](../arquitetura/extracao-documental.md)
com fixtures pequenas e ensaio real do corpus. A partir de backend/:

```powershell
uv sync --locked
uv run --locked pytest tests/knowledge/test_extraction.py
uv run --locked --env-file ../.env pytest -m integration tests/knowledge/test_extraction.py tests/knowledge/test_extraction_postgres.py tests/knowledge/test_corpus_extraction.py
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

O primeiro comando pytest seleciona os testes unitários. As integrações incluem
subprocesso real, PostgreSQL de teste para aprovação/revogação e sete PDFs reais,
com diretórios temporários exclusivos. Não requer Qdrant aberto, pesos, OCR ou LLM.
O grupo de regressão geral mantém o comando DB/INT habitual com Mailpit opt-in.
Na raiz, executar também gerar_spec.py --check, verificar_documentacao.py e
git diff --check, conforme as seções anteriores.

Fixtures PDF/TXT foram renderizadas/conferidas: símbolos, unidades, negações,
marcadores, páginas em imagem, documento misto, vazio e protegido. As expectativas
ficam em backend/tests/knowledge/fixtures/expectativas.json, separadas da literatura.
Casos complementares cobrem UTF-8/BOM/CRLF, limites, timeout, saída inválida,
falha persistida, replay, retry explícito máximo três, cache corrompido,
concorrência e revogação antes/durante/depois da extração.

O [relatório real](extracao-corpus-rag03.json) verifica os sete hashes e 327 páginas
físicas: três documentos CONCLUIDA e quatro REVISAO_NECESSARIA. Os quatro pendentes
não devem ser indexados como extrações concluídas sem tratamento/revisão técnica.
Isso não representa avaliação de busca, resposta de LLM ou aprovação clínica.
Os 11 documentos de reserva não foram promovidos nem extraídos para ingestão.

Schema PostgreSQL e frontend permanecem fora desta entrega; não há migration ou
novo endpoint. A persistência da extração é um artefato privado versionado por
UUID/hash/configuração; ativação do índice pertence ao RAG-04.

Evidência de 2026-11-11: 34 testes específicos (24 unitários/10 integrações)
aprovados; regressão com 135 BE, 9 API e 97 DB/INT, incluindo Mailpit, aprovada.
Ruff/formato, mypy em 115 arquivos, SPEC e DOC aprovados. Sem testes de frontend
nesta entrega, pois a interface não foi alterada. O ensaio não promove os quatro
documentos pendentes e não demonstra qualidade/velocidade de respostas da IA.

## Indexação e embeddings locais

RAG-04 entrega [seleção/chunking, E5 CPU e indexação](../arquitetura/indexacao-documental.md).
A partir de backend/, com PostgreSQL de teste e pesos locais provisionados:

~~~powershell
uv sync --locked
uv run --locked --env-file ../.env python -m app.modules.knowledge.embeddings.provision
uv run --locked pytest tests/knowledge/test_indexing.py
$env:ACADEMIA_TEST_EMBEDDINGS_REAL = '1'
uv run --locked --env-file ../.env pytest -m 'database or integration' tests/knowledge/test_indexing.py
uv run --locked --env-file ../.env pytest -o addopts='' tests/knowledge/test_indexing.py tests/knowledge/test_vector.py
uv run --locked ruff check . ../database/migrations/env.py ../database/migrations/versions/0013_knowledge_indexing.py
uv run --locked ruff format --check . ../database/migrations/env.py ../database/migrations/versions/0013_knowledge_indexing.py
uv run --locked mypy app tests ../database/migrations/env.py ../database/migrations/versions/0013_knowledge_indexing.py
~~~

O primeiro pytest seleciona unitários. Integração usa diretório Qdrant temporário,
PostgreSQL real e, com a flag, pesos E5 CPU reais. Sem a flag, dois testes E5 ficam
explicitamente skipped; isso não é aceite de embeddings reais. Se usar outro
caminho, configurar ACADEMIA_EMBEDDING_PATH absoluto. Não requer chave de LLM ou GPU.
A API deve estar parada ao operar seu diretório vetorial por CLI; testes isolados
não compartilham o índice de desenvolvimento. O provisionamento é o único passo
que precisa de internet. Pesos, índices, extrações e dados de teste não entram no Git.

Cobertura: limites 300/48/512, parágrafo/tabela indivisível, símbolos/negações,
finalidade aprovada e origem, vetores normalizados/finitos/384, rate limit e timeout
com retry limitado, encerramento do worker, idempotência, falha parcial/retomada,
crash entre vetor e checkpoint, payload corrompido, revogação e migration ida/volta.
O ensaio completo E5 + PG + Qdrant usa texto sintético delimitado e comprova a
integração técnica. Não demonstra qualidade de busca ou resposta, nem ativa as
quatro fontes com revisão técnica pendente do RAG-03. Não houve teste de frontend,
pois a interface não foi alterada. Permanecem as duas linhas longas preexistentes
nas migrations 0004/0006; esta entrega verifica o backend e a migration nova.

Evidência de 2026-11-11: 21 testes RAG-04 (13 unitários e 8 DB/INT), junto aos
32 testes de conexão, totalizaram 53 aprovados com E5 real habilitado. A regressão
geral passou com 148 BE, 9 API e 104 DB/INT, incluindo Mailpit; o caso adicional
de corrupção/reparo passou na execução complementar, totalizando 105 DB/INT
verificados. Ruff/formato e mypy em 129 arquivos aprovados. SPEC e DOC aprovados.
A primeira tentativa de integração encontrou PostgreSQL parado; após iniciá-lo,
os ensaios foram repetidos com sucesso. Nenhum teste foi ignorado para obter aceite.
Dependências anteriores do lockfile foram preservadas; 51 entradas novas cobrem
a inferência e plataformas alternativas do lock, sem significar instalação de GPU.

## Recuperação semântica e avaliação RAG

RAG-05 entrega [porta de recuperação](../arquitetura/recuperacao-semantica.md),
[28 casos rotulados](rag05-consultas-v1.json) e [relatório real](rag05-avaliacao.json).
Em backend/, com PostgreSQL exclusivo de teste e E5 provisionado conforme RAG-04:

~~~powershell
$env:ACADEMIA_TEST_EMBEDDINGS_REAL = '1'
uv run --locked --env-file ../.env pytest -o addopts='' tests/knowledge/test_retrieval.py tests/knowledge/test_retrieval_evaluation.py
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
~~~

Sem a flag, o ensaio real é explicitamente skipped e não comprova aceite RAG.
Se os pesos estiverem em outro lugar, definir ACADEMIA_EMBEDDING_PATH absoluto.
Não exige chave Groq, GPU ou API LLM. O cenário SC-05 remove a chave do ambiente
para verificar a recuperação de instrução sintética como dado, sem executar ação.

Para escrever novo relatório do ensaio, configurar ACADEMIA_RAG_REPORT para um
arquivo local próprio antes de executar somente test_retrieval_evaluation.py.
Esse arquivo registra métricas reais; não sobrescrever a evidência versionada em
uma execução de rotina. O conjunto fixa limiares e perguntas antes da medição.
As integrações revertem transações do banco de teste e usam Qdrant temporário.

O ensaio real usa sete trechos completos, hash/página/offsets, de BR-RBCM-001;
18 consultas buscam português, seis buscam o resumo original em inglês da mesma
publicação e quatro são fora de escopo. Não traduz o corpus. Modelo aquecido e
cache de consultas inicialmente vazio; carga inicial informada separadamente.
Mede busca e recuperação total sem LLM, p50/p95 e recall por idioma. Uma amostra
de sete candidatos não demonstra desempenho em corpus amplo nem qualidade do MVP.
A geração de fichas e tempo total da LLM serão avaliados em AI-06.

Casos de domínio cobrem autorização documental/revogação depois do cache e durante
a consulta, ingestão parcial, finalidade, adulteração de payload, isolamento de
cache por contexto, tamanho/top-K, baixa similaridade, falha de embeddings,
pertinência curada por condição/população/intervenção e conflito. Fonte com score
alto não recebe suporte de saúde automaticamente. O livro Nahas foi escolhido e
registrado como referência pendente de extração válida; os quatro PDFs anteriores
não foram promovidos. Não há migration, dependência nova ou alteração de frontend.

Evidência de 2026-11-11: 16 testes específicos aprovados (6 BE e 10 INT,
incluindo E5/Qdrant/PostgreSQL reais e o ensaio rotulado). Regressão: 154 BE,
114 DB/INT com Mailpit e 9 API aprovados; a regressão adicional de finalidade
adulterada passou em execução complementar, totalizando 115 DB/INT verificados.
Ruff/formato, mypy em 136 arquivos,
SPEC e DOC verificados. Neste conjunto: recall@5=100%, recall PT/EN=100% e
abstenção fora de escopo=100%. Tempos exatos, inicialização e tamanho da amostra
estão no relatório JSON; esses resultados não são métricas da futura LLM.
Não foi executado frontend, pois não houve alteração de interface.

## Triagem acadêmica e preparação AI-01

[Contrato](../arquitetura/triagem-academica.md) e [mapa de casos](ai01-cobertura.json).
Em backend/, com PostgreSQL de teste configurado para a integração:

~~~powershell
uv run --locked pytest tests/ai
uv run --locked --env-file ../.env pytest -m integration tests/ai
uv run --locked --env-file ../.env pytest -o addopts='' tests/ai
uv run --locked pytest tests/contracts
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
~~~

Não requer chave Groq, pesos ou Qdrant para os testes AI-01. O Analyst é um double
rotulado de contrato; a API, sessões/papéis e PostgreSQL são reais. A suíte geral
DB/INT continua incluindo opt-ins E5/Mailpit dos módulos anteriores quando ativados.
Testes novos verificam os 19 casos aplicáveis da tabela de triagem, tamanho real
excedido, ausência/negação/gravidade, saída estrita e evidência inventada, timeout
com resposta tardia e catálogo vazio separado da decisão de saúde.

Integração: cliente titular, terceiros, administrador sem permissão de saúde e
instrutor sem designação são diferenciados; instrutor designado acessa pelo serviço
interno. A API resolve cliente/snapshot pela sessão, mantém no-store, não aceita
sinais de análise pelo usuário e não expõe resumo. Cobrir snapshot alterado,
catálogo inativado, equipamento indisponível e conta revogada durante a análise.
Auditoria registra apenas metadados, sem anamnese ou motivos clínicos no log.

Evidência de 2026-11-11: 32 testes específicos (26 unitários/6 integrações),
180 BE, 121 DB/INT com Mailpit e 9 API aprovados. Ruff/formato, mypy em 148 arquivos,
SPEC e DOC verificados. Schema 0013 reutilizado; sem migration ou dependência nova.
Não executar frontend nesta entrega, pois a interface não mudou. O provedor real,
qualidade semântica e desempenho integrado permanecem em AI-02/AI-06; não afirmar
aceite de LLM pelos doubles. A revisão manual do responsável será no MVP, sem
substituir os testes automatizados, E2E e critérios obrigatórios de cada etapa.

## Orquestrador e contratos AI-02

[Arquitetura/limites](../arquitetura/orquestracao-ia.md) e
[schemas portáveis](../requisitos/schemas/execucao-ia-v1.schema.json).
A partir de backend/, ambiente uv/Python 3.12; integração requer PostgreSQL de teste:

~~~powershell
uv run --locked pytest tests/ai/test_execution.py tests/ai/test_groq.py tests/ai/test_execution_contracts.py
uv run --locked --env-file ../.env pytest -m integration tests/ai/test_execution_integration.py
uv run --locked pytest
uv run --locked --env-file ../.env pytest -m 'database or integration'
uv run --locked pytest tests/contracts
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
~~~

Na raiz: python scripts/gerar_spec.py --write, depois --check;
python scripts/verificar_documentacao.py e git diff --check.
Testes não exigem GROQ_API_KEY nem fazem requisição à Groq. MockTransport exercita
o adaptador HTTPX real, body/modelo/JSON, timeout, quota, redirects, tamanho, modelo
divergente e ausência de credencial; não comprova disponibilidade ou latência real.
Harness FastAPI testa transporte JSON/OpenAPI dos schemas, sem registrar uma rota
de execução no produto. O arquivo JSON versionado é comparado aos modelos Python.

Casos do orquestrador verificam uma análise/uma geração ou apenas chat; graves e
dados desconhecidos sem rede, JSON/schema inválidos sem reparo, IDs/recursos/fontes,
evidência pertinente para saúde, excesso sem truncamento, chamadas físicas/reserva
mantidas em falha, replay concorrente, entrada diferente, cancelamento, resposta
tardia e invalidação de fonte/contexto. Injeção é tratada como dado; campo de
parecer humano é rejeitado. Não afirmar resistência semântica absoluta por doubles.

Três integrações novas usam PostgreSQL real: autorização fresca/titular/instrutor
designado, catálogo/equipamento alterado durante execução e ponte de evidência
com ingestão/Qdrant reais e revogação. QueryDouble nessa ponte substitui embeddings;
a regressão RAG existente executa E5 real com ACADEMIA_TEST_EMBEDDINGS_REAL=1,
modelo local provisionado e ACADEMIA_EMBEDDING_PATH configurado.
ACADEMIA_TEST_MAILPIT=1 mantém também o teste SMTP real. Testes revertem transações
e usam diretórios Qdrant temporários; não alteram dados pessoais ou corpus ativo.

Evidência de 2026-11-11: 60 testes específicos aprovados (57 BE/3 INT).
Regressão: 237 BE, 124 DB/INT com E5/Mailpit e 9 API aprovados (API é subconjunto
de BE). Ruff/formato, mypy em 168 arquivos, SPEC e DOC verificados.
Schema físico permanece 0013. HTTPX já instalado passou a runtime, mesma versão.
Não executar frontend pois nenhuma interface mudou. Não declarar geração/publicação
integrada: o estado durável e publicação ficam em AI-03; chat/interface em AI-04/05;
ensaio de qualidade/desempenho real em AI-06, E2E/aceite do MVP em TST-01.

## Geração persistente AI-03

[Contrato](../arquitetura/geracao-persistente.md). Em backend/:

~~~powershell
uv run --locked pytest tests/ai/test_generation_unit.py
uv run --locked --env-file ../.env pytest -o addopts='' tests/ai/test_generation.py tests/ai/test_generation_http.py tests/ai/test_generation_concurrency.py
uv run --locked pytest
uv run --locked --env-file ../.env pytest -m 'database or integration'
uv run --locked pytest tests/contracts
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
~~~

Na raiz: python scripts/gerar_spec.py --write/--check (uma opção por execução),
python scripts/verificar_documentacao.py e git diff --check.
Migration 0014 testada por upgrade/downgrade/upgrade e comparação ORM/schema.
Sem alterar migrations aplicadas. Novas integrações usam PostgreSQL/Qdrant reais,
QueryDouble para embeddings sintéticos e GroqAdapter/HTTPX MockTransport.
Nenhum teste novo exige GROQ_API_KEY ou consulta a Groq. Não confundir esse
contrato com ensaio semântico de qualidade/latência, que continua no AI-06.
E5 real e Mailpit permanecem na regressão com as flags documentadas anteriormente.

Cobertura específica: publicação própria/origem IA/parecer PENDENTE antes do aceite;
tokens e chamadas físicas; replay/divergência sem gerar outra ficha; saída inválida
preservando vigente; cancelamento em voo; mudança de equipamento; quinze versões
com expurgo da explicação e ausência de cópia JSON na execução; processo reiniciado
sem repetir chamadas; retenção de conteúdo privado por 90 dias com recibo preservado.
API real cobre 401, CSRF/403, 422, consulta/cancelamento alheio 404 e no-store.
Conexões PostgreSQL independentes verificam claim único e cota atômica/replay sem
segunda vaga. Cenários complementares alteram fonte/onboarding na transação final
e verificam bloqueio grave/desconhecido antes de qualquer chamada LLM.
Fixtures/limpezas são isoladas no banco de teste; dados pessoais reais não são usados.

Evidência de 2026-11-11: 16 testes novos aprovados (2 BE/14 INT), incluindo quatro
integrações complementares executadas após a regressão geral.
239 BE, 134 DB/INT na regressão com E5/Mailpit, mais as quatro integrações novas
(138 DB/INT verificados ao todo); 9 API aprovados, incluídos em BE.
Ruff/formato e mypy em 182 arquivos aprovados; SPEC/DOC verificados.
Frontend não executado pois nenhuma interface mudou. AI-04 entregará a tela;
AI-05 chat/adaptação públicos; AI-06 provedor real/qualidade/latência, sem dispensar
o E2E e o aceite do MVP em TST-01. Pendências anteriores do corpus permanecem.

## Acompanhamento e interface AI-04

[Contrato](../arquitetura/solicitacao-e-acompanhamento-ia.md) e
[schemas portáveis](../requisitos/schemas/acompanhamento-ia-v1.schema.json).
Em backend/:

~~~powershell
uv run --locked pytest tests/ai/test_followup_unit.py
uv run --locked --env-file ../.env pytest -m integration tests/ai/test_followup.py
uv run --locked pytest
uv run --locked --env-file ../.env pytest -m 'database or integration'
uv run --locked pytest tests/contracts
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
~~~

Em frontend/: npm test, npm run lint, npm run typecheck e npm run build.
Nesta sessão, os mesmos scripts foram resolvidos pelo Node 24 empacotado:
node node_modules/vitest/vitest.mjs run; node node_modules/eslint/bin/eslint.js .;
node node_modules/typescript/bin/tsc --noEmit; node node_modules/vite/bin/vite.js build.
Lockfiles/dependências preservados; sem nova instalação ou pacote.

Testes React: uma geração por clique, UUID/CSRF, retomada somente por GET,
bloqueio/insuficiência/abstenção/timeout, cancelamento com resposta tardia, perda
de acesso removendo conteúdo/fontes, ID inexistente e URL insegura, revisão IA
com aceite/rejeição e reenvio da tentativa efetivamente salva sem republicar.
Os quatro testes anteriores da revisão manual seguem passando.

Quatro integrações novas usam PostgreSQL/Qdrant reais e o cenário sintético de
AI-03: fontes/parecer antes do aceite, falha SMTP sem perder fila, replay sem novo
envio, repetição explícita idempotente, sem instrutor, onboarding atualizado,
fonte revogada, troca de designação e permissões das APIs. O transporte SMTP é
controlado, assim como o texto Groq/embeddings da fixture; não é ensaio do modelo.
E5/Mailpit reais continuam na regressão via flags documentadas.
Oito unitários cobrem contrato de tentativa inicial/limitada, minimização de fonte
e correspondência da cópia portátil com os modelos da API.

Evidência de 2026-11-11: 22 testes novos aprovados (8 BE/4 INT/10 FE).
Regressão: 246 BE e um contrato BE complementar (247 verificados), 142 DB/INT
com E5/Mailpit, 9 API (subconjunto de BE), 79 FE. Após acrescentar aviso de fonte
alterada, repetidos os quatro INT e 14 FE afetados, com build/tipos/lint aprovados.
Ruff/formato e mypy em 187 arquivos aprovados; SPEC/DOC verificados.
Preview do build em navegador headless, com respostas controladas: 390 e 1280 px,
sem overflow horizontal ou erro JavaScript, geração única e consulta sem POST.
Esse ensaio visual não é E2E com backend/provedor real: AI-06/TST-01 permanecem abertos.
Artefatos temporários de navegador/visualização ficam fora do repositório.
Schema físico permanece 0014; MER preservado. Chat/adaptação públicos seguem em AI-05.
