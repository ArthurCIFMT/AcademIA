# Revisão autorizada: orquestrador e RAG semântico

> Mapa da mudança em af1685b. Refinamentos posteriores, inclusive dispensa de
> aprovação médica e novas dependências dos cartões, estão na
> [revisão didática vigente](2026-11-04-revisao-didatica-e-consistencia.md).

## Origem e prevalência

O responsável esclareceu que IA deve responder dúvidas, analisar resumo do onboarding
e gerar fichas pelo LLM com conhecimento especializado. Esta revisão substitui
a pesquisa Agentic RAG e descarta as sete alterações locais parciais da revisão
interrompida que proibiam geração por IA. Nenhuma aplicação existia nessa transição.

## Mapa de mudanças

| Fonte anterior | Destino vigente | Consequência |
|---|---|---|
| MRF01–MRF15 de prescrição multiagente / versão parcial de chat exclusivo | 15 MRFs reescritos, 67 critérios | Dúvidas, resumo/triagem, geração e revisão profissional separados |
| MRF16–MRF19 de pesquisa agentiva | Retirados do escopo; histórico no Git | Não implementar planner LLM, ferramentas autônomas ou loop de pesquisa |
| RF-13/RF-15/RF-18/RF-19 | Snapshot/resumo, geração LLM, chat curto e adaptação explícita | Origem, suporte, bloqueios e isolamento rastreáveis |
| Catálogo implícito | RF-38 / TRN-01 / EQP-01 | Exercícios em PostgreSQL vinculados aos recursos; prescrição no item de ficha |
| Orçamento sem alvo de simplicidade | RNF-18 / AI-02 / AI-06 | Até uma geração no chat; ficha até uma análise + uma geração; medir tempo total |
| Arquitetura/extensão/testes agentivos | rag-semantico.md / dados-rag-ia.md / rag-ia-semantico.md | Arquivos antigos são pontes históricas, sem instruções ativas |
| Prompts de RAG/IA | Mesmos IDs RAG-01–RAG-05 / AI-01–AI-06 / TST-01 | Dependências mantidas; entregáveis e testes adequados |
| Referências gerais | Mestre, contexto, fundação, módulos, matrizes e testes atualizados | Sem referências normativas executáveis aos MRFs retirados |

## Limites preservados

Monólito modular Python, React/TS/Vite, PostgreSQL, banco vetorial especializado,
CompreFace, catraca fictícia, matrícula manual sem pagamento obrigatório, Docker
tardio, equipamentos no MVP, até 15 versões completas e regra de rejeitadas.
Cliente consulta ficha/chat sem aceite prévio. Instrutor revisa e cria manualmente.
MER original e PDFs permanecem intactos. Nenhuma fonte ganha aprovação automática.

## Decisões pendentes

Livro/material especializado inicial, curador/corpus, provedores gratuitos/modelos,
política de bloqueio/encaminhamento, campos/unidades de onboarding e resumo, limites
de contexto/tempo/retentativas, retenção operacional e limiares de qualidade.
Não supor que RAG acelera qualquer API gratuita ou que livro substitui catálogo.
Ativar somente material pertinente/aprovado; ampliar acervo depende das lacunas
observadas no ensaio. Não remover PDF útil apenas porque mudou a orquestração.

## Revisão

Conferir [MRFs](../requisitos/macrorequisitos-ia-rag.md),
[arquitetura](../arquitetura/rag-semantico.md),
[manifesto](../prompts/README.md) e
[testes](../testes/rag-ia-semantico.md).
A criação destes documentos não implementa nem testa o modelo real.
