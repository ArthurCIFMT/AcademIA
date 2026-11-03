# ACS-05 — Frequência e lotação consistentes

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ACS-03.
- Requisitos: RF-23, RF-24; RN-32, RN-33; RNF-17.
- Módulos: MOD-07.

## Objetivo e contexto

Entregar frequência e lotação consistentes, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/attendance/**`
- `backend/tests/access/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Consumir apenas passagem confirmada e manter presença por cliente.
2. Definir eventos fora de ordem, entrada repetida, saída sem entrada e reconciliação antes de processar.
3. Calcular histórico por período e lotação sem valor negativo.

## Critérios de aceite

- Entrada válida conta uma vez; duplicidade não muda total.
- Saída válida encerra presença e não cria número negativo.
- Reprocessar histórico produz mesmo resultado; concorrência não duplica presença.

## Testes obrigatórios

BE com sequências de eventos; INT concorrente; API; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Subtrair cega e cumulativamente todo evento de saída.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
