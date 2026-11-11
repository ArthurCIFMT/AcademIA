# Registro da preparação documental

Documento histórico da preparação de 2026-11-04, com continuidade registrada
abaixo. A especificação central está em [SPEC.md](../../SPEC.md) e o estado
atual de execução está no [manifesto](../prompts/README.md).

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
e não impedem os scaffolds. Os marcos PG-01/02/03 exigem as entregas e os aceites
integrados indicados no [manifesto](../prompts/README.md).

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

## Continuidade da implementação

A fundação, identidade/pessoas, notificações, onboarding/avaliações, equipamentos
e treino manual até TRN-04 foram entregues. RAG-01 concluiu a curadoria e
RAG-02 entregou a conexão Qdrant persistente; RAG-03 entregou extração e
proveniência, com pendências de qualidade registradas. A sequência segue em RAG-04.
Consulte o manifesto para dependências, critérios e evidências por cartão,
e o [SPEC](../../SPEC.md) para o retrato por capacidade.

Os guias de [backend](../../backend/README.md), [banco](../../database/README.md) e
[frontend](../../frontend/README.md) descrevem a execução local.
A chave pessoal GROQ_API_KEY e os pesos de embeddings são necessários às entregas
de IA/RAG correspondentes; a ausência não impede cadastros ou treino manual.

## Verificação executada na preparação de 2026-11-04

Retrato histórico anterior à [auditoria de 2026-11-06](../analises/2026-11-06-auditoria-rf-rn-ia.md).
As contagens abaixo pertencem à preparação histórica. Consulte o
[modelo lógico vigente](modelo-de-dados/modelo-logico.dbml) e execute o
verificador documental para obter as contagens atuais.

- Parser oficial @dbml/core 11.0.1: DBML válido, 42 tabelas e 60 referências.
- Ajv 8.20.0 / draft 2020-12: schema válido e 10 casos sintéticos de contrato passaram.
- XML draw.io: 307 células extraídas da fonte em memória; PNG original preservado.
- Auditor documental passou na proposta: 110 Markdown, 743 links locais, 61 cartões,
  grafo sem ciclos, 18 PDFs/MER íntegros e 32 casos documentais preservados.
- Casos de triagem têm 24 resultados esperados definidos; não foram apresentados
  como testes executados do backend ou LLM.

Ferramentas DBML/Ajv foram executadas em diretório temporário fora do repositório,
sem adicionar dependências à aplicação naquele marco. Fixtures de contrato estão em
[casos](../testes/contratos-onboarding-v1.json). Não são teste de FastAPI/LLM reais.
