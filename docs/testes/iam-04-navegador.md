# Roteiro de integração do IAM-04

## Preparar o ambiente local

1. Configure o PostgreSQL e aplique as migrations conforme o [guia do banco](../../database/README.md). Use uma conta ativa com papel administrador conforme o [guia do primeiro administrador](../instalacao/primeiro-administrador.md). Use somente contas sintéticas para o roteiro.
2. Defina `ACADEMIA_AUTH_ORIGIN=http://127.0.0.1:5173` e `ACADEMIA_AUTH_ALLOW_LOCAL_HTTP=true` no `.env` local. A partir de `backend/`, inicie a API com `uv run --locked --env-file ../.env uvicorn app.main:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log`.
3. Siga o [guia do frontend](../../frontend/README.md) e configure `ACADEMIA_API_PROXY_TARGET=http://127.0.0.1:8000` no `.env.local` do frontend. Rode `npm run dev` e abra a SPA em `http://127.0.0.1:5173`. Use sempre a origem cadastrada no backend.

## Verificar no navegador

| Cenário | Ação | Resultado esperado |
| --- | --- | --- |
| Acesso direto sem sessão | Em janela privada, abra `/area/administracao`. | A SPA verifica a sessão e abre o login sem renderizar a área. |
| Credenciais inválidas | Envie senha incorreta de uma conta de teste. | A API retorna 401 e a interface exibe a mensagem no login. |
| Credenciais válidas | Entre com a conta ativa. Recarregue a área. | A área do papel aparece e a recarga restaura a sessão. |
| Papel incompatível | Com sessão de uma conta sintética somente cliente, abra `/area/administracao`. | A interface exibe acesso negado e oferece a área do cliente. |
| Logout | Clique em **Sair** e abra novamente uma rota protegida. | A área some imediatamente, a API responde 204 e a rota exige login. |
| Expiração | Entre novamente e mantenha a aba aberta e sem atividade por pelo menos 31 minutos. Recarregue a área. | A interface esconde a área no prazo de inatividade e a API responde 401 na recarga. |

## Execução

O ensaio local em Microsoft Edge headless usou largura de 390 px, proxy Vite,
FastAPI e PostgreSQL de teste. O login foi exibido sem rolagem horizontal. Uma conta administradora e uma cliente foram criadas
em schema temporário, removido ao final. Foram verificados os cenários
acima, os atributos HttpOnly e SameSite=Lax dos cookies, o 403 em
logout sem CSRF e a remoção dos cookies após o 204. Para testar a
expiração do lado do servidor, o ensaio antecipou o vencimento da sessão
no schema isolado.

Os testes da SPA ficam em `frontend/tests/auth/`. Execute `npm test`,
`npm run lint`, `npm run typecheck` e `npm run build` em `frontend/`.
A partir de `backend/`, execute `uv run --locked pytest tests/contracts`
para os contratos REST.
