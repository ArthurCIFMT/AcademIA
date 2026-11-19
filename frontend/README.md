# Frontend do AcademIA

Use Node.js 24 e npm 11. Em `frontend/`, execute `npm ci`. Crie
`.env.local` a partir de `.env.example` para usar o proxy de desenvolvimento.
Inicie o backend conforme o [guia](../backend/README.md) e execute `npm run dev`.
A SPA fica em <http://127.0.0.1:5173>.

`VITE_API_BASE_URL` define a base usada pelo cliente HTTP. O padrão é
`/api`. `ACADEMIA_API_PROXY_TARGET` indica o endereço do backend no Vite.
O proxy encaminha `/api/health` para `/health` e mantém o caminho das rotas
versionadas. A tela inicial informa carregamento, sucesso ou falha e oferece
nova tentativa. O cliente HTTP fica em `src/lib/` e os fluxos em `src/features/`.

Os convites e a recuperação de senha usam Mailpit local; não chegam ao Gmail
ou Outlook. Configure `VITE_TEST_MAILBOX_URL=http://127.0.0.1:8025` em
`.env.local` para mostrar o botão de abertura da caixa nos formulários.
Reinicie o Vite depois de mudar variáveis. Links e persistência da caixa estão
no [guia de notificações](../docs/arquitetura/notificacoes.md).

```text
npm test
npm run lint
npm run typecheck
npm run build
```

## Geração e acompanhamento AI-04

A curadoria RAG pertence à operação técnica, não ao menu administrativo comum.
VITE_CORPUS_MAINTENANCE_ENABLED=false é o padrão. A ativação temporária da
tela /tecnico/corpus exige também o backend habilitado e sessão administrativa.
Veja o [preparo local](../docs/instalacao/preparar-rag-local.md).

Cliente autenticado: /area/cliente/treino-ia. O identificador do pedido fica na
URL para consulta após recarregar, sem repetir geração. A tela mostra resultado,
fontes e parecer; o instrutor usa a revisão existente.
[Contrato completo](../docs/arquitetura/solicitacao-e-acompanhamento-ia.md).

## Chat do cliente — AI-05

/area/cliente/assistente oferece dúvidas sem exigir ficha/onboarding/parecer.
Adaptação pede confirmação dos dados já salvos no formulário autenticado,
base atual e dia-alvo; publica nova versão PENDENTE depois das validações.
Retomada por UUID/foco usa GET; envio/reenvio exige ação explícita.
Texto não executa HTML; fonte aceita somente http/https.
Os testes de training-chat cobrem envio, retomada, falha, autorização,
confirmação de adaptação e 429 sem repetição automática.
[Contrato](../docs/arquitetura/chat-e-adaptacao.md).
