# DSH-01 — Dashboard administrativo base

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: PES-02, PES-01, ACS-05, MEM-01, IAM-04.
- Requisitos: RF-28, RF-29; RN-04, RN-23, RN-28, RN-34.
- Módulos: MOD-11.

## Objetivo e contexto

Entregar dashboard administrativo base, respeitando os critérios abaixo.
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

1. Consolidar clientes ativos/assinantes, funcionários, frequência semanal e por dia/hora, lotação.
2. Consultar módulos por contratos de leitura, sem assumir ownership dos dados.
3. Separar erro por indicador; cartões financeiros entram depois de FIN-03.

## Critérios de aceite

- Indicadores conferem com fixtures conhecidas e intervalos temporais.
- Usuário não autorizado é recusado via API e tela.
- Falha em um indicador não mostra dado alheio e não expõe biometria.

## Testes obrigatórios

BE; INT; API; FE com zero, erro parcial e dados conhecidos.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Chamar receita de lucro ou exigir módulos fora das dependências aprovadas do dashboard.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
