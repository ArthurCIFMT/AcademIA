# Revisão antes da implementação

Data: 2026-11-04. Base Git: d7a5199. Revisão documental, sem implementação de aplicação.

O planejamento vigente tem 38 RFs, 39 RNs, 18 RNFs, 15 MRFs/67 critérios, 13 módulos
e 61 cartões. Orquestrador coordena dúvidas, triagem de resumo e geração pelo LLM,
com busca vetorial semântica fixa. Substitui a pesquisa agentiva e a revisão local
interrompida que restringia fichas ao instrutor.

[Mapa de mudança](../analises/2026-11-04-revisao-ia-semantica.md),
[MRFs](../requisitos/macrorequisitos-ia-rag.md),
[arquitetura](../arquitetura/rag-semantico.md),
[dados](../arquitetura/modelo-de-dados/dados-rag-ia.md),
[manifesto](../prompts/README.md) e [testes](rag-ia-semantico.md).

## Consistência e preservação

Cartões RAG/IA revisados, sem dependências novas/cíclicas. Mestre, contexto,
fundação, catálogo, matrizes, testes e referências apontam o fluxo atual.
Documentos agentivos antigos são pontes históricas; MRF16–MRF19 não são executáveis.
MER original permanece intacto; FND-03 produzirá modelo lógico/migrations depois.
PDFs originais, metadados e os 32 casos documentais foram preservados; perguntas
antigas precisam de revisão antes de serem usadas como aceite do modelo.

## Pendências por etapa

| Antes de | Necessário |
|---|---|
| Scaffolds/modelagem | Framework/ferramentas Python, identidade, academia única/múltipla, Git e serviços locais |
| Identidade/pessoas | Alcance de inativar perfil quando usuário acumula papéis |
| ONB-02 | Campos/unidades/obrigatoriedade e origem declarada/medida aprovados |
| RAG/IA | Livro/corpus e curador, provedores gratuitos/modelos, política de bloqueio, esquema de resumo, orçamento/contexto, retenção e qualidade |
| Aceite da IA | Casos esperados revisados e benchmark real por rota; doubles não aprovam qualidade |
| Biometria | Hospedagem/versão/ensaio CompreFace e alternativa de acesso |
| Reservas/financeiro | Escopo e gateway/sandbox, sem bloquear fundação/matrícula |

Aprovação desta funcionalidade não fecha escolhas ainda abertas. Manter fila/parecer
posterior e trabalho manual independente dos serviços de IA.

## Verificação

Executar na raiz: python scripts/verificar_documentacao.py e git diff --check.
O auditor confere links, IDs, cartões, matrizes, dependências, hashes e casos
documentais. Não é ensaio de recuperação real, triagem ou geração. Não marcar
prompts de implementação como concluídos por redação ou aprovação documental.

## Leitura manual

Contexto/requisitos → decisões → mestre/contexto/contrato → manifesto por
dependências. FND-01 permanece primeira tarefa formal; gates bloqueiam somente
partes dependentes. Histórico detalhado das revisões anteriores permanece no Git.

Resultado documental na proposta isolada: auditor OK; 98 Markdown, 653 links
locais, 61 cartões/rastreabilidades, 12 gates/marcos, grafo sem ciclos, 18 PDFs
e MER íntegros, 32 casos/94 referências de páginas preservados. Não foram
executados testes BE/INT/API/FE/E2E/RAG/IA da aplicação, ainda não implementada.
