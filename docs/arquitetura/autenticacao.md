# Adaptador de autenticação

IAM-01 entrega autenticação em Python com Argon2id pelo pwdlib, sessão opaca
e portas de persistência. O adaptador HTTP é montado por `BrowserAuth.router()`
quando recebe uma unidade de trabalho capaz de fornecer `AuthService`.
A composição da aplicação com os repositórios PostgreSQL é a próxima etapa,
IAM-02. O ensaio local compõe o adaptador real com repositórios de teste.

| Rota | Contrato |
|---|---|
| POST /api/v1/auth/login | Recebe JSON com `email` e `senha`. Inicia sessão e devolve JSON com `user_id`, `expires_at` e `csrf_token`. |
| GET /api/v1/auth/session | Consulta a sessão vigente e recupera o token CSRF por JSON para a interface recarregada. |
| POST /api/v1/auth/logout | Exige origem e CSRF. Revoga a sessão, limpa os cookies e retorna 204. |

Os cookies são restritos ao caminho `/api/v1`, HttpOnly e SameSite=Lax.
Em HTTPS são Secure. Defina `ACADEMIA_AUTH_ORIGIN` com a origem exata da
interface. Para desenvolvimento em loopback, habilite `ACADEMIA_AUTH_ALLOW_LOCAL_HTTP`.
A interface mantém o CSRF em memória e o envia em `X-CSRF-Token` nas mutações.
Login também exige a origem configurada. Use o proxy Vite e a mesma origem em
implantação.

Sessão e CSRF usam 32 bytes aleatórios cada. A persistência recebe somente
seus hashes SHA-256. O prazo absoluto é de 12 horas e o de inatividade é de
30 minutos. A autenticação verifica o estado da conta em cada requisição.
O limite inicial é de 5 falhas por par e-mail normalizado e IP em 15 minutos.
Esse controle vive em memória no processo único do MVP e reinicia com ele.
As variáveis `ACADEMIA_AUTH_LOGIN_MAX_FAILURES` e
`ACADEMIA_AUTH_LOGIN_WINDOW_SECONDS` permitem configurar a janela.

A porta de sessão exige criação atômica condicionada à revisão e ao estado
ativo da conta. A atualização de uso verifica novamente a validade e deve
manter o maior instante observado. Ao alterar a senha, a unidade de trabalho
atualiza a revisão e chama `revoke_after_password_change` antes do commit.
Assim, um login concorrente com credencial anterior não abre nova sessão.

A partir de `backend/`, execute `uv run --locked pytest tests/identity`
para os testes unitários e `uv run --locked pytest -m integration tests/identity`
para o fluxo HTTP com Argon2id real. A suíte INT geral também inclui os testes
do PostgreSQL, separados desse ensaio. [Decisão de identidade](decisoes/ADR-002-identidade-e-papeis.md)
