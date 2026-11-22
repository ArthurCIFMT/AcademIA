# UX-07 · Área de trabalho do instrutor

## Regressão antes de implementar

O commit `61609b8` foi verificado antes de alterar arquivos. Passaram 112
testes de frontend e oito jornadas no Edge, com o PostgreSQL de teste
revertido ao final. Os casos abaixo complementaram o caminho usual.

| Fluxo | Comportamento verificado |
|---|---|
| Convite restrito | Rascunho retido após falha de rede, retomada do formulário e recusa de gravação quando outra aba troca o vínculo de convite. |
| Acesso e sessão | Sessão de outra conta não lê histórico alheio, CSRF anterior não funciona e o mesmo usuário alterna papéis permitidos no celular. |
| Assistente | Triagem grave, dados ausentes e desconhecidos, limite de uso e resposta atrasada após recusa de acesso. A consulta do recibo não reenvia geração. |
| Fichas | Mudança de dia sem nova leitura, exportação autorizada, expiração entre listagem e leitura e remoção de rejeitada anterior. |
| Operação manual | Instrutor publica ficha durante indisponibilidade da IA. Recurso alterado entre rascunho e publicação gera conflito. |

## Entrega e verificação

A lista de clientes designados abre avaliação ou fichas. As observações
históricas e os dados do onboarding ficam em seções recolhidas. O
editor mostra dias, exercícios e revisão do rascunho. A revisão técnica
da ficha identifica cliente e versão e distingue publicação e parecer.

- **Frontend.** 115 testes aprovados, incluindo 20 nos componentes
  de designação, avaliação, rascunho e parecer. Lint, TypeScript e
  build aprovados. Os novos testes verificam o descarte explícito
  após conflito e a retirada dos dados da tela após recusa de acesso.
- **Leitura no navegador.** O verificador sintético conferiu as rotas
  existentes, incluindo a revisão do instrutor, a 320, 390, 768 e 1440
  CSS px no Edge 158.0.4370.33.
- **Integração.** Oito jornadas aprovadas e reversão do banco confirmada.
  E2E-01 parte de **Meus clientes**, abre e recolhe o onboarding pelo
  teclado, registra avaliação, publica e registra parecer. Depois da
  troca de responsável, o antigo instrutor perde acesso à revisão e
  ao editor e o novo abre a área de fichas desse cliente. E2E-06 verifica o
  409 de publicação com equipamento indisponível e o rascunho ainda
  consultável. E2E-07 confirma publicação manual durante falha da IA.

| Captura | Evidência sintética |
|---|---|
| Antes | [Revisão original a 390 px](../interface/evidencias-ux01/antes/parecer-390.png) |
| Avaliações | [Onboarding recolhido e histórico a 390 px](../interface/evidencias-ux07/avaliacoes-390.png) |
| Publicação | [Cliente, versão e confirmação a 390 px](../interface/evidencias-ux07/publicacao-390.png) |
| Conflito | [Recusa com rascunho preservado a 390 px](../interface/evidencias-ux07/conflito-390.png) |

A SPA continua usando FastAPI e os contratos JSON existentes. O iniciador
permanece compatível com os serviços e comandos locais. As jornadas usam
fixtures sintéticas, PostgreSQL de teste, Mailpit e IA controlada.

Em `frontend/`, executar `npm test -- --maxWorkers=2`,
`npm run lint`, `npm run typecheck` e `npm run build`.
Para repetir as jornadas, usar o [runner E2E](aceitacao-mvp.md) com
uma pasta nova. O [verificador visual](../interface/verificar-ux02.cjs)
complementa os testes em quatro larguras.
