# Designação do instrutor responsável

PES-03 monta o router e a dependência de autorização em
`backend/app/main.py`. O adaptador `backend/app/modules/people/assignment_directory.py`
oferece nomes, elegibilidade e bloqueio de identidades do MOD-01 por contrato.
O MOD-02 mantém a relação histórica em sua própria tabela. A SPA conecta as
telas em `frontend/src/app/AppRoutes.tsx` e oferece a entrada no detalhe de
cliente em `frontend/src/features/clients/ClientDirectory.tsx`.

## API e autorização

| Rota | Operação |
|---|---|
| GET /api/v1/designacoes/instrutores | Administrador pesquisa candidatos ativos por nome ou e-mail. |
| GET /api/v1/designacoes/clientes/{client_id} | Administrador consulta vínculo atual e histórico paginado, com início, fim e autor. |
| PUT /api/v1/designacoes/clientes/{client_id} | Administrador cria ou substitui o vínculo, enviando `instrutor_id` e `vigente_id`. |
| GET /api/v1/designacoes/minhas | Instrutor consulta a lista paginada dos clientes elegíveis designados à própria sessão. |

A primeira designação usa `vigente_id: null`. Uma troca informa o UUID do
vínculo que o administrador consultou. Se outro operador já o substituiu,
a API retorna 409. Selecionar o mesmo instrutor com o vínculo vigente correto
preserva o registro existente. O backend exige a política de administrador,
origem e CSRF para a alteração. A lista do instrutor usa o ator autenticado
e retorna somente o identificador, nome do cliente e início da designação.

A migration 0005 cria o índice parcial único por cliente com `fim IS NULL`.
A transação bloqueia as identidades envolvidas, verifica elegibilidade, fecha
o vínculo anterior no mesmo instante em que abre o novo e grava auditoria.
O autor e as datas do vínculo anterior ficam disponíveis no histórico.
Perfil cliente ativo com conta convidada pode receber designação. O instrutor
precisa de conta ativa, perfil funcionário ativo e papel efetivo de instrutor.

## Leitura profissional

O adaptador `PostgresAssignmentReader` implementa `AssignmentReader`.
Rotas que protegem informações por designação podem receber
`assignments: AssignmentAccess` e chamar `require_permission` com a operação
e o identificador do cliente obtido do recurso. Serviços transacionais podem
instanciar o leitor com a sessão da própria operação. A verificação considera
vínculo sem fim e elegibilidade dos dois perfis. Desativação de perfil ou troca
de instrutor retira a autorização mesmo quando a sessão antiga permanece aberta.

Se o instrutor ficar inativo, a designação administrativa fica registrada
como indisponível. O administrador pode substituí-la. O registro permanece
como referência histórica e fica fora da consulta profissional enquanto o
perfil estiver inativo. O módulo de avaliação usa esse contrato nas
[rotas profissionais](onboarding.md#avaliação-pelo-instrutor-designado).
