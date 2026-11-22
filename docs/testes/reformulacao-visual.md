# Validação da reformulação visual

Status: UX-01 a UX-05 verificados. Consulte a
[linha de base](ux01-referencia-visual.md) e a
[verificação dos componentes e das telas existentes](ux02-base-visual.md),
além dos ensaios de [navegação e acesso](ux03-navegacao-e-acesso.md),
[onboarding por etapas](ux04-onboarding-etapas.md)
e [Assistente](ux05-assistente.md).
O aceite da aplicação redesenhada segue a trilha abaixo.
Fonte: [critérios de experiência](../requisitos/experiencia-e-interface.md).

## Ambiente e dados

Para a linha de base visual de UX-01, usar build do MVP com HTTP interceptado
e fixtures sintéticas, conforme o relatório. Nos testes integrados, usar
React/Vite e o backend existentes, PostgreSQL academia_test e fixtures
sintéticas, com Mailpit quando o fluxo exigir. Não apagar ou usar o banco de
desenvolvimento para a preparação automatizada. Preservar chaves, fotos e dados
reais fora de capturas/commits. IA controlada serve para verificar interação e
contagem de chamadas; não aprova qualidade do modelo nem substitui AI-06 real.
Não reexecutar o LLM real para conferir cores, navegação ou espaçamentos.

## Verificação por cartão

| Etapa | Evidência mínima esperada na execução |
|---|---|
| UX-01 | Inventário de telas e rotas atuais; plano e protótipos locais de cliente, instrutor e administração, incluindo onboarding/assistente; linha de base sintética no navegador. |
| UX-02 | Exemplos dos componentes e estados, contraste medido e testes de interação/foco dos componentes interativos novos. |
| UX-03 | Navegação desktop/móvel para quatro papéis e papéis acumulados; links diretos, logout e recusa de API preservados. |
| UX-04 | Formulário por etapas em convite e conta, campos condicionais, rascunho/retomada, confirmação de nova versão e falha de rede. |
| UX-05 | Dúvida, fontes, geração e adaptação pelos contratos corretos; quota/abstenção/bloqueio; zero geração causada por abrir tela ou consultar estado. |
| UX-06 | Ficha atual por dia, histórico, parecer, exportação e conteúdo expirado, inclusive a 390 px. |
| UX-07 | Designação vigente, avaliação, edição manual, conflito, publicação e parecer posterior; dados de outro cliente inacessíveis. |
| UX-08 | Cadastros/listagens, pesquisa/paginação existentes, validação e disponibilidade de equipamentos; nada de falso dashboard ou menu financeiro sem implementação. |
| UX-09 | Jornadas integradas, teclado, ampliação, viewports, capturas comparáveis e relatório com defeitos e limitações. |

Medir larguras 320/390/768/1440 e texto a 200%; inspecionar contraste/foco e
descrever o método. Registrar navegador/versão e tamanho da janela. Capturas de
protótipo são identificadas como protótipo; só capturas do aplicativo exercitado
comprovam o resultado da implementação. Comparar pelo menos entrada/navegação,
onboarding, assistente, ficha, editor/revisão e cadastro administrativo.
Não criar teste que confira somente valores de CSS repetindo a implementação.
Imagens de referência sintéticas não são comprovação de segurança/usabilidade.

## Comandos existentes

Em frontend/, selecionar arquivos pertinentes com npm test -- <caminhos> e
executar npm run lint, npm run typecheck e npm run build. Em UX-09 executar a
regressão completa npm test -- --maxWorkers=1. Não escrever uma nova suíte
equivalente quando um teste existente já cobre o comportamento relevante.

E2E existente: ler [aceitação do MVP](aceitacao-mvp.md) e
[comandos reais](comandos.md). Iniciar Mailpit e academia_test conforme o guia,
definir ACADEMIA_E2E=1 e, em backend/, executar:

```powershell
uv run --locked --env-file ../.env python -m tests.acceptance --output ./data/e2e/ux-rodada-N
```

A pasta deve ser nova; não sobrescrever relatórios anteriores. O executor controla
API/navegador/fixtures. npm run test:e2e isolado exige variáveis fornecidas por
ele; não anunciar comando inventado para uma suíte visual ainda inexistente.
Se um cartão acrescentar cenários ao harness, registrar os seletores e comandos
quando existirem. Usar timeout e tentativas explícitos, sem mascarar falhas.

## Registro e aceite

Cada implementação registra arquivos, comandos/resultados, capturas sintéticas
antes/depois, cenários/estados observados e limitações. Em UX-09 montar relatório
de cobertura por tela/perfil/critério, incluindo feedback manual quando disponível.
Revisão do responsável é recomendada, mas ausência de feedback não vira aprovação
presumida nem impede verificações independentes já autorizadas. Não declarar
UX-09 concluído com falha obrigatória ou somente com mockups/testes unitários.
Relatórios AI-06/TST-01 históricos conservam seus hashes; não são alterados para
parecer que exercitaram uma interface nova. Falhas de API ou requisito novo
descobertos são registrados para uma entrega funcional própria.
