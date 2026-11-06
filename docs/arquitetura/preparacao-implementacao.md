# Prontidão documental para implementar

Data: 2026-11-04. Autoridade: responsável determinou academia única e delegou
frameworks, campos e regras técnicas. Não há necessidade de nova aprovação genérica.

## Decisões fechadas

| Gate | Decisão/evidência | Estado |
|---|---|---|
| GATE-01 | Python 3.12, FastAPI/Pydantic, SQLAlchemy/Alembic, uv, testes — ADR-001 | FECHADO |
| GATE-02 | Auth integrada, sessão opaca/Argon2id, estados de perfis — ADR-002 | FECHADO |
| GATE-03 | Academia única — ADR-003 | FECHADO |
| GATE-04 | Qdrant local, E5, Groq/Llama, corpus inicial, onboarding/triagem/limites — ADR-004 e contratos | FECHADO |
| GATE-05 | Commits coesos na main e push autorizado — ADR-003 | FECHADO |
| GATE-06 | PostgreSQL nativo, Qdrant local, Mailpit, sem Docker — ADR-005 | FECHADO |

Fechamento é de escolhas/documentação. Não significa serviço instalado, chave
configurada, benchmark ou ensaio real. GATE-07/08/09 continuam posteriores ao MVP
e não impedem scaffold. Marcos PG-01/02/03 continuam abertos, sem código funcionando.

## Entregas documentais efetivamente executadas

- FND-01: fontes consolidadas, pendências técnicas agora resolvidas por delegação.
- FND-02A/FND-02B: cinco ADRs aceitos com origem, alternativas e consequências.
- FND-03: modelo lógico DBML/JSON, dicionário, invariantes/estados e XML de origem
  extraído sem regravar o PNG. São 42 tabelas lógicas (inclui fases posteriores);
  migrations físicas pertencem aos prompts respectivos.

[ADRs](decisoes/README.md), [modelo](modelo-de-dados/modelo-logico.dbml),
[dicionário](modelo-de-dados/dicionario.md),
[invariantes](modelo-de-dados/invariantes-e-estados.md),
[formulário](../requisitos/onboarding-e-triagem.md),
[JSON Schema](../requisitos/schemas/onboarding-v1.schema.json),
[configuração IA](../requisitos/configuracao-ia-rag.md),
[corpus](../../materiais/rag/corpus-inicial.json).

## Próximos prompts prontos

FND-04 (backend) e FND-07 (frontend) estão PRONTO. Implementar apenas o cartão
escolhido, sem criar todas as tabelas ou antecipar Docker/IA.
FND-05 requer o scaffold; configura PostgreSQL real de teste, sem SQLite substituto.
A chave pessoal GROQ_API_KEY só é necessária na integração real de IA; ausência
não bloqueia fundação, cadastros e treino manual. Pesos de embedding e serviços
locais serão instalados nos prompts correspondentes; não inventar resultados.

## Verificação executada na preparação de 2026-11-04

Retrato histórico anterior à [auditoria de 2026-11-06](../analises/2026-11-06-auditoria-rf-rn-ia.md).
O modelo atual mantém 42 tabelas, com 61 referências; os resultados abaixo são do modelo anterior.

- Parser oficial @dbml/core 11.0.1: DBML válido, 42 tabelas e 60 referências.
- Ajv 8.20.0 / draft 2020-12: schema válido e 10 casos sintéticos de contrato passaram.
- XML draw.io: 307 células extraídas da fonte em memória; PNG original preservado.
- Auditor documental passou na proposta: 110 Markdown, 743 links locais, 61 cartões,
  grafo sem ciclos, 18 PDFs/MER íntegros e 32 casos documentais preservados.
- Casos de triagem têm 24 resultados esperados definidos; não foram apresentados
  como testes executados do backend ou LLM.

Ferramentas DBML/Ajv foram executadas em diretório temporário fora do repositório,
sem adicionar dependências à aplicação inexistente. Fixtures de contrato estão em
[casos](../testes/contratos-onboarding-v1.json). Não são teste de FastAPI/LLM reais.
