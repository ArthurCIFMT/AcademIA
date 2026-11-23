# Agenda de aulas — MOD-09

O AUL-01 implementa o RF-30. Cada registro de `aula_ocorrencia` tem nome,
descrição opcional, início, fim, estado e revisão. Nome e descrição pertencem
à ocorrência no modelo lógico aceito. Para anunciar duas sessões da mesma
aula, cadastrar duas ocorrências. Inscrições, lotação e recorrência ficam
fora da agenda básica.

## Interfaces e papéis

| Tela | Acesso | Operações |
|---|---|---|
| `/aulas` | Visitante | Consulta da agenda |
| `/area/cliente/aulas` | Cliente ativo | Consulta pela área do cliente |
| `/area/administracao/aulas` | Administrador ativo | Consulta completa, cadastro, edição e cancelamento com confirmação |

A apresentação usa `America/Sao_Paulo` e `pt-BR`. O formulário recebe datas
e horas locais, converte para um instante inequívoco e preserva a precisão
do valor original quando o horário exibido não muda. O término pode cair
em outro dia. A aplicação rejeita horários locais ambíguos ou inexistentes
na conversão de novos valores.

## Contrato REST/JSON

| Método e rota | Contrato |
|---|---|
| GET `/api/v1/aulas` | Lista ocorrências agendadas cujo término ainda não passou. Ordena por início crescente e desempata por UUID. Retorna `id`, `nome`, `descricao`, `inicio` e `fim`. |
| GET `/api/v1/admin/aulas` | Lista ocorrências, inclusive encerradas ou canceladas, com `estado` e `revisao`. Ordena por início decrescente e desempata por UUID. |
| POST `/api/v1/admin/aulas` | Recebe `nome`, `descricao` opcional, `inicio`, `fim` e `solicitacao_id`. Retorna 201. A mesma solicitação com os mesmos dados pode ser repetida enquanto o registro conservar a revisão inicial. |
| PUT `/api/v1/admin/aulas/{occurrence_id}` | Recebe os campos da aula e a `revisao` consultada. Retorna 200 com a aula atualizada. |
| POST `/api/v1/admin/aulas/{occurrence_id}/cancelamento` | Recebe a `revisao`. Retorna 200 com a ocorrência em estado `CANCELADA`. Repetir com a revisão atual da ocorrência cancelada devolve o estado existente. |

Listas usam `pagina` e `limite` (20 por padrão, até 100). As datas chegam em
ISO 8601 com fuso explícito e são armazenadas em PostgreSQL como
`timestamptz`. A API devolve UTC. Nome tem até 120 caracteres e descrição
até 1000. Datas inválidas ou `fim <= inicio` retornam 422. A revisão
desatualizada, a edição de ocorrência cancelada e o reuso incompatível da
solicitação retornam 409. Um UUID desconhecido para edição ou cancelamento
retorna 404. As rotas administrativas usam sessão e validam papel, origem e
CSRF conforme o contrato comum.

O cancelamento mantém a linha para consulta administrativa e a retira da
agenda pública. Cadastro, edição efetiva e cancelamento registram ação, ator
e correlação com a alteração na mesma transação. O índice por início e UUID
apoia a ordenação da agenda. A etapa reutiliza a API, SPA e PostgreSQL locais
já usados pelo iniciador.
