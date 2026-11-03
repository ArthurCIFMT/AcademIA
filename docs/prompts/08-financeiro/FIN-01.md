# FIN-01 — Cobranças e consulta financeira

## Metadados

- Fase: Financeiro tardio.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: MEM-01, IAM-04.
- Requisitos: RF-26, RF-27; RN-04, RN-05, RN-24, RN-33.
- Módulos: MOD-08.

## Objetivo e contexto

Entregar cobranças e consulta financeira, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/billing/**`
- `backend/tests/billing/**`
- `frontend/src/features/billing/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Definir estados/competência/vencimento/valor e vínculo à matrícula/cliente.
2. Criar manutenção administrativa e consulta própria autorizada.
3. Manter tentativas e histórico; regra de inadimplência deve ser configuração explícita.

## Critérios de aceite

- Registro/atualização válido persiste na cobrança correta.
- Cliente não consulta cobrança de outro e atendente segue matriz aceita.
- Valores e datas inválidos não deixam lançamento parcial.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Gateway real, contabilidade completa e cálculo de lucro.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
