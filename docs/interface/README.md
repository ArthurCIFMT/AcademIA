# UX-01 · Referência visual do AcademIA

[Abrir o protótipo local](prototipo/index.html) ·
[Resultados da verificação](../testes/ux01-referencia-visual.md)

O protótipo começa em **Meus treinos**. Use o seletor **Área** para ver a
navegação de cliente, instrutor, atendimento e administração. O logotipo
leva à tela de entrada. Em **Assistente**, explore dúvida, geração,
adaptação e exemplos de abstenção, quota, triagem, dados insuficientes e falha.
A navegação funciona localmente com dados sintéticos fixos. Os formulários
ilustram as etapas e sua hierarquia. Entrar na demonstração, mudar de área
e consultar cenários são transições do protótipo.

## Inventário do MVP e mapa para a reformulação

As rotas vêm de [AppRoutes](../../frontend/src/app/AppRoutes.tsx). Nomes entre
crases são rotas vigentes. Os fragmentos do protótipo são pontos de referência
da apresentação, não novas rotas do produto.

| Área | Rotas vigentes e ações reais | Organização proposta e estados |
|---|---|---|
| Pública | `/`, `/login`; `/recuperar-acesso`, `/redefinir-senha`, `/primeiro-acesso`; `/equipamentos` | Entrada com foco no acesso; recuperação e primeiro acesso mantêm seus fluxos próprios. Diferenciar sessão expirada, credencial recusada, carregamento e erro de conexão. Catálogo público permanece acessível. |
| Convite | `/onboarding/convite`; abertura, retomada, salvamento e conclusão com sessão restrita | Página dedicada com passos e retorno. Exibe convite inválido/usado/expirado, falha de rede e confirmação. A conclusão orienta a voltar ao login. |
| Entrada autenticada | `/area`, `/area/cliente`, `/area/instrutor`, `/area/atendimento`, `/area/administracao`; saída e escolha entre papéis efetivos | Cabeçalho com área corrente e troca entre áreas permitidas. Preservar abertura direta por URL, recusa de acesso e saída. Administração e instrutor preservam seus avisos pendentes. |
| Cliente · treinos | `/area/cliente/treinos`; ficha atual, versões retidas, exportação JSON própria | Ficha por dia, exercício e recurso; revisão e histórico têm contexto próprio. Mostrar pendente, aceito e rejeitado por texto. Vazio, recurso indisponível e versão expirada têm saída clara. |
| Cliente · dados | `/area/cliente/onboarding`; preenchimento, rascunho, consulta, nova versão confirmada | Objetivos e rotina → Dados físicos → Saúde → Revisão. Rascunho persistido e edição local têm mensagens distintas. A consulta mostra a idade na conclusão. Solução de conflito preserva edições conforme o contrato. |
| Cliente · assistente | `/area/cliente/assistente` → Dúvida ou Adaptação; `/area/cliente/treino-ia` → Geração e acompanhamento | Uma entrada de menu com três ações explícitas. Dúvida oferece resposta e fontes ou abstenção; adaptação exige alvo e confirmação; geração apresenta recibo salvo, triagem, quota, falha e nova tentativa. |
| Instrutor | `/area/instrutor/clientes` → `/area/instrutor/clientes/:clientId/avaliacoes` ou `/area/instrutor/clientes/:clientId/treinos`; `/area/instrutor/revisoes` → `/area/instrutor/clientes/:clientId/treinos/:versionId/revisao`; `/area/instrutor/exercicios` | Lista e ficha do cliente designado, avaliação, rascunho, revisão e publicação em sequência. Revisão pendente, fila vazia, conflito de versão, inativação e recusa de acesso aparecem perto da ação. |
| Atendimento | `/area/atendimento/clientes`; cadastro, busca, detalhe, idade, atualização e convites | Uma entrada para clientes e convites. Busca e lista precedem edição. Perfil ativo, convite, falha de e-mail e conta têm rótulos distintos. |
| Administração | `/area/administracao/clientes`, `/area/administracao/funcionarios`, `/area/administracao/designacoes`, `/area/administracao/equipamentos`, `/area/administracao/exercicios` | Menu agrupado por trabalho recorrente. Busca, listagem e detalhe separados da ação de alteração. Mostrar revisão superada, validação, inativação, vínculo vigente e disponibilidade. |
| Manutenção | `/tecnico/corpus`; `/area/administracao/corpus` redireciona | Link e acesso visual condicionados à manutenção habilitada e ao perfil autorizado. Excluído do menu de operação diária. |

