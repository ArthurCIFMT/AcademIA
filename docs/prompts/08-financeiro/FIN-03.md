# FIN-03 — Indicadores financeiros

## Metadados

- Fase: Financeiro tardio.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FIN-02, DSH-01.
- Requisitos: RF-28, RF-29; RN-04, RN-28, RN-32.
- Módulos: MOD-08, MOD-11.

## Objetivo e contexto

Entregar indicadores financeiros, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/dashboard/**`
- `backend/tests/dashboard/**`
- `frontend/src/features/dashboard/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Adicionar valores cobrados, recebidos, pendentes e vencidos por período.
2. Exibir mensal, anual e total com regra temporal explícita.
3. Respeitar tentativas e estornos definidos para não contar webhook ou tentativa como receita.

## Critérios de aceite

- Totais conferem com pagamentos confirmados de fixture e não duplicam tentativa.
- Faturamento e receita recebida são identificados separadamente.
- Datas nas bordas do período e permissões produzem resultados corretos.

## Testes obrigatórios

BE com cálculo monetário; INT; API; FE.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Lucro sem módulo de despesas ou contabilidade fiscal.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
