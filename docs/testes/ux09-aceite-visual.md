# UX-09 — Aceite visual e regressão integrada

Ensaio em 22/11/2026 no Microsoft Edge 158.0.4370.33 em Windows. A matriz usa
o build do React/Vite com respostas sintéticas e viewports de 320, 390, 768 e
1440 CSS px. O ensaio integrado usa a aplicação, a API, PostgreSQL no banco
`academia_test` e Mailpit, com dados sintéticos e IA controlada.
[Matriz da execução no navegador](../interface/evidencias-ux09/resultado-visual.json).

## Telas, perfis e capturas

As comparações usam o aplicativo em UX-01 e UX-09. Em cada par, o primeiro
arquivo é de 390 px e o segundo é de 1440 px. As 14 rotas da matriz passaram
nas quatro larguras, com fonte a 200% também em 320 e 390 px.

| Tela e cenário | Perfil | UX-01 | UX-09 |
|---|---|---|---|
| Entrada e recuperação de acesso | Visitante | [390](../interface/evidencias-ux01/antes/entrada-390.png) · [1440](../interface/evidencias-ux01/antes/entrada-1440.png) | [390](../interface/evidencias-ux09/entrada-390.png) · [1440](../interface/evidencias-ux09/entrada-1440.png) |
| Onboarding e revisão dos dados | Cliente | [390](../interface/evidencias-ux01/antes/onboarding-390.png) · [1440](../interface/evidencias-ux01/antes/onboarding-1440.png) | [390](../interface/evidencias-ux09/onboarding-390.png) · [1440](../interface/evidencias-ux09/onboarding-1440.png) |
| Assistente, dúvida com evidência insuficiente | Cliente | [390](../interface/evidencias-ux01/antes/duvida-390.png) · [1440](../interface/evidencias-ux01/antes/duvida-1440.png) | [390](../interface/evidencias-ux09/duvida-390.png) · [1440](../interface/evidencias-ux09/duvida-1440.png) |
| Geração, limite do provedor atingido | Cliente | [390](../interface/evidencias-ux01/antes/quota-390.png) · [1440](../interface/evidencias-ux01/antes/quota-1440.png) | [390](../interface/evidencias-ux09/quota-390.png) · [1440](../interface/evidencias-ux09/quota-1440.png) |
| Ficha vigente, parecer pendente e exercícios por dia | Cliente | [390](../interface/evidencias-ux01/antes/ficha-390.png) · [1440](../interface/evidencias-ux01/antes/ficha-1440.png) | [390](../interface/evidencias-ux09/ficha-390.png) · [1440](../interface/evidencias-ux09/ficha-1440.png) |
| Parecer sobre a versão publicada | Instrutor designado | [390](../interface/evidencias-ux01/antes/parecer-390.png) · [1440](../interface/evidencias-ux01/antes/parecer-1440.png) | [390](../interface/evidencias-ux09/parecer-390.png) · [1440](../interface/evidencias-ux09/parecer-1440.png) |
| Editor manual com dia e exercício | Instrutor designado | Sem captura do editor na linha de base | [390](../interface/evidencias-ux09/editor-390.png) · [1440](../interface/evidencias-ux09/editor-1440.png) |
| Cadastro de cliente e alternância de área | Administrador e atendente | [390](../interface/evidencias-ux01/antes/cadastro-390.png) · [1440](../interface/evidencias-ux01/antes/cadastro-1440.png) | [390](../interface/evidencias-ux09/cadastro-390.png) · [1440](../interface/evidencias-ux09/cadastro-1440.png) |
| Cadastro no atendimento | Atendente | Sem captura | Matriz do navegador |
| Funcionários, designações, equipamentos e exercícios | Administrador | Sem captura | Matriz do navegador |
| Catálogo de equipamentos | Visitante | Sem captura | Matriz do navegador |

## Critérios verificados

