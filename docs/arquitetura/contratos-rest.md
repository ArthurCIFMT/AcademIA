# Convenções REST

FND-06 usa `backend/app/main.py` como ponto de composição para registrar
handlers e middleware de `app/core/`. Os modelos JSON vivem em `app/contracts/`.

`GET /health` é a rota técnica da fundação. Rotas de domínio usam `/api/v1`
e descrevem pedidos e respostas em OpenAPI. Criação síncrona retorna 201,
trabalho aceito para execução posterior retorna 202 e sucesso sem corpo retorna 204.

| HTTP | Código | Significado |
|---|---|---|
| 400 | INVALID_JSON | Corpo JSON malformado |
| 401 | UNAUTHENTICATED | Sessão necessária |
| 403 | FORBIDDEN | Operação sem permissão |
| 404 | NOT_FOUND | Recurso indisponível |
| 409 | CONFLICT | Conflito de estado, como revisão superada |
| 422 | VALIDATION_ERROR | Dados incompatíveis com o contrato |
| 500 | INTERNAL_ERROR | Falha interna |

O corpo de erro tem `code`, `message`, `details` e `correlation_id`.
`details` pode identificar a origem de validação, como `body` ou `query`.
Erros usam mensagens controladas. O log de falha interna registra apenas
o identificador de correlação e a mensagem fixa.

Cada resposta traz `X-Correlation-ID`. Um único UUID válido fornecido pelo
cliente é propagado. Nos demais casos, o servidor gera um UUID.

Consultas paginadas usam `page` a partir de 1 e `page_size` padrão 20,
com máximo 100. Timestamps têm deslocamento explícito na entrada e saem em
ISO 8601 UTC. Datas civis, como nascimento e vencimento, usam `YYYY-MM-DD`.
