# ACS-04 — Liberação manual auditada

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ACS-03, FND-08, IAM-04, GATE-08.
- Requisitos: RN-08, RN-09, RN-27, RN-35, RN-36.
- Módulos: MOD-07, MOD-12.

## Objetivo e contexto

Entregar liberação manual auditada, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/manual/**`
- `backend/tests/access/**`
- `frontend/src/features/manual-access/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Definir com responsável se alternativa manual substitui só identificação ou permite exceções adicionais.
2. Implementar solicitação por papel autorizado, motivo obrigatório e auditoria durável.
3. Preservar exigência de matrícula e regras enquanto nenhuma exceção explícita estiver aprovada.

## Critérios de aceite

- Falha facial permite alternativa apenas conforme política aceita.
- Motivo ausente/papel indevido é recusado.
- Autor não apaga evidência; evento confirmado manual não duplica passagem existente.

## Testes obrigatórios

BE; INT; API; FE.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Bypass genérico de matrícula/validade ou exceção criada pelo agente.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
