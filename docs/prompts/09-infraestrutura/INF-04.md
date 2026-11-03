# INF-04 — Instalação e teste integrado em Docker

## Metadados

- Fase: Infraestrutura final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: INF-03, TST-01.
- Requisitos: RNF-07, RNF-10, RNF-11, RNF-12.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar instalação e teste integrado em docker, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `docs/instalacao/**`
- `frontend/tests/e2e/**`
- `backend/tests/acceptance/**`
- `infra/**`
- `docs/testes/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Reproduzir instalação em ambiente limpo identificado, com inicialização e migrations.
2. Reexecutar cenário crítico do MVP e integrações selecionadas no Compose.
3. Documentar backup/restauração e diferenças entre setup local e containerizado.

## Critérios de aceite

- Outra instalação reproduz a aplicação a partir do repositório e instruções.
- Dados sobrevivem reinício; migrations não duplicam estruturas.
- Mesmo fluxo de aprovação/isolation passa no ambiente containerizado.

## Testes obrigatórios

INF; E2E; API; INT; suites críticas pertinentes.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Declarar ambiente limpo testado sem tê-lo executado.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
