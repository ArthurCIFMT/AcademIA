# Cobranças e consulta financeira — FIN-01

Os valores representam registros didáticos de cobrança e recebimento.
O cliente acessa a [compra simulada de plano](compra-simulada.md) pela área
financeira. Seus recibos têm histórico próprio.

Em **Administração → Gerenciar clientes → Cobranças de …**, o administrador
registra a competência, o vencimento e o valor. A matrícula é opcional e a
seleção lista apenas matrículas desse cliente. Edição, cancelamento e reabertura
gravam uma revisão com autor, data e os campos registrados. O histórico
continua disponível depois do cancelamento.

Em **Minhas cobranças**, o cliente vê as próprias competências, vencimentos,
valores e saldos. O cliente é identificado pela sessão. Instrutores e atendentes
seguem suas permissões operacionais. A manutenção financeira exige o papel de
administrador.

## Estados e cálculo

A competência é representada pelo primeiro dia do mês em ISO 8601. Valores em
reais são strings decimais na API e `numeric(12,2)` no PostgreSQL. A cobrança
aceita zero. Datas civis de vencimento são interpretadas em São Paulo.

| Situação exibida | Regra |
|---|---|
| Em aberto | Lançamento aberto, com saldo, até o próprio dia de vencimento. |
| Vencida | Lançamento aberto, com saldo, após o vencimento. |
| Quitada | Lançamento aberto, com valor integral coberto ou de valor zero. |
| Cancelada | Lançamento cancelado, com saldo exigível zero e pagamentos preservados. |

**Registrar pagamento** na cobrança abre o formulário do MEM-00 já associado.
O valor pago soma pagamentos com estado `CONFIRMADO` e instante de confirmação
registrado. Pagamentos parciais reduzem o saldo. Anulação e correção recalculam
o valor pago na próxima consulta. Tentativas e pagamentos anteriores são
preservados. Uma correção mantém o vínculo original. Os lançamentos anteriores
à migração ficam sem vínculo. A associação é informada no registro de um novo
lançamento.

A opção `ACADEMIA_INADIMPLENCIA=SOMENTE_INFORMATIVA` registra a política
acadêmica. A autorização de entrada continua sendo avaliada pelo motor de acesso.

## REST e JSON

Rotas administrativas começam por `/api/v1/admin/clientes/{client_id}/cobrancas`.
A consulta do cliente é `GET /api/v1/cliente/cobrancas`. As respostas usam
`Cache-Control: no-store`, e a escrita exige sessão e CSRF.

| Rota administrativa | Operação |
|---|---|
| `GET` | Lista paginada das cobranças do cliente. |
| `POST` | Cria cobrança aberta e revisão inicial usando `solicitacao_id`. |
| `GET /matriculas` | Lista paginada das matrículas com modalidade e período. |
| `GET /{charge_id}` | Consulta cobranças dentro do cliente selecionado. |
| `PUT /{charge_id}` | Atualiza campos e estado com a revisão esperada. |
| `GET /{charge_id}/historico` | Lista revisões paginadas com autoria e data. |

Campos de escrita incluem `competencia`, `vencimento`, `valor` e
`matricula_id` opcional. Atualizações também recebem `estado` e `revisao`.
Reenvio da criação devolve o registro existente sem repetir a auditoria.
Revisão desatualizada e UUID conflitante retornam HTTP 409. Dados inválidos
e vínculo de matrícula com outro cliente retornam HTTP 422. A migração `0026`
adiciona vínculos com integridade de cliente e mantém os dados da revisão anterior.