O seletor lista os papéis já atribuídos à identidade. Selecionar outro papel
apenas muda a área, com autorização no backend e titularidade/designação
revalidadas durante consultas e ações. No caso sintético de administração
com atendimento acumulado, a linha de base mostra os dois papéis. O seletor
aberto a quatro exemplos no protótipo é uma ferramenta de demonstração.
Matrícula, catraca, aulas, dashboard, financeiro e edição do próprio perfil
aguardam suas entregas funcionais.

## Comparação com a linha de base

O [relatório](../testes/ux01-referencia-visual.md) liga cada cena à captura do
MVP e à do protótipo. A linha de base usa os componentes e rotas reais, servidos
a partir do build atual com respostas HTTP sintéticas.

- A navegação do MVP ocupa várias linhas antes do conteúdo em cada área.
  Concentrar as ações recorrentes no menu dá contexto ao título e à ação da página.
- O onboarding do MVP é uma página longa. Dividi-lo em quatro etapas reduz o
  volume simultâneo de campos e permite revisar respostas antes da confirmação.
- O assistente e a geração já têm telas distintas. Uma entrada de navegação
  apresenta as três ações com rótulos próprios, mantendo o efeito de cada pedido.
- Ficha, parecer e cadastro já exibem os dados principais. Cards e linhas de
  dados agrupam leitura e ações sem exigir tabela horizontal no celular.

## Tokens e componentes para UX-02

| Uso | Valores e decisão |
|---|---|
| Fundo, superfície e texto | `#f3f6f4`, `#ffffff`, `#142c30`; texto secundário `#4e6264`. Superfície branca identifica conteúdo acionável e blocos de leitura. |
| Marca e seleção | `#07574f`, `#073b3b`, fundo ativo `#e1f0eb`. Seleção com texto, cor e linha inferior; capa escura só para destacar ficha corrente e entrada. |
| Campo e foco | Separador `#d5e0dc`, borda de controle `#687e7b`, foco `#1c57a0` com 3 px e afastamento de 3 px. Bordas decorativas e contornos funcionais têm usos distintos. |
| Aviso e erro | Aviso `#634300` em `#fff5d9`; erro `#842f24` em `#fcece9`. Sempre mostrar título ou estado em texto. |
| Tipografia | Fonte do sistema, 16 px de base, altura de linha 1,55. Níveis principais 32–50, 21,6 e 16 CSS px na escala padrão, com medidas em rem. Sem carregamento de fonte externa. |
| Espaçamento e superfície | Escala 4, 8, 12, 16, 24, 32 CSS px; raios de 9 a 16 px conforme componente. Conteúdo com limite de 72 rem. |
| Interação | Botão principal sólido, secundário contornado e links sublinhados. Alvos principais de 44 px ou mais. Usar rótulos ligados aos campos, foco visível, âncora de salto e títulos focados ao trocar de vista. |

Em **1440 px**, menu lateral, cabeçalho compacto e painéis de conteúdo lado a lado.
Em **768 px**, menu lateral reduzido, com painéis empilhados e campos em duas
colunas quando couberem. Em **390 px**, menu recolhível no topo com seção atual
visível, ficha e formulário empilhados e ações que quebram linha. Em **320 px**, a mesma ordem
é preservada com quebra de texto e células estreitas. O breakpoint de 47 rem
troca o menu para a disposição superior. O de 63 rem empilha os painéis.

Em UX-02, implementar primeiro tokens, formulário e estados comuns. Para
UX-03, aplicar menu e entrada; UX-04–UX-08 integram os fluxos por área.
UX-09 compara a aplicação real com esta linha de base. Preservar restrições
de saúde, recursos, avisos, autorização e status da IA durante essa evolução.
Estado salvo e nova solicitação continuam operações diferentes. As respostas
do assistente no protótipo são estáticas e não geram ou alteram fichas.
