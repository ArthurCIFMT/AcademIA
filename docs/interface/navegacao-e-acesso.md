# UX-03 · Navegação e telas de acesso

A estrutura da SPA usa os [componentes de UX-02](componentes.md). O cabeçalho
oferece saída e mostra a troca de área quando a conta tem mais de um papel
efetivo. O menu ao lado do conteúdo reúne as tarefas da área atual. Em telas
de até 47 rem, duas tarefas frequentes ficam em destaque. O menu recolhível
mostra todas as seções e indica a seção ativa no controle.

| Área | Destino inicial | Outras tarefas |
|---|---|---|
| Cliente | Meus treinos | Assistente, dados de treino, frequência, cobranças simuladas, equipamentos e agenda. |
| Instrutor | Meus clientes | Revisões pendentes e catálogo de exercícios. |
| Atendimento | Clientes e convites | Matrícula e referência na ficha do cliente, reconhecimento de chegada e lotação. |
| Administração | Painel | Clientes, funcionários, designações e catálogos. |

A [lista de rotas e papéis](../../frontend/src/app/areaNavigation.ts) organiza
as tarefas que já existem. A curadoria mantém a entrada condicionada ao papel
administrativo e à configuração explícita de manutenção. A área inicial
segue a prioridade já estabelecida em [autenticação](../arquitetura/autenticacao.md).
A troca de área abre sua tarefa inicial diretamente. O catálogo de equipamentos
tem uma rota autenticada na área do cliente e outra rota pública para visitantes.
O cabeçalho oferece **Meu perfil** em cada área autenticada. O perfil é pessoal
e o endereço acompanha a conta ao alternar papéis.

Uma subpágina de avaliação ou editor manual marca **Meus clientes**. Uma revisão
de ficha marca **Revisões pendentes**. Rotas principais usam `aria-current="page"`
e subpáginas marcam a seção com `aria-current="location"`. Ao navegar, o menu
móvel fecha e o conteúdo recebe foco. Escape fecha e devolve o foco ao
controle. **Ir para o conteúdo** funciona sem trocar o fragmento da URL.

O login, a solicitação de recuperação e a criação ou redefinição de senha
compartilham o painel de acesso. Formulários têm rótulos e mensagens de falha
em texto. A recuperação dá a mesma confirmação pública para qualquer pedido
aceito. A confirmação de senha associa a divergência ao campo e leva o foco
até ele. A SPA remove o fragmento do link de senha depois de lê-lo e mantém
o token em memória durante a confirmação. Primeiro acesso e recuperação têm
formulários de mesma aparência com finalidades distintas. O convite de
onboarding mantém uma página pública própria, com sua sessão restrita e
orientações de conclusão.

Os avisos pendentes continuam na entrada de administração e instrutor.
O aviso sobre o Mailpit mantém o link para a caixa local quando configurada
para loopback. Os caminhos diretos continuam sob os controles da sessão e
da [autorização no backend](../arquitetura/autorizacao.md). Alternar a área
apenas navega. O frontend oculta a área desde o início do logout, e os estados
de verificação, expiração e falha preservam o contrato de sessão.
