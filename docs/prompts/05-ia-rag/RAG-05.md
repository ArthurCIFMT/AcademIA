# RAG-05 — Recuperação, citações e avaliação vetorial

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: RAG-04.
- Requisitos: MRF02, MRF11, MRF12, MRF15; RN-29, RN-39; RNF-13.
- Módulos: MOD-05.

## Referências de arquitetura

[Fluxo semântico](../../arquitetura/rag-semantico.md),
[dados](../../arquitetura/modelo-de-dados/dados-rag-ia.md) e
[testes](../../testes/rag-ia-semantico.md).

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

## Finalidades e limites

Expor recuperação para dúvidas, triagem do resumo e geração de ficha, por
contratos de MOD-05; este módulo não implementa LLM/planner nem decide aptidão.
Aprovação é por versão; revogação invalida novo uso/cache, mesmo antes da remoção
vetorial. Livro/literatura dependem de curadoria; inventário e clientes não são
indexados como literatura compartilhada. Não enviar documento inteiro por pedido.

## Critérios de aceite

- Consulta nunca recupera documento não aprovado/revogado, inclusive após
  aquecer o cache ou com o vetor ainda presente. SC-05 verifica isso em índice
  de teste e confirma que conversas e dados operacionais não integram o acervo.
- Exercitar a porta de recuperação com o vetorial de teste e sem configurar
  provedor LLM. O resultado contém apenas evidências e proveniência dentro
  do top-K permitido, mesmo quando um trecho sintético contém uma instrução.
- Consultas de teste em português recuperam evidências esperadas PT/EN com modelo
  de embeddings compatível; avaliar relevância por idioma, sem traduzir o acervo
  automaticamente ou presumir desempenho só porque o modelo é multilíngue.
- Busca insuficiente retorna ausência explícita, sem citações inventadas.
- Score alto sozinho não prova suporte: verificar condição, população e
  intervenção. Sem evidência pertinente, adaptação por saúde não pode prosseguir.
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
