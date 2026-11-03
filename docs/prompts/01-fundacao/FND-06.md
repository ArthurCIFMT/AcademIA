# FND-06 — Convenções REST, contratos e testes de API

## Metadados

- Fase: Fundação.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-04, FND-05.
- Requisitos: RNF-04, RNF-06, RNF-07, RNF-15, RNF-16; RN-23, RN-32.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar convenções rest, contratos e testes de api, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/core/**`
- `backend/app/contracts/**`
- `backend/tests/contracts/**`
- `backend/tests/integration/**`
- `AGENTS.md`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Definir envelope de erros, validação JSON, identificador de correlação e datas ISO 8601.
2. Documentar convenções de paginação, HTTP e OpenAPI sem inventar endpoints de domínio.
3. Configurar suites API e INT com resultados legíveis.

## Critérios de aceite

- JSON inválido gera erro coerente sem stack trace ou dado sensível.
- OpenAPI descreve healthcheck e contrato de erro; teste compara resposta ao schema.
- Status 401, 403, 404 e conflito têm convenção distinguível.

## Testes obrigatórios

API; INT; BE; DOC. Registrar comandos reais de contrato e integração.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Implementar autorização de todos os módulos ou regras de negócio futuras.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
