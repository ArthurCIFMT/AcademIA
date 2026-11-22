# UX-04 · Onboarding por etapas

O convite e a conta do cliente compartilham Objetivos e rotina, Dados físicos,
Saúde e Revisão. O indicador de etapa informa onde o cliente está. A versão e
a revisão do rascunho exibem o estado gravado. Navegar preserva os valores em
memória e a conclusão exige ação explícita na revisão.

| Verificação | Resultado |
|---|---|
| Frontend | 104 testes em 21 arquivos. A suíte existente em `frontend/tests/onboarding/` cobre navegação sem gravação, campos condicionais, foco no campo obrigatório, falha de rede, confirmação e isolamento de convites. |
| E2E-01 · Convite | Edge a 390 px, fragmento removido, página sem navegação da conta, teclado e foco no campo obrigatório, falha no primeiro PATCH, dados mantidos, nova gravação, recarga e conclusão. |
| E2E-04 · Conta | Edge a 390 px, edição por teclado, gravação e retomada de rascunho, revisão dos valores e confirmação da nova versão antes da adaptação do treino. |
| Regressão integrada | Oito jornadas aprovadas no Edge 158.0.4370.33 com API, PostgreSQL de teste e Mailpit. O runner confirmou a reversão dos dados. O LLM foi controlado, sem novas chamadas aos provedores. |
| Inspeção visual | Edição e revisão sem rolagem horizontal a 320, 390, 768 e 1440 CSS px usando fixtures sintéticas. Lint, TypeScript e build passaram. |

| Captura | Evidência |
|---|---|
| Antes | [Formulário da UX-02 a 390 px](../interface/evidencias-ux02/onboarding-390.png) |
| Depois | [Convite a 390 px](../interface/evidencias-ux04/convite-390.png) · [Revisão na conta a 390 px](../interface/evidencias-ux04/revisao-390.png) |

As duas capturas da UX-04 vêm das jornadas integradas e usam dados sintéticos.
O dispositivo móvel foi emulado no Edge. Testes em aparelho físico e o aceite
visual completo seguem no roteiro de UX-09. A entrega não exigiu mudanças
no iniciador, nos serviços ou em suas configurações.

## Reprodução

Em `frontend/`, executar `npm test -- --maxWorkers=2`, `npm run lint`,
`npm run typecheck` e `npm run build`. Para os fluxos integrados, seguir o
[runner E2E](aceitacao-mvp.md) com uma pasta de saída nova. Os cenários E2E-01
e E2E-04 registram as capturas com o prefixo `ux04-`. Para inspecionar as
quatro larguras, usar o [verificador visual](../interface/verificar-ux02.cjs)
conforme os [comandos de reprodução](ux02-base-visual.md#reprodução).
