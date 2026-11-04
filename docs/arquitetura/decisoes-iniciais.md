# Decisões arquiteturais iniciais

## Como interpretar este documento

- **Confirmada**: decisão expressa pelo responsável do projeto.
- **Recomendada**: escolha técnica proposta, sujeita ao checkpoint FND-02B.
- **Aberta**: não implementar o componente dependente antes de registrar ADR.

## Decisões confirmadas

| ID | Decisão | Consequência |
|---|---|---|
| DEC-001 | Projeto acadêmico com MVP incremental. | Evitar complexidade comercial prematura. |
| DEC-002 | React + TypeScript + Vite no frontend. | SPA responsiva e contratos tipados. |
| DEC-003 | Backend obrigatoriamente em Python. | Framework será fechado por ADR. |
| DEC-004 | PostgreSQL para dados relacionais. | Invariantes por constraints e migrations. |
| DEC-005 | REST + JSON + OpenAPI nas fronteiras. | Contratos documentados e testáveis. |
| DEC-006 | RAG com banco vetorial especializado. | Conhecimento separado dos dados operacionais. |
| DEC-007 | Usuário pode acumular papéis. | Relação usuário–papel N:N e perfis específicos. |
| DEC-008 | Cliente deve ser designado a instrutor. | Vínculo histórico com responsável principal. |
| DEC-009 | Cliente consulta treino e conversa com IA sem aceite prévio. | Parecer posterior do instrutor é separado da publicação tecnicamente validada. |
| DEC-010 | Atendente matricula/renova sem exigir pagamento confirmado. | Financeiro tardio e independente da matrícula e do acesso acadêmico. |
| DEC-011 | Docker fica depois do MVP. | Desenvolvimento local é requisito anterior. |
| DEC-012 | Repositório remoto é `ArthurCIFMT/AcademIA`. | Entregas autorizadas devem ser sincronizadas. |
| DEC-013 | Reconhecimento facial real e catraca fictícia por API externa. | Não há hardware; mocks isolados não comprovam reconhecimento. |
| DEC-014 | Cadastro da foto após matrícula pelo atendente. | Referência vinculada ao cliente matriculado e autor da operação. |

## Recomendações a formalizar em ADR

| ID | Recomendação | Justificativa resumida |
|---|---|---|
| REC-001 | Monólito modular já vigente em AGENTS.md; formalizar em ADR. | Evitar divergência entre regra atual e registro de decisão. |
| REC-002 | FastAPI + Pydantic. | Python, OpenAPI e validação tipada. |
| REC-003 | SQLAlchemy + Alembic. | ORM e migrations explícitas. |
| REC-004 | Keycloak/OIDC. | Identidade e credenciais fora do domínio. |
| REC-005 | Qdrant. | Banco vetorial especializado e configurável. |
| REC-006 | Academia única no MVP. | Evita isolamento multitenant prematuro. |
| REC-007 | Um instrutor principal ativo por cliente. | Responsabilidade inequívoca com histórico. |
| REC-008 | Separar publicação, validação técnica e parecer por versão. | Não condicionar consulta/chat ao aceite; explicitar tratamento da atualidade e de rejeição. |
| REC-009 | Armazenar timestamps em UTC/ISO 8601. | Consistência e rastreabilidade. |
| REC-010 | Objetos tipados internamente; JSON nas fronteiras. | Evita serialização artificial dentro do monólito. |
| REC-011 | Amazon Rekognition como API facial candidata. | Cadastro de referências e busca por nova imagem; sujeito a GATE-08, conta e orçamento de teste. |

## Decisões abertas que funcionam como gates

### GATE-01 — Stack Python

Escolher e registrar framework, validação, ORM, migrations, gerenciador de
dependências, lint, formatação e testes.

### GATE-02 — Identidade

Escolher Keycloak/OIDC ou autenticação integrada. Definir como o serviço será
executado localmente antes da fase Docker.

### GATE-03 — Escopo de academia

Confirmar academia única no MVP ou introduzir isolamento multitenant desde o
primeiro schema.

### GATE-04 — IA e RAG

Confirmar Qdrant, provedores de LLM/embeddings, corpus inicial, responsável por
aprovar documentos e critérios de bloqueio de casos graves.

### GATE-05 — Git

Definir se cada prompt usa branch e pull request ou se entregas acadêmicas podem
ser integradas diretamente na `main`.

### GATE-06 — Dependências locais

Documentar como PostgreSQL, identidade e Qdrant serão disponibilizados antes da
containerização final.

## Restrições permanentes

Gates complementares no manifesto: GATE-07 (reservas), GATE-08 (API facial real,
matrícula manual independente de pagamento, simulador de catraca, limites e alternativa de acesso), GATE-09 (pagamento/sandbox). São decisões da fase
correspondente e não precisam bloquear a redação dos prompts.

- Containerização não pode ser antecipada por prompts de fundação ou MVP.
- Matrícula pelo atendente não exige pagamento nem registro financeiro, manual ou
  automatizado. O acesso acadêmico verifica matrícula e regras próprias; pagamento
  não é um pré-requisito. Eventual bloqueio financeiro futuro exige decisão explícita.
- Agentes de IA são papéis sob um orquestrador; não implicam microserviços.
- Regras críticas não ficam exclusivamente em prompts ou documentos vetoriais.
- A base RAG não recebe literatura inventada pelo agente.
- `EXERCICIO` descreve catálogo; séries, repetições, carga, ordem e descanso
  pertencem ao item prescrito na ficha.
