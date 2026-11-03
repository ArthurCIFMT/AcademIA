# RAG-05 — Recuperação, citações e avaliação vetorial

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: RAG-04.
- Requisitos: MRF02, MRF11, MRF12, MRF15; RN-29; RNF-13.
- Módulos: MOD-05.

## Objetivo e contexto

Entregar recuperação, citações e avaliação vetorial, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/knowledge/retrieval/**`
- `backend/tests/knowledge/**`
- `docs/testes/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar top-K por cosseno com filtros de versão/estado e query minimizada.
2. Retornar fonte, página/seção e score; tratar baixa evidência por abstenção.
3. Criar conjunto rotulado de consultas, medir relevância e p95 documentando ambiente e tamanho.

## Critérios de aceite

- Consulta nunca recupera documento não aprovado/revogado.
- Busca insuficiente retorna ausência explícita, sem citações inventadas.
- p95 vetorial <= 2 segundos no cenário documentado; métricas de relevância têm limiar aceito antes do ensaio.

## Testes obrigatórios

RAG; BE; INT; configurar comando RAG e guardar relatório reprodutível.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Confundir similaridade com probabilidade clínica ou tempo completo da geração.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