| Critério | Resultado e evidência |
|---|---|
| Consistência | Capturas conferidas com a referência de componentes. Cabeçalho, menus, campos e mensagens mantêm a mesma identidade entre papéis. |
| Hierarquia | Título, contexto e ação principal visíveis. O editor diferencia adicionar e remover, com rótulos explícitos e a variante de ação destrutiva. |
| Responsividade | As 14 rotas em quatro larguras sem rolagem horizontal da página. A tabela de exemplo mantém rolagem localizada acessível por teclado. |
| Ampliação | Fonte raiz a 200% em 320 e 390 px. O cabeçalho e a ficha cabem na página. [Ficha a 320 px com texto ampliado](../interface/evidencias-ux09/ficha-320-ampliada.png). |
| Contraste | Dez pares de cores medidos no navegador. Texto principal 13,47:1, texto secundário 5,93:1, foco 6,61:1 e borda do campo 4,32:1. Mensagens trazem rótulos textuais. |
| Toque | Alvos principais amostrados com pelo menos 44×44 CSS px, incluindo a ação de abertura dos formulários. Menu do mostruário acionável em contexto de toque. |
| Teclado | Atalho para o conteúdo e foco visível nas 14 rotas a 390 px. Menu de exemplo fecha com Escape e devolve foco. Editor acionado por teclado até incluir um exercício. |
| Formulários | Campo inválido recebe foco e desfaz estado de erro após correção. Evidências de retomada e preservação após falha de rede em [UX-04](ux04-onboarding-etapas.md) e [UX-08](ux08-cadastros-e-catalogos.md). |
| Estados | Quota, bloqueio, vazio, conflito, sucesso e falha cobertos pela regressão e pelas evidências de [UX-05](ux05-assistente.md) e [UX-07](ux07-area-do-instrutor.md). Consultar o pedido mantém a contagem de geração estável. |
| Privacidade | Jornadas de isolamento entre contas, acesso recusado pela API e sessão/perfis independentes. Capturas feitas só com fixtures sintéticas. |
| Conteúdo | Português nos títulos, rótulos e mensagens, inclusive nos estados de treino e do Assistente. Navegação restrita às funções disponíveis. |
| Evidência visual | Aplicativo real no Edge, com sete cenários comparados em duas larguras e capturas adicionais do editor, dos componentes e da ampliação. |

O cabeçalho cortava a marca a 320 px com texto a 200%, conforme registrado em
[UX-06](ux06-fichas-no-celular.md). A marca agora pode se ajustar ao espaço.
Nas fichas, o recuo do exercício e o espaçamento horizontal foram limitados
em telas estreitas para reduzir quebras de palavras com texto ampliado.
No editor, **Remover dia** e **Remover exercício** usam a variante destrutiva.
O iniciador de dois cliques permanece compatível com os mesmos serviços,
comandos e configurações.

## Regressão e reprodução

- Em `frontend/`, a suíte de `npm test -- --maxWorkers=1` passou com 116
  testes em 21 arquivos. A verificação de lint, tipos e build também passou.
  O Node executou os binários locais equivalentes aos scripts de `package.json`.
- O [executor E2E](aceitacao-mvp.md) passou em 8/8 jornadas na primeira tentativa.
  Cobriu cadastro, primeiro acesso, convite, onboarding, ficha manual, isolamento,
  CSRF, triagem, geração única, adaptação, expurgo, parecer, exportação, mudança de
  disponibilidade de equipamento, falha da IA e recuperação de conta. O executor
  confirmou rollback e registrou zero chamadas a LLM externo.
- Para repetir as verificações de layout e contraste a partir da raiz, criar
  capturas em dois diretórios ainda inexistentes, dentro de `backend/data/`:

```powershell
node docs/interface/verificar-ux02.cjs backend/data/ux09-build-N backend/data/ux09-visual-N
```

A execução cobre o Edge no Windows e viewports emulados. O ensaio de ampliação
altera a fonte raiz. A verificação de contraste e alvos é amostral, com cobertura
por rota conforme a matriz. Dispositivos físicos, leitores de tela e conformidade
integral com WCAG ficam fora deste aceite. O ensaio usa IA controlada e preserva
os registros históricos de AI-06 e TST-01 associados às versões que exercitaram.

## Revisão manual disponível

O responsável relatou problemas de apresentação e navegação no MVP, e solicitou
o redesenho. A revisão do responsável sobre o resultado de UX-09 segue pendente.
No aplicativo local, o cliente pode revisar o onboarding, alternar entre dúvida
e geração no Assistente e abrir as versões da ficha. O instrutor pode incluir um
exercício em um rascunho e consultar o parecer de uma ficha de demonstração.
Atendente e administrador podem conferir cadastros, convites e as opções
visíveis para cada papel. A biometria, a matrícula e os demais módulos futuros
terão suas verificações de interface nas próprias entregas.
