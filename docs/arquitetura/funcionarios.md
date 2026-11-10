# Cadastro e manutenção de funcionários

PES-01 monta o router no ponto de composição `backend/app/main.py` e
integra a tela à área administrativa em `frontend/src/app/AppRoutes.tsx`.
A tela reaproveita o cliente HTTP de `frontend/src/lib/api/auth.ts` e a
confirmação de senha em `frontend/src/features/auth/RecoveryPages.tsx`.
A identidade fornece emissão e cancelamento do convite e o bloqueio
transacional de alterações de administrador. Notificações fornece a
consulta do estado de entrega. Esses pontos de ligação complementam os
diretórios de implementação do cartão.

## API e autorização

| Rota | Operação |
|---|---|
| GET /api/v1/funcionarios | Lista com `pagina` e `limite`. Página inicial 1 e tamanho padrão 20, com máximo 100. |
| GET /api/v1/funcionarios/{user_id} | Consulta dados, papéis, estado do perfil e estado do último convite. |
| POST /api/v1/funcionarios | Cria identidade e perfil na mesma transação, ou vincula uma identidade existente quando indicado expressamente. |
| PUT /api/v1/funcionarios/{user_id} | Atualiza nome, cargo, data de admissão, papéis e estado do perfil. Exige a `revisao` da consulta. |
| POST /api/v1/funcionarios/{user_id}/convite | Emite novo convite para funcionário ativo com conta convidada. Exige a `revisao` da consulta. |

O backend verifica o papel de administrador em todas as rotas. Mutações usam
origem da SPA e CSRF da sessão. Os papéis administrativos disponíveis são
administrador, atendente e instrutor. Nome, cargo, admissão e pelo menos um
papel operacional são obrigatórios. O vínculo explícito usa o e-mail da conta
de cliente existente. Conta ativa mantém as credenciais. Conta convidada
recebe um convite de primeiro acesso. Duplicidade incompatível, revisão antiga
ou tentativa de remover o último administrador ativo recebem 409.

A inativação altera o perfil de funcionário. A conta e eventual perfil de
cliente ativo continuam independentes. A política de autorização recalcula
os papéis efetivos a cada requisição. As mudanças preservam o perfil histórico
e geram auditoria com ator e instante. Atribuição de papéis e mudanças de
papel ou estado também avisam os administradores ativos. O bloqueio
transacional de administradores é compartilhado com o bootstrap inicial.
A entrega reutiliza as tabelas instaladas nas revisões 0003 e 0004.

## Convite e primeiro acesso

O envio ocorre após o commit do cadastro. O detalhe mostra validade e estado
da entrega. Falha de SMTP preserva a conta convidada e o perfil criado.
O botão **Reenviar convite** emite novo link e invalida o anterior. São
permitidas até três emissões em 24 horas por conta convidada. A mesma revisão
usada novamente recebe 409, evitando reenvio duplicado. O envio de teste usa
o [Mailpit local](notificacoes.md#ensaio-local-com-mailpit).

O link abre `/primeiro-acesso` no frontend com o token no fragmento. A SPA
remove o fragmento e envia o token e a senha no JSON ao endpoint já existente
`POST /api/v1/auth/first-access`. O token expira em 24 horas e é consumido ao
definir a senha. A autenticação usa a mesma identidade criada ou vinculada.
Se o perfil for inativado enquanto a conta estiver convidada, os links
pendentes são invalidados quando não há outro perfil ativo de cliente.
