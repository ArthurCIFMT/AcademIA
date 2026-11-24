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

## Consultas e telas — ACS-06

| Consulta autenticada | Permissão e retorno |
|---|---|
| `GET /api/v1/acesso/lotacao` | Qualquer perfil autenticado. Retorna somente `total_presentes`. |
| `GET /api/v1/cliente/frequencia` | Perfil de cliente. O sistema deriva a identidade da sessão. |
| `GET /api/v1/clientes/{client_id}/frequencia` | Administrador ou atendente. A consulta aceita cadastro existente, inclusive inativo para preservar o histórico. |

As respostas têm `Cache-Control: no-store`. O histórico contém nome do cliente,
datas do recorte, paginação, total e a lista de visitas com ID, entrada e eventual
saída em ISO 8601 UTC. O parâmetro `de` e o parâmetro `ate` são datas civis
inclusivas em São Paulo, com seleção pela data de entrada. Sem parâmetros de data,
a API consulta os últimos 30 dias, incluindo hoje. A ordem é decrescente pela
entrada e pelo ID. A página começa em 1, e o limite padrão é 20, com máximo de 100.
O estado sem visitas retorna lista vazia e total zero.

No menu da área, **Lotação atual** mostra o total e permite nova consulta por
**Atualizar lotação**. **Minha frequência** abre o histórico do próprio cliente.
Atendente e administrador usam o link **Frequência de …** na lista de clientes.
O backend valida cada consulta. Exibição dos horários da academia, filtros,
estado vazio e paginação usam a mesma interface em desktop e celular.

Na área de atendimento, após **Cliente identificado**, o botão **Solicitar autorização**
chama o motor existente. **Consultar passagem** atualiza o estado do comando. Após
a confirmação externa pela catraca fictícia, uma nova consulta ao histórico e à lotação
reflete o evento. A interface conserva o fluxo auditado de identificação manual.
O [painel administrativo](painel-administrativo.md) consome a lotação e a frequência por data e hora pelo contrato de leitura do MOD-07.

A migration `0024` preenche a projeção a partir de passagens já confirmadas.
Seu downgrade elimina a projeção. Os eventos e comandos continuam disponíveis
para reconstrução em nova aplicação da migration.
