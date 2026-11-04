# AcademIA

Projeto acadêmico para gestão de academia e geração assistida de fichas de treino.

## Planejamento

- [Revisão antes da implementação e pendências](docs/testes/revisao-dos-prompts.md)
- [Revisão didática e consistência dos prompts](docs/analises/2026-11-04-revisao-didatica-e-consistencia.md)
- [Contexto e escopo](docs/requisitos/contexto-e-escopo.md)
- [Requisitos funcionais](docs/requisitos/requisitos-funcionais.md)
- [Regras de negócio](docs/requisitos/regras-de-negocio.md)
- [Requisitos não funcionais](docs/requisitos/requisitos-nao-funcionais.md)
- [Registro de normalização](docs/requisitos/registro-de-normalizacao.md)
- [Macrorequisitos de IA e RAG](docs/requisitos/macrorequisitos-ia-rag.md)
- [Funcionamento da IA/RAG e fichas rejeitadas](docs/arquitetura/funcionamento-ia-rag.md)
- [Arquitetura do orquestrador e RAG semântico](docs/arquitetura/rag-semantico.md)
- [Extensão de dados de RAG/IA](docs/arquitetura/modelo-de-dados/dados-rag-ia.md)
- [Revisão do escopo de IA](docs/analises/2026-11-04-revisao-ia-semantica.md)
- [Conjunto de testes do RAG e IA](docs/testes/rag-ia-semantico.md)
- [Acervo bibliográfico para o RAG](materiais/rag/README.md)
- [Módulos](docs/arquitetura/modulos.md)
- [Fluxos atualizados: treino, matrícula e biometria](docs/arquitetura/fluxos-atualizados.md)
- [Revisão da cobertura dos módulos](docs/arquitetura/revisao-modulos.md)
- [Análise do MER original, preservado](docs/arquitetura/revisao-mer.md)
- [Prompt mestre](docs/prompts/00-prompt-mestre.md)
- [Contexto de execução](docs/prompts/00-contexto-de-execucao.md)
- [Manifesto dos prompts](docs/prompts/README.md)
- [Comparação com o modelo do professor](docs/prompts/comparacao-modelo-professor.md)
- [Estratégia de testes](docs/testes/estrategia.md)

O mestre produz o plano. A implementação incremental usa `AGENTS.md`, o contexto
de execução, o contrato comum e um prompt operacional escolhido de cada vez.
Os 61 cartões foram redigidos; a criação da documentação não implementa o sistema.

Para a leitura manual: comece pela revisão, confira decisões e escopo, leia o mestre
e depois percorra o manifesto por dependências. Os primeiros passos executáveis
são FND-01, propostas/decisões de FND-02A/B e modelo lógico de FND-03; a escolha de
stack e outros gates continua necessária antes dos respectivos scaffolds.

Verificação documental reutilizável (Python 3.10+, sem pacotes externos):

```text
python scripts/verificar_documentacao.py
```

Ela não implementa a aplicação, não valida decisões clínicas e não aprova corpus.
