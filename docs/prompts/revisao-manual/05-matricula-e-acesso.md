# 05 — Matrícula e acesso na ficha do cliente

**Estado da entrega: CONCLUÍDO.** Fluxo de atendimento entregue e verificado no Edge com catraca simulada.

Ao reusar o cartão, execute primeiro a verificação focal. A correção fica limitada aos caminhos abaixo e depende de uma regressão reproduzida.

## Tarefa

Reunir matrícula, consulta da compra simulada e cadastro facial em **Atendimento → Clientes → Matrícula e acesso**, mantendo a pessoa selecionada ao alternar as ações.

## Escopo permitido

- `frontend/src/features/clients/`, `memberships/`, `biometrics/` e navegação/rotas da área de atendimento em `frontend/src/app/`.
- `backend/app/modules/memberships/` apenas para o estado ou a consulta da matrícula. O resumo do recibo pertence a `backend/app/modules/billing/payments/checkout_http.py`. Em `backend/app/main.py`, ajuste apenas o registro de `attendant_checkout_router`. Preserve o contrato de reconhecimento e decisão do módulo de acesso.
- Testes de matrícula, acesso, compra simulada, autorização e E2E de atendimento. Documentação de RF-22/31, RN-24/35/36 e contratos afetados.

Pagamento real, mudança da política financeira e redistribuição de papéis do checkout ficam fora deste cartão. Preserve contas, histórico, códigos públicos do motor de acesso e o caminho manual auditado.

## Contexto e execução

Depende de 01, 02 e 04. Leia RF-22/31/37, RN-08/09/24/35/36, MEM-01, FIN-02 e ACS-01/03/04/06. Mostre estado da matrícula, ação para registrar/renovar e situação da referência facial no mesmo contexto. Se o recibo simulado estiver acessível no fluxo aprovado, exponha ao atendente autorizado apenas o resumo necessário por contrato tipado. A compra continua simulada e independente da matrícula. Atendente pode registrar sem pagamento confirmado.

Após matricular, conduza ao cadastro facial obrigatório para habilitar a entrada facial. Matrícula gravada sem referência válida exibe **Biometria pendente**. A captura de chegada e o retorno da catraca ficam identificados como ações separadas. Mantenha um retorno à lista com filtros e cliente selecionado quando aplicável. Se a navegação alterar URLs antigas, preserve destino equivalente.

## Critérios de aceite

- O atendente encontra o cliente e alterna entre informações, matrícula e biometria sem recolher a lista a cada ação. Voltar recupera contexto e filtros.
- Matrícula com ou sem pagamento pode ser registrada pelo atendente. Confirmação simulada não cria matrícula automaticamente. Antes da referência confirmada, a entrada facial continua pendente.
- Após referência e matrícula válidas, a chegada segue reconhecimento, autorização e passagem simulada nessa ordem. Lotação/frequência mudam somente com a passagem confirmada. A contingência continua auditada.
- O backend valida consulta e escrita. Acesso direto à URL exige as mesmas permissões.

## Testes e entrega

Em `backend/` com PostgreSQL isolado, configure o Edge e o Node 24 como em `docs/testes/comandos.md`:

```powershell
uv run --locked pytest -o addopts='' tests/memberships/test_memberships.py tests/billing/test_checkout.py
$env:ACADEMIA_E2E_ACCESS = '1'
uv run --locked pytest -o addopts='' tests/access/test_browser_access.py::test_edge_access_journey
```

Em `frontend/`:

```powershell
npm test -- src/features/memberships/Memberships.test.tsx src/features/attendance/Attendance.test.tsx src/features/biometrics/ClientBiometrics.test.tsx
```

Verifique que a compra aparece como simulada, que o atendente matricula sem pagamento e que um cliente não consulta o resumo do recibo administrativo. Confira no Edge o retorno ao mesmo cliente, aba e filtro após abrir frequência. A lotação muda só após a passagem confirmada pelo simulador. Use o cartão 04 para o ensaio de reconhecimento real. Use o cartão 11 para a prova específica de matrícula com as tabelas financeiras ausentes.
