# 05 — Matrícula e acesso na ficha do cliente

## Tarefa

Reunir matrícula, consulta da compra simulada e cadastro facial em **Atendimento → Clientes → Matrícula e acesso**, mantendo a pessoa selecionada ao alternar as ações.

## Escopo permitido

- `frontend/src/features/clients/`, `memberships/`, `biometrics/` e navegação/rotas da área de atendimento em `frontend/src/app/`.
- `backend/app/modules/memberships/`, composição de acesso pertinente em `backend/app/modules/access/` e contrato de leitura de recibo em `backend/app/modules/billing/` apenas se necessário. Preserve o módulo dono de cada dado.
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

BE/INT das regras e contratos de módulos envolvidos, FE da ficha de atendimento e E2E de matrícula, foto, entrada e saída. Inclua confirmação de compra simulada e ausência de pagamento. Consulte `docs/testes/comandos.md`. Registre uso de serviços reais versus dublês. Próximo 06 na ordem proposta.
