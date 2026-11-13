# Aceitação ponta a ponta do MVP — TST-01

## Escopo e estado

TST-01 CONCLUIDO e PG-01 FECHADO em 2026-11-12, conforme a
[consolidação reproduzível](tst01-consolidacao.json). O aceite combina oito
jornadas E2E compatíveis com o código atual, 14 testes críticos reexecutados e
AI-06 real aprovado. É o MVP acadêmico delimitado, com revisão manual do
responsável como próximo passo; não encerra módulos pós-MVP.

O [runner](../../backend/tests/acceptance/__main__.py) inicia FastAPI/Uvicorn real,
SPA/Vite real e Playwright/Edge. PostgreSQL e Qdrant são reais; SMTP usa Mailpit local.
Há oito [jornadas rastreáveis](tst01-cenarios.json), com navegador a 1280×800 e consulta
móvel a 390×844. Não é API isolada apresentada como navegação.

O LLM é um adaptador controlado de testes, sem chave/rede Groq. Embeddings e texto
são fixtures explicitamente sintéticas, separadas do corpus de uso. A publicação
continua passando pelos serviços reais de triagem, autorização, catálogo, fontes,
inventário, versões, avisos e parecer. Isso testa integração e renderização,
sem afirmar que a IA produziu uma resposta real ou uma prescrição fundamentada.
A emissão do convite de onboarding e as 16 publicações do cenário de retenção
usam a API autenticada real; o preenchimento e a consulta são feitos no navegador.

[Resultado sanitizado](tst01-resultado.json). A qualidade, PT/EN e ataques semânticos
do modelo real dependem da [consolidação AI-06](ai06-consolidacao.json).
O runner local conserva seu snapshot original aceite_mvp=false, com AI-06
ainda pendente naquela execução. Esse recibo não foi reescrito para fingir uma
nova navegação. O novo consolidador combina-o ao aceite real atualizado e
registra aceite_mvp=true em arquivo próprio, com hashes dos insumos.

## Instalação e execução

Pré-condições: PostgreSQL 17 com academia_test dedicado e vazio, Mailpit nativo
em 127.0.0.1:1025/8025, Python 3.12/uv, Node 24/npm 11 e Microsoft Edge instalado.
Configurar ACADEMIA_TEST_DATABASE_URL no .env local conforme o guia do banco.
Não é necessário configurar GROQ_API_KEY para este ensaio.

Na pasta frontend/:
~~~powershell
npm ci
~~~

Na pasta backend/:
~~~powershell
uv sync --locked
$env:ACADEMIA_E2E = '1'
uv run --locked --env-file ../.env python -m tests.acceptance --output ./data/e2e/rodada-N
~~~

Escolha pasta nova para cada rodada. O runner recusa sobrescrever evidências.
Node deve estar no PATH; alternativamente informe --node com o executável Node 24.
A opção --frontend-port muda a porta local padrão 5187. O backend usa porta local
livre; a origem e o proxy são passados explicitamente para aquela execução.
Não reutiliza frontend/backend de desenvolvimento ou servidor já aberto na porta.

O comando npm run test:e2e existe, mas recebe ambiente/fixture do runner Python;
não deve ser usado isoladamente contra o ambiente de desenvolvimento.
Chromium também é selecionável com --channel chromium, após instalar o navegador
compatível por npx playwright install chromium. A evidência desta entrega usa Edge.

