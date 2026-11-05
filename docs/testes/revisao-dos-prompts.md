# Revisão antes da implementação — preparação técnica

Data: 2026-11-04. Preparação por delegação do responsável, após a revisão c6d1c82.
[Prontidão e evidências](../arquitetura/preparacao-implementacao.md) é o índice vigente.

## Resultado

Uma academia. FastAPI/Pydantic/SQLAlchemy/Alembic/uv; React/TS/Vite; sessão integrada;
PostgreSQL nativo e Qdrant local antes do Docker; E5-small e Groq/Llama como defaults.
Campos, validações, estados de perfis, triagem, limites e avaliação foram definidos.
GATE-01–GATE-06 fechados documentalmente. FND-01–FND-03 concluídos; FND-04/FND-07 prontos.
Sem instalação de aplicação ou testes reais de PostgreSQL/LLM/CompreFace nesta fase.

## Contratos e consistência

[ADRs](../arquitetura/decisoes/README.md),
[onboarding/triagem](../requisitos/onboarding-e-triagem.md),
[JSON Schema](../requisitos/schemas/onboarding-v1.schema.json),
[configuração IA](../requisitos/configuracao-ia-rag.md),
[modelo DBML](../arquitetura/modelo-de-dados/modelo-logico.dbml),
[dicionário](../arquitetura/modelo-de-dados/dicionario.md),
[invariantes](../arquitetura/modelo-de-dados/invariantes-e-estados.md).

TRN-02 entrega rascunho/editor e estrutura de versões; TRN-03 publica/retem/revisa,
sem exigir publicação completa no cartão anterior. AI-03 usa TRN-03 e AI-04 só
acompanha, sem nova publicação/aviso. AI-05 usa formulário ONB-03 para confirmação.
Dúvida geral sem onboarding; dado ausente não é saudável; sem laudo obrigatório.
Módulos continuam independentes por contrato, não por acesso livre às tabelas.

## Verificação documental/técnica

Parser @dbml/core: DBML válido com 42 tabelas e 60 referências.
Ajv 2020: contrato e dez casos sintéticos passaram. XML de origem extraído e
parseado (307 células), sem alterar PNG. Auditor geral executado antes de aplicar.
Ferramentas temporárias externas à aplicação; nenhuma dependência do projeto instalada.
Testes de aplicação, recuperação/geração e biometria reais continuam por executar.

## Recursos e fases posteriores

GROQ_API_KEY, pesos locais e PostgreSQL/Mailpit serão configurados nos prompts
dependentes; não bloqueiam a criação dos scaffolds. Não pedir chave em texto/log.
GATE-07/08/09 (reservas, detalhes de acesso/CompreFace e gateway) continuam tardios.
MVP e demais marcos não foram marcados como aplicação concluída.
Sete documentos selecionados para ingestão; outros onze pendentes; PDFs preservados.
