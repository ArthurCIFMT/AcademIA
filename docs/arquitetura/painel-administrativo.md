# Painel administrativo — DSH-01

O início da **Área administrativa** apresenta os indicadores da academia e
mantém os avisos pendentes. O botão **Atualizar indicadores** faz uma nova
consulta. As séries têm valores legíveis em texto e permitem escolher o dia
para consultar as faixas de uma hora, inclusive em tela pequena.

| Indicador | Definição e origem |
|---|---|
| Clientes ativos | Conta e perfil ativos com papel efetivo de cliente, conforme MOD-01. |
| Clientes com matrícula vigente | Pessoas distintas com matrícula ativa, no período contratado inclusivo, conforme MOD-08. A contagem inclui contas convidadas com matrícula vigente e independe do pagamento. |
| Funcionários cadastrados | Total de perfis de funcionário mantidos pelo MOD-01, incluindo cadastros inativos. |
| Pessoas presentes agora | Presenças abertas confirmadas pelo MOD-07. |
| Frequência semanal | Entradas de visitas confirmadas nas quatro semanas civis mais recentes, incluindo a atual. Cada semana começa na segunda-feira. |
| Frequência por dia e hora | Totais dos últimos sete dias civis, incluindo hoje. Para cada dia, detalha a quantidade de visitas por hora de entrada. |

A academia usa o fuso `America/Sao_Paulo`. A frequência inclui uma visita
quando seu instante de entrada está no recorte e é igual ou anterior ao instante
da consulta. Datas civis são ISO 8601 e o instante de consulta é informado em UTC.
Entradas repetidas, reconhecimento sem passagem e saídas sem entrada não criam
visitas. Dias e semanas sem visitas retornam zero. O detalhamento horário lista
somente as horas com visitas.

## Contrato REST

`GET /api/v1/admin/dashboard` usa a sessão do navegador e exige o papel
administrativo efetivo. Uma sessão ausente recebe HTTP 401 e um perfil sem
permissão recebe HTTP 403. A resposta válida usa `Cache-Control: no-store`.
Cada indicador tem `estado: DISPONIVEL` e `valor`, ou
`estado: INDISPONIVEL` quando a leitura falha. As leituras são isoladas em
transações e os demais indicadores continuam disponíveis numa falha parcial.
A resposta e os logs usam somente agregados e o nome técnico do indicador em
falha. Identidades, referências faciais e conteúdo de exceções ficam fora
do contrato.

O MOD-11 calcula os indicadores sob demanda pelas portas de leitura do MOD-01,
MOD-07 e MOD-08. O escopo financeiro pertence ao FIN-03.
