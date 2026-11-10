# Autorização por operação e recurso

A API resolve o ator pelo cookie de sessão e consulta os papéis efetivos no
PostgreSQL em cada requisição protegida. Uma conta acumula permissões de seus
perfis ativos. Conta global inativa ou bloqueada perde a sessão. Um perfil
inativo retira apenas as permissões daquele perfil.

| Operação | Papel e condição |
|---|---|
| Administrar contas, papéis, funcionários e designações | Administrador ativo |
| Manter cadastro básico de clientes | Administrador ou atendente ativo |
| Ler onboarding, saúde ou ficha | Cliente titular ou instrutor com vínculo vigente |
| Editar o próprio onboarding e usar contexto privado da IA | Cliente titular |
| Registrar avaliação e prescrever ou revisar ficha | Instrutor com vínculo vigente |

As operações e condições estão em `app/policies/access.py`. A autorização
nega por padrão. Dados de saúde exigem escopo próprio ou designação com
necessidade funcional. O papel administrativo por si só permite as operações
cadastrais da matriz. O contexto privado do chat fica restrito ao cliente.

Em uma rota protegida, declare `actor: AuthenticatedActor` de
`app.policies.http` e chame `require_permission` com a operação e o titular
obtido pelo backend a partir do recurso. Por exemplo, a consulta e a
exportação de uma ficha usam ambas `Operation.READ_WORKOUT` e o identificador
do titular da ficha. O módulo dono do recurso continua responsável por verificar
a existência, a visibilidade e as regras de publicação ou retenção. A interface
usa os papéis para navegação. A API decide o acesso e retorna 401 para sessão
inválida ou 403 para sessão válida sem permissão.

`AssignmentReader` é fornecido pelo módulo de designação entregue no PES-03.
O adaptador PostgreSQL verifica o vínculo vigente e a elegibilidade dos
perfis. Rotas profissionais podem usar a dependência `AssignmentAccess`
e aplicar a política ao identificador do cliente obtido pelo backend.
Sessão, conta, perfis e papéis também usam PostgreSQL.
[Contrato de designações](designacoes.md#leitura-profissional).

[Contratos de autenticação](autenticacao.md) · [Decisão de identidade](decisoes/ADR-002-identidade-e-papeis.md)
