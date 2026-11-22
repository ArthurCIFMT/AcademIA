# UX-03 · Verificação de navegação e acesso

O [guia de navegação](../interface/navegacao-e-acesso.md) descreve a interface
implementada. Rotas e endpoints existentes são exercitados com as contas e
e-mails sintéticos do ensaio. As capturas abaixo são da SPA atual.

| Captura | Cenário |
|---|---|
| Login | [390 px](../interface/evidencias-ux03/ux03-login-celular.png) · [1440 px](../interface/evidencias-ux03/ux03-login-desktop.png) |
| Administração | [Funcionários selecionado a 1280 px](../interface/evidencias-ux03/ux03-administracao.png) |
| Instrutor | [Início e avisos a 1280 px](../interface/evidencias-ux03/ux03-instrutor.png) |
| Atendimento | [Menu aberto pelo teclado a 390 px](../interface/evidencias-ux03/ux03-atendimento-celular.png) |
| Cliente | [Conta com papéis acumulados e menu aberto por toque a 390 px](../interface/evidencias-ux03/ux03-cliente-celular.png) |

## Resultados

- **Frontend** com 103 testes aprovados em 21 arquivos. Lint, tipos e build
  passaram. Os testes existentes de sessão, curadoria, login, primeiro acesso,
  recuperação e avisos foram mantidos.
- **Regressão integrada** com oito jornadas no Edge 158.0.4370.33, FastAPI,
  PostgreSQL dedicado de teste e Mailpit. E2E-01 usa o menu administrativo e
  confirma a seção ativa, o foco após navegação e o menu autorizado do
  instrutor. E2E-08 percorre troca de papel no celular, navegação por toque,
  Escape com retorno de foco e recusa de link direto de outro perfil.
  O [registro sanitizado](../interface/evidencias-ux03/resultado-e2e.json)
  confirma as oito aprovações e a reversão do schema de teste.
- **Recuperação** com resposta pública idêntica para endereço conhecido e
  desconhecido. A jornada de troca real de senha verifica o link no Mailpit
  e a revogação da sessão anterior. Logout e isolamento entre contas são
  verificados nas demais jornadas. O LLM usado na regressão é controlado.
- **Responsividade** com as mesmas oito rotas de UX-02 a 320, 390, 768 e
  1440 CSS px. A rodada serviu o build atualizado com HTTP interceptado e
  mediu largura do documento e alvos das ações. Toque no E2E foi emulado
  pelo Edge. O iniciador segue compatível com a operação local.

A primeira rodada de testes de componentes revelou perda de contexto no
login causada por um Outlet intermediário e dois conjuntos de links durante
a troca de largura. O login voltou a consumir o contexto diretamente e o
menu passou a renderizar uma única variante por largura.
Após as oito jornadas, o encerramento do Vite do runner no Windows exigiu
intervenção no processo isolado da porta de teste. O runner gravou o resultado
e confirmou a reversão depois que esse processo foi encerrado.

## Reprodução

Em `frontend/`, com as dependências existentes:

```powershell
npm test -- --maxWorkers=2
npm run lint
npm run typecheck
npm run build
```

Em `backend/`, com PostgreSQL de teste vazio e Mailpit conforme
[as pré-condições do runner](aceitacao-mvp.md#instalação-e-execução):

```powershell
$env:ACADEMIA_E2E = '1'
uv run --locked --env-file ../.env python -m tests.acceptance --output ./data/e2e/ux03-N
```

Na raiz, com Edge e Node 24 disponíveis:

```powershell
node docs/interface/verificar-ux02.cjs backend/data/ux03-build-N backend/data/ux03-larguras-N
python scripts/gerar_spec.py --check
python scripts/verificar_documentacao.py
git diff --check
```

Os relatórios brutos e as credenciais sintéticas do E2E ficam na pasta
ignorada de execução. A rodada de UX-03 verifica a regressão do frontend e
as jornadas integradas atuais. Os recibos históricos de aceite do MVP e
do provedor real conservam sua versão original.
