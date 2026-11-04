# RAG-04 — Chunking, embeddings e indexação idempotente

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, RAG-02, RAG-03.
- Requisitos: MRF01, MRF11, MRF15; RNF-17.
- Módulos: MOD-05.

## Referências de arquitetura

[Fluxo semântico](../../arquitetura/rag-semantico.md),
[dados](../../arquitetura/modelo-de-dados/dados-rag-ia.md) e
[testes](../../testes/rag-ia-semantico.md).

## Objetivo e contexto

Entregar chunking, embeddings e indexação idempotente, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/knowledge/ingestion/**`
- `backend/app/modules/knowledge/embeddings/**`
- `backend/tests/knowledge/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Fragmentar respeitando limites do modelo e contexto sem perder metadados de fonte.
2. Gerar embeddings em lotes com timeout, retry limitado e tratamento de rate limit.
3. Indexar por IDs estáveis/versionados; controlar processamento parcial e ativação da versão completa.

## Finalidades e limites

Expor recuperação para dúvidas, triagem do resumo e geração de ficha, por
contratos de MOD-05; este módulo não implementa LLM/planner nem decide aptidão.
Aprovação é por versão; revogação invalida novo uso/cache, mesmo antes da remoção
vetorial. Livro/literatura dependem de curadoria; inventário e clientes não são
indexados como literatura compartilhada. Não enviar documento inteiro por pedido.

## Critérios de aceite

- Reprocessar não duplica chunks e vetores.
- Falha no meio do lote não marca versão completa; retomada conclui somente os faltantes.
- Mudança de modelo/dimensão exige coleção/versão compatível; cada vetor aponta ao texto correto.

## Testes obrigatórios

BE com rate limit/timeout; INT no banco vetorial real; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Chamar API paga irrestritamente ou deixar versão parcialmente indexada como ativa.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
