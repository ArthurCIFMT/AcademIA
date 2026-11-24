# Frequência e lotação — ACS-05

Só entra na frequência um evento `PASSAGEM_SIMULADA` da origem
`CATRACA_SIMULADA` associado a um comando `CONFIRMADO`. A confirmação e a
reconciliação das presenças do cliente acontecem na mesma transação.
A [autorização de acesso](autorizacao-acesso.md) continua com seu próprio
controle de entradas confirmadas e reservas para aplicar o limite diário.

| Passagem na sequência do cliente | Resultado | Efeito |
|---|---|---|
| Entrada sem presença aberta | `ENTRADA_REGISTRADA` | Abre uma presença |
| Entrada com presença aberta | `ENTRADA_REPETIDA` | Preserva a presença aberta |
| Saída com presença aberta | `SAIDA_REGISTRADA` | Encerra a presença |
| Saída sem presença aberta | `SAIDA_SEM_ENTRADA` | Mantém a lotação |

O processamento ordena pelo instante da ocorrência em UTC. No mesmo instante,
a entrada precede a saída, e o UUID do evento ordena passagens da mesma direção.
Uma passagem atrasada aceitada pelo contrato do callback recalcula a sequência
do cliente. O resultado derivado em `evento_acesso.resultado_presenca` pode
mudar nessa reconciliação. O evento original e seu vínculo com o comando são
preservados. O mesmo retorno recebido novamente é idempotente.

A lotação é a contagem de presenças abertas, inclusive quando uma visita cruza
a meia-noite. A ausência de uma saída confirmada mantém a visita aberta.
O PostgreSQL impede mais de uma presença aberta por cliente. O identificador
da presença é o evento de entrada e permanece estável ao associar a saída.

O MOD-07 fornece consultas internas tipadas de lotação e frequência.
O histórico seleciona visitas pela hora da entrada, em intervalo inclusivo no
início e exclusivo no fim, e retorna início, eventual saída e total paginado.
A ordem é da entrada mais recente para a mais antiga, com desempate pelo UUID.
ACS-06 define as rotas e telas de frequência, e DSH-01 consome os indicadores
no painel administrativo.

A migration `0024` preenche a projeção a partir de passagens já confirmadas.
Seu downgrade elimina a projeção. Os eventos e comandos continuam disponíveis
para reconstrução em nova aplicação da migration.
