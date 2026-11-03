# AUL-01 — Agenda de aulas por ocorrências

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: IAM-03, IAM-04.
- Requisitos: RF-30; RN-04, RN-32, RN-33; RNF-14.
- Módulos: MOD-09.

## Objetivo e contexto

Entregar agenda de aulas por ocorrências, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/classes/**`
- `backend/tests/classes/**`
- `frontend/src/features/classes/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Modelar aula e ocorrência com data/hora inequívocas em vez de somente dia da semana.
2. Criar cadastro, alteração, cancelamento e visualização de agenda.
3. Tratar fuso de apresentação e preservar ocorrência cancelada quando houver histórico.

## Critérios de aceite

- Data/horário inválido é recusado.
- Alterar ou cancelar reflete na consulta da agenda.
- Cliente/visitante tem somente visibilidade permitida, sem manutenção administrativa.

## Testes obrigatórios

BE com datas; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Reservas ou recorrência complexa sem requisito aprovado.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