Playwright foi acrescentado somente às dependências de desenvolvimento, com versão
exata 1.65.0 no lockfile; é necessário para percorrer a interface de forma reproduzível.
Vitest exclui tests/e2e/** para não executar testes Playwright como componentes.
Não houve alteração funcional de domínio, migration, MER ou regra de saúde.
Referências: [servidores de teste](https://playwright.dev/docs/test-webserver) e
[navegadores suportados](https://playwright.dev/docs/browsers).

## Isolamento e proteção dos dados

O runner exige opt-in ACADEMIA_E2E=1, URL e conexão efetiva para academia_test.
Recusa schema academia preexistente; não executa DROP/TRUNCATE sobre um banco usado.
Aplica as migrations em transação externa, testa bootstrap repetido sem duplicar,
cria fixtures sintéticas e usa savepoints nos serviços reais. Requisições HTTP são
serializadas no harness para proteger a conexão única. Concorrência/carga não é
comprovada por este navegador: continua nos testes PostgreSQL apropriados.

Ao terminar, encerra o servidor e reverte a transação; uma nova conexão confirma
que o schema de teste foi desfeito. Não aponta para academia_dev. Qdrant e arquivos
de corpus ficam no diretório privado da rodada. Mensagens sintéticas no Mailpit
são filtradas por destinatário de teste; o ensaio não limpa a caixa compartilhada
nem envia mensagens a pessoas reais. Nenhum relay externo é usado.

A senha dos usuários é gerada por execução e enviada somente no ambiente do processo.
A chave Groq é removida do ambiente do runner/filhos, sem alterar o .env original.
Não versionar fixtures privadas, logs, downloads, screenshots de falhas, índices ou
cookies. backend/data/ já é ignorado. Só o relatório sanitizado acompanha o Git.
O relatório vincula código da aplicação/testes e lockfiles por hash normalizado,
registra versão do navegador, tentativas, duração, persistência e rollback.

## O que as jornadas demonstram

| Jornada | Evidência local |
|---|---|
| E2E-01 | Bootstrap, funcionário/cliente, primeiro acesso via e-mail, designação, convite restrito, rascunho/conclusão, avaliação, equipamento/exercício e ficha manual, exportação, rejeição e persistência após novo login. |
| E2E-02 | Dois clientes, troca de sessão, APIs/IDs alheios recusados, CSRF e HTML/script entregue pela API real sem execução no navegador. |
| E2E-03 | Três estados de triagem com fixtures rotuladas; grave não publica, NAO_SEI/ausente insuficientes; consulta/chat sem aceite ou instrutor. |
| E2E-04 | Replay e consulta não duplicam ficha/aviso; nova versão do onboarding exige confirmação; adaptação explícita mantém outro dia e inicia parecer PENDENTE. |
| E2E-05 | 16 → 15 versões completas; exclusão impede consulta/exportação; rejeição posterior substitui o conteúdo da rejeitada anterior. |
| E2E-06 | Mudança do equipamento entre rascunho/publicação provoca 409; permissão do inventário é aplicada na API. |
| E2E-07 | Indisponibilidade controlada da IA não impede editar/publicar/consultar treino manual. |
| E2E-08 | Papéis/perfis independentes e recuperação por e-mail com revogação de sessão anterior. |

Backend/integração complementam fronteiras não demonstradas isoladamente pelo
navegador: concorrência, expurgo de chat/cache, alterações de restrição durante
revisão, tokens inválidos/expirados e isolamento do corpus. As evidências e comandos
constam no [registro de testes](comandos.md#aceitação-local-do-mvp-tst-01).

## Fechamento reproduzível

O [consolidador](../../backend/tests/acceptance/consolidation/__init__.py) verifica:

- mesmo código de aplicação, interface, harness e lockfiles do E2E (237 arquivos);
- oito jornadas distintas aprovadas em uma tentativa, navegador/API reais;
- bootstrap, persistência e rollback confirmados, migration atual 0015;
- 14 testes críticos completos/aprovados, mesmo código e fontes dos testes;
- AI-06 real aprovado e integralmente reproduzido a partir de execução/revisão;
- hashes dos três relatórios e do próprio verificador, separados do runtime.

Em backend/, com perfil principal, sem chamada externa ou necessidade de banco
para a consolidação:

~~~powershell
uv run --locked python -m tests.acceptance.consolidation --output ./data/e2e/aceite-N.json
uv run --locked pytest tests/acceptance
~~~

A saída deve ser nova; evidência anterior não é sobrescrita. A decisão só retorna
APROVADO/aceite_mvp=true quando todos os critérios passam. Mudança de código,
revisão, schema, relatório ou ausência de caso mantém o aceite pendente. Uma
nova implementação precisa reexecutar as evidências correspondentes.

## Evidências e resultado de 2026-11-12

O relatório de oito jornadas da execução Gemini já existente corresponde ao
código atual, com 237 hashes iguais e zero diferença. Ele substitui a publicação
anterior (235 arquivos), preservada no [histórico](historico/tst01-antes-fechamento/README.md).
Nesta entrega não se repetiu navegador ou chamada LLM. A imagem móvel existente
e os cenários continuam referentes à mesma interface.

[Críticos atuais](tst01-criticos.json): 14 testes aprovados em PostgreSQL/Qdrant
reais, incluindo concorrência, retenção, inventário, snapshot, isolamento e
recuperação vetorial com E5 local. As chaves Groq/Gemini foram removidas do processo.
Um aviso de reescrita do plugin anyio ocorreu por importação no helper de snapshot;
não houve falha/skip dos 14 casos. A [regressão geral anterior](tst01-regressao.json)
é histórica; os 458 BE/85 FE não são declarados reexecutados agora.

Os 21 testes de guardas do aceite passaram: casos ausentes, duplicados, ignorados,
tentativa repetida, código/fontes antigos, rollback/migration incompatíveis,
AI-06 pendente/revisão alterada e tentativa de sobrescrever saída não fecham MVP.
Ruff/formato e mypy (228 fontes) verificados; SPEC/DOC e diff conferidos.
Novos arquivos são de teste/consolidação, sem alteração de código da aplicação,
frontend, migrations, dependências, corpus ou parâmetros do LLM.

[Consolidação final](tst01-consolidacao.json): APROVADO, nove critérios verdadeiros,
TST-01 CONCLUIDO e PG-01 FECHADO. AI-06 mantém seus limites de cinco exemplos e
percentis descritivos; reservas não qualificadas, fontes pendentes e módulos de
matrícula/CompreFace/catraca, agenda, indicadores, financeiro e Docker permanecem
fora do aceite deste MVP. Não iniciar essas funcionalidades nesta entrega.
