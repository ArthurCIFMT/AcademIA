# Confirmação manual de identidade — ACS-04

Em **Atendimento → Reconhecimento facial**, uma tentativa não identificada
oferece a opção **Confirmar identidade manualmente**. O atendente localiza o
cliente, confere sua identidade e registra um motivo de até 240 caracteres
antes de solicitar a autorização.

A confirmação só pode partir de uma falha facial recente. A janela é a mesma
usada pelo motor, inicialmente de 60 segundos. Rosto desconhecido, score abaixo
do limite, ambiguidade, captura inválida ou falha do provedor permitem o fluxo.
A direção vem da tentativa original e a imagem permanece fora da solicitação.

## REST

`POST /api/v1/atendimento/acessos/{event_id}/confirmacao-manual` exige sessão de
atendente e CSRF. `event_id` é o ID interno da tentativa facial. A entrada contém
`cliente_id`, `motivo` e `identidade_confirmada: true`. O resultado contém o
ID da falha, a origem `ATENDIMENTO_MANUAL` e o recibo normal da decisão.
[Autorização e comando](autorizacao-acesso.md).

- HTTP 201 registra a confirmação. HTTP 200 repete o recibo com os mesmos
  dados e o mesmo atendente, inclusive depois da janela. Um envio pendente
  ou com falha reutiliza o UUID do comando se ainda estiver vigente.
- HTTP 409 indica tentativa já utilizada com dados diferentes ou resultado
  facial que não permite alternativa. HTTP 410 indica prazo vencido para
  registrar a primeira confirmação. HTTP 422 cobre motivo ou confirmação
  inválidos. HTTP 404 indica tentativa ou cliente indisponível.
- O motor aplica as regras vigentes de cada direção. Na entrada, exige conta
  e perfil de cliente ativos, matrícula vigente, modalidade e limite diário.
  Aceitação do comando pela catraca permanece distinta da passagem.

## Trilha de auditoria

A migration 0023 adiciona `identificacao_manual`. Em uma transação, o sistema
preserva a falha original, cria o evento `IDENTIFICACAO_MANUAL`, vincula
atendente e motivo e registra a decisão, o comando e a auditoria. Uma falha
admite uma única confirmação. A interface e a API do atendente permitem
registrar e reenviar essa operação. O motivo detalhado fica na trilha privada,
com a ação e o código do motivo no registro de auditoria.

A passagem permanece no contrato autenticado da catraca. O vínculo pelo
comando e pela decisão qualifica a origem manual, e o mesmo evento de passagem
é contabilizado uma só vez. A falha biométrica e a confirmação continuam
consultáveis tecnicamente no histórico vinculado.
