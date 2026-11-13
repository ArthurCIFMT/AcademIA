# AcademIA

Aplicação web acadêmica para gestão de uma academia e geração assistida de treinos.

## Comece pela especificação

O [SPEC.md](SPEC.md) é a especificação completa para compreender ou reconstruir
o sistema em outra IA. Ele incorpora requisitos/critérios, regras, decisões
técnicas, evolução do MER, modelo de dados, contratos, parâmetros de IA/RAG,
corpus, testes e sequência de prompts. Pode ser transportado como arquivo único.

As fontes especializadas continuam versionadas; a compilação mantém a cópia
completa sincronizada. A [visão geral](docs/especificacao/visao-geral.md) orienta
a leitura e o [roteiro](docs/especificacao/roteiro-reconstrucao.md) explica como
fragmentar uma reconstrução sem enviar o documento inteiro em cada prompt.

O [AGENTS.md](AGENTS.md) define as regras de trabalho dos agentes.
O [prompt mestre](docs/prompts/00-prompt-mestre.md) orienta planejamento e os
[prompts operacionais](docs/prompts/README.md) delimitam tarefas de implementação.

## Estado e navegação

**MVP acadêmico concluído**, com TST-01 aprovado e PG-01 fechado.
[Evidências e limites do aceite](docs/testes/aceitacao-mvp.md).
A revisão manual do aplicativo local é o próximo passo; funcionalidades
pós-MVP permanecem no roteiro.

O [manifesto](docs/prompts/README.md) registra capacidades entregues, pendentes,
dependências e evidências. O resumo por módulo está no
[SPEC](SPEC.md#5-capacidades-e-estágio-da-implementação). Funcionalidade descrita
em um requisito ou cartão não significa implementação concluída.

- [Requisitos funcionais](docs/requisitos/requisitos-funcionais.md),
  [regras de negócio](docs/requisitos/regras-de-negocio.md) e
  [requisitos não funcionais](docs/requisitos/requisitos-nao-funcionais.md).
- [Macrorequisitos IA/RAG](docs/requisitos/macrorequisitos-ia-rag.md) e
  [arquitetura semântica](docs/arquitetura/rag-semantico.md).
- [Módulos](docs/arquitetura/modulos.md) e [ADRs aceitos](docs/arquitetura/decisoes/README.md).
- [Modelo lógico](docs/arquitetura/modelo-de-dados/modelo-logico.dbml) e
  [análise do MER preservado](docs/arquitetura/revisao-mer.md).
- [Estratégia](docs/testes/estrategia.md) e [comandos/resultados](docs/testes/comandos.md).
- [Materiais para RAG](materiais/rag/README.md).

## Execução local

Siga os guias de [PostgreSQL e migrations](database/README.md),
[backend Python](backend/README.md), [frontend React](frontend/README.md) e
[primeiro administrador](docs/instalacao/primeiro-administrador.md).
Os exemplos de ambiente são versionados; credenciais locais ficam fora do Git.

## Trabalho com IA e evolução

Leia AGENTS.md, SPEC.md e as fontes da capacidade antes de executar o cartão
escolhido. A especificação define o produto e os contratos; o prompt organiza
a entrega. Mudanças aprovadas atualizam a fonte especializada, os critérios,
a rastreabilidade e os cartões afetados, conforme o
[protocolo do SPEC](SPEC.md#9-protocolo-de-alteração-e-manutenção).

O [registro de preparação](docs/arquitetura/preparacao-implementacao.md) e as
[análises datadas](docs/analises/2026-11-06-auditoria-rf-rn-ia.md) preservam decisões
e verificações históricas. Use o manifesto para acompanhar a execução atual.

## Verificação documental

Python 3.10+, sem dependências externas:

```text
python scripts/gerar_spec.py --check
python scripts/verificar_documentacao.py
```

Após alterar uma fonte, execute `python scripts/gerar_spec.py --write` e
versione fonte/cópia juntas. A verificação detecta cópia desatualizada e a
auditoria confere a estrutura documental. Os testes da aplicação e os
ensaios de integrações/IA têm comandos e evidências próprios.
