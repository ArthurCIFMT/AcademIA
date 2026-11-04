# RAG-04 — Chunking, embeddings e indexação idempotente

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, RAG-02, RAG-03.
- Requisitos: MRF01, MRF11, MRF15; RNF-17; MRF18 (apoio à recuperação contextual).
- Módulos: MOD-05.

## Objetivo e contexto

Entregar chunking, embeddings e indexação idempotente, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.
Consulte o [fluxo agentivo](../../arquitetura/agentic-rag.md), a
[extensão de dados](../../arquitetura/modelo-de-dados/extensao-agentic-rag.md)
e o [conjunto de testes](../../testes/agentic-rag.md). Suíte significa conjunto
organizado de testes; sigla de teste não é comando pronto de terminal.

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

## Critérios de aceite

- Reprocessar não duplica chunks e vetores.
- Falha no meio do lote não marca versão completa; retomada conclui somente os faltantes.
- Mudança de modelo/dimensão exige coleção/versão compatível; cada vetor aponta ao texto correto.

## Complementos obrigatórios para Agentic RAG

- IDs estáveis ligam trecho, versão, página/seção, ordem/vizinhança e texto/hash;
  preservar grupos de tabela/ressalva para leitura complementar sem inventar fonte.
- Corpus ativo é composto apenas de versões completas e aprovadas; filtros e
  checagem relacional impedem uso de revogadas mesmo antes da limpeza vetorial.
- Verificar que leituras complementares resolvem a mesma versão e que retomada
  não duplica trechos nem perde vínculos de contexto. Não indexar chat/onboarding.

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
