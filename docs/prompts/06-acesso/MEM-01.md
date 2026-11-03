# MEM-01 — Planos e matrícula manual mínima

## Metadados

- Fase: Pós-MVP / base do acesso.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, PES-02, IAM-04, GATE-08.
- Requisitos: RF-31 parcialmente; RN-22, RN-35, RN-36.
- Módulos: MOD-08.

## Objetivo e contexto

Entregar planos e matrícula manual mínima, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/memberships/**`
- `backend/tests/memberships/**`
- `frontend/src/features/memberships/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar plano ativo/inativo e matrícula manual com início, término, modalidade e limites.
2. Definir unidade/janela dos acessos e regra de expiração com responsável antes de codificar.
3. Expor consulta de validade por contrato ao módulo de acesso.

## Critérios de aceite

- Plano inativo não origina matrícula nova.
- Matrícula inexistente, futura ou vencida não é retornada como válida.
- Renovação manual registra autor e preserva histórico sem depender de pagamento.

## Testes obrigatórios

BE com relógio controlado; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Checkout, webhook financeiro e exigência de cartão.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
