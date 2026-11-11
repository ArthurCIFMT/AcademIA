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

```text
npm test
npm run lint
npm run typecheck
npm run build
```

## Geração e acompanhamento AI-04

Cliente autenticado: /area/cliente/treino-ia. O identificador do pedido fica na
URL para consulta após recarregar, sem repetir geração. A tela mostra resultado,
fontes e parecer; o instrutor usa a revisão existente.
[Contrato completo](../docs/arquitetura/solicitacao-e-acompanhamento-ia.md).
