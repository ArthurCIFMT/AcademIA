# AUL-02 — Reserva e capacidade de aulas opcionais

## Metadados

- Fase: Extensão opcional.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: AUL-01, GATE-07.
- Requisitos: RN-25; RF complementar de reservas a aprovar.
- Módulos: MOD-09.

## Objetivo e contexto

Entregar reserva e capacidade de aulas opcionais, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/classes/**`
- `backend/tests/classes/**`
- `frontend/src/features/class-booking/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Registrar requisito complementar antes de executar: capacidade, cancelamento e exceção autorizada.
2. Implementar reserva transacional por cliente/ocorrência.
3. Auditar exceções e reverter ocupação conforme política de cancelamento.

## Critérios de aceite

- Duas reservas simultâneas para última vaga não ultrapassam capacidade.
- Duplicidade do mesmo cliente não consome vaga extra.
- Exceção só ocorre com papel/motivo aceitos; cancelamento libera vaga uma vez.

## Testes obrigatórios

BE; INT com concorrência; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Executar enquanto reserva não estiver no escopo ou inventar lista de espera.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
