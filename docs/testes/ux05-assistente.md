# UX-05 · Assistente e fichas de treino

A área do cliente oferece três ações na mesma navegação. **Tirar dúvida**
consulta fontes do RAG e mantém a conversa no histórico. **Gerar ficha**
faz a solicitação de geração existente e mostra seu estado salvo.
**Adaptar um dia** exige selecionar o dia da ficha vigente e confirmar
os dados do onboarding. Os links diretos da geração e do histórico
continuam funcionando.

## Verificações

- **Frontend.** 108 testes em 21 arquivos, com cenários de idempotência,
  quota, abstenção, fontes, confirmação de adaptação e recusa de acesso
  enquanto outra requisição ainda está em andamento. Lint, TypeScript e
  build aprovados.
- **Navegador com fixtures.** Edge 158.0.4370.33 a 320, 390, 768 e
  1440 CSS px. A ação principal e a área de conteúdo permanecem
  acessíveis nas telas de dúvida e consulta de quota.
- **Jornadas integradas.** Oito jornadas aprovadas na segunda execução,
  com reversão do banco de teste confirmada. E2E-02 verifica dúvida, fonte e isolamento de
  contas, E2E-03 exercita a cota HTTP e a consulta posterior, E2E-04
  conta os POSTs da interface e confirma geração e adaptação com
  versão-base, e E2E-07 verifica indisponibilidade da IA e treino
  manual. A primeira execução usou seletores de mensagem do formulário
  anterior. A rodada seguinte seleciona o campo pelo nome acessível.

| Tela | Captura a 390 CSS px com dados sintéticos |
|---|---|
| Dúvida | [Resposta e fonte](../interface/evidencias-ux05/duvida-390.png) |
| Geração | [Ficha publicada e parecer pendente](../interface/evidencias-ux05/geracao-390.png) |
| Adaptação | [Dia-alvo e confirmação dos dados](../interface/evidencias-ux05/adaptacao-390.png) |

Os testes usam IA controlada, sem consumir quota de provedores.
O iniciador permanece compatível, pois o frontend usa os mesmos
serviços, portas e comandos locais.

## Reprodução

Em `frontend/`, executar `npm test -- --maxWorkers=2`,
`npm run lint`, `npm run typecheck` e `npm run build`. Para navegador
com API Python, PostgreSQL e Mailpit de teste, usar o
[runner E2E](aceitacao-mvp.md) com uma pasta nova. O
[verificador visual](../interface/verificar-ux02.cjs) complementa
as jornadas nas quatro larguras com fixtures sintéticas.
