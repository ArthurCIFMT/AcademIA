# 06 — Idade durante o onboarding

## Tarefa

Mostrar a idade atual durante o preenchimento, tanto pelo convite válido quanto pelo editor do cliente autenticado. Preservar a idade registrada ao concluir cada versão.

## Escopo permitido

- `backend/app/modules/onboarding/` e leitura cadastral mínima por contrato em `backend/app/modules/people/`, quando necessária.
- `frontend/src/features/onboarding/`, `backend/tests/onboarding/`, `frontend/tests/onboarding/` e jornada E2E afetada.
- Contratos de leitura, RF-11/13/14, especificação de onboarding, evidências e fontes do SPEC diretamente afetados.

Não introduza campo editável, duplicação persistente da idade, migration para idade, alteração de snapshot existente ou mudança da triagem neste cartão.

## Contexto e execução

Depende de 01. Leia ONB-02/03 e `docs/requisitos/onboarding-e-triagem.md`. O backend calcula idade em anos completos com data civil de São Paulo ao concluir. A interface exibe a idade do snapshot concluído. Disponibilize **Idade atual** como dado de leitura derivado do cadastro onde se edita o onboarding. O contrato deve funcionar antes de existir qualquer versão concluída e respeitar a consulta pelo convite válido.

No DTO do rascunho/leitura, exponha apenas a idade calculada necessária à tela. Preserve destino, expiração e titularidade do token. Ao concluir, mantenha `idade_snapshot` com o cálculo do momento. O histórico exibe **Idade na conclusão** e a IA continua usando o snapshot conforme contrato.

## Critérios de aceite

- Convite válido e editor autenticado mostram idade mesmo na primeira versão, sem pedir ao cliente para digitá-la. Os dados são calculados no backend conforme a regra de São Paulo.
- Correção do nascimento no cadastro afeta a próxima leitura atual. Versão já concluída mantém o valor histórico.
- Convite expirado, token de outro cliente e acesso alheio continuam recusados. Data de nascimento não é incluída no resumo de IA nem exposta no novo campo de leitura.

## Testes e entrega

BE/INT de contrato, ano/aniversário/fuso, convite e persistência. FE de formulário e tela concluída. E2E focado de convite e edição. Consulte `docs/testes/comandos.md` para as suites de onboarding. Próximo 07.
