# VAL-02 — Aceitação e regressão dos módulos finais

## Metadados

- Fase: Entrega final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: VAL-01.
- Requisitos: RNF-07 e critérios dos módulos selecionados.
- Módulos: MOD-00–MOD-12 conforme escopo.

## Objetivo e contexto

Entregar aceitação e regressão dos módulos finais, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/tests/**`
- `frontend/tests/**`
- `docs/testes/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Executar suites dos módulos selecionados e comparar com matriz de aceite.
2. Cobrir autorização direta, concorrência, idempotência, histórico e falhas de serviços pertinentes.
3. Registrar defeitos, limites e resultados sem mascarar teste falho.

## Critérios de aceite

- Cenários críticos passam no ambiente declarado.
- Falha obrigatória mantém entrega pendente e é identificada por requisito.
- Mocks e ensaios reais estão distinguidos no relatório.

## Testes obrigatórios

BE; INT; API; FE; E2E; DB; RAG; IA; INF conforme módulos entregues.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Inventar resultado de teste ou expandir o produto para resolver limitação não aprovada.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
