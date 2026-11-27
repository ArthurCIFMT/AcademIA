# 06 — Idade durante o onboarding

**Estado da entrega: CONCLUÍDO.** Idade atual e idade na conclusão verificadas em sessão e por convite.

Ao reusar o cartão, execute primeiro a verificação focal. A correção fica limitada aos caminhos abaixo e depende de uma regressão reproduzida.

## Tarefa

Mostrar a idade atual durante o preenchimento, tanto pelo convite válido quanto pelo editor do cliente autenticado. Preservar a idade registrada ao concluir cada versão.

## Escopo permitido

- `backend/app/modules/onboarding/` apenas para o cálculo e os contratos de leitura da idade, e `backend/app/modules/people/onboarding_directory.py` apenas para a leitura cadastral usada nesse cálculo.
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

Em `backend/`, prepare PostgreSQL e Mailpit isolados e habilite o ensaio de e-mail no processo de teste:

```powershell
$env:ACADEMIA_TEST_MAILPIT = '1'
uv run --locked pytest -o addopts='' tests/onboarding/test_onboarding.py::test_age_changes_on_birthday tests/onboarding/test_onboarding.py::test_own_draft_completion_and_version_confirmation tests/onboarding/test_onboarding.py::test_invite_from_mailpit_resumes_and_completes_only_the_linked_draft tests/onboarding/test_onboarding.py::test_expired_invite_and_other_credential_are_refused
```

Em `frontend/`:

```powershell
npm test -- tests/onboarding/Onboarding.test.tsx tests/onboarding/form.test.ts
```

No Edge, E2E-01 verifica o convite e o preenchimento. Confira **Idade atual** antes de concluir com uma conta sintética e consulte a versão concluída depois. A idade histórica deve continuar a mesma após uma correção cadastral. O caso com Mailpit precisa executar para comprovar a jornada do convite.
