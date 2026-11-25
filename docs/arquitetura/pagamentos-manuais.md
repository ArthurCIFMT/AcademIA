# Pagamentos manuais — MEM-00

Um administrador com conta e perfil ativos abre **Gerenciar clientes** e
escolhe **Pagamentos de …** no cadastro correspondente. O registro contém
valor simulado em reais, data, meio simulado, referência fictícia e autoria
obtida da sessão. A interface recebe a referência textual. O armazenamento
consiste no identificador informado e nos dados do lançamento.

O valor é positivo, com até duas casas decimais e precisão de 12 dígitos.
A API recebe dinheiro como string decimal e o PostgreSQL usa `numeric(12,2)`.
A data civil do pagamento deve ser igual ou anterior a hoje em São Paulo. A
confirmação do registro e a anulação usam instantes em UTC.

| Estado | Significado |
|---|---|
| `CONFIRMADO` | Lançamento ativo registrado pelo administrador. |
| `ANULADO` | Lançamento retirado do conjunto de confirmações, preservando valor, data, autoria, referência e motivo. |

**Corrigir** anula o lançamento anterior e cria o substituto do mesmo cliente
na mesma transação. Se a nova gravação falhar, o lançamento anterior continua
confirmado. **Anular** registra um motivo e encerra o lançamento. A anulação é
uma operação do registro interno da academia.

Uma referência pode identificar apenas um pagamento manual confirmado no
sistema. A verificação ignora diferenças entre maiúsculas e minúsculas. Após
anulação, a referência pode ser usada no lançamento correto. Reenvio do mesmo
UUID com cliente, autoria e dados iguais devolve o registro existente. Repetir
uma correção ou anulação com conteúdo divergente gera conflito. Auditoria e
alteração financeira são gravadas na mesma transação.

## Contrato REST

Rotas relativas a `/api/v1/admin/clientes/{client_id}/pagamentos`, com sessão
administrativa e `Cache-Control: no-store`. Escritas exigem CSRF.

| Método e sufixo | Operação |
|---|---|
| `GET` | Histórico paginado de registros manuais, com estados, datas e autoria. |
| `POST` | Registrar confirmação, com HTTP 201 ou 200 no reenvio idempotente. |
| `POST /{payment_id}/correcao` | Substituir registro, com HTTP 201 ou 200 no reenvio idempotente. |
| `POST /{payment_id}/anulacao` | Anular com motivo, com HTTP 200. |

Registro e substituição usam `solicitacao_id`, `valor`, `pago_em`, `metodo` e
`referencia_externa`. Correção e anulação requerem `motivo`. IDs de outro
cliente na rota de ajuste retornam HTTP 404. Duplicidade e estado incompatível
retornam HTTP 409, e dados inválidos retornam HTTP 422.

A migration `0025` cria a base `pagamento`. O FIN-01 acrescenta o vínculo
opcional `cobranca_id` com a [cobrança](cobrancas.md) do mesmo cliente. A
correção preserva o vínculo. Matrícula, renovação e acesso continuam
independentes da confirmação financeira.
