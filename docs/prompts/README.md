# Manifesto dos prompts

## Finalidade

Este diretório contém o prompt mestre, o template obrigatório e a sequência de
prompts operacionais do projeto. Um prompt operacional deve produzir uma entrega
coesa, verificável e compatível com o estado atual do repositório.

## Como executar

1. Leia `AGENTS.md`.
2. Leia `00-prompt-mestre.md`.
3. Confirme que todas as dependências do prompt operacional estão concluídas.
4. Execute somente um prompt operacional por vez.
5. Rode os testes e verificações indicados.
6. Atualize a rastreabilidade e o estado neste manifesto.
7. Faça a operação Git autorizada pelo prompt.

## Estados

- `PLANEJADO`: identificado, mas o texto operacional ainda pode depender de gates.
- `PRONTO`: texto completo e dependências documentais disponíveis.
- `EM_EXECUCAO`: uma entrega está em andamento.
- `BLOQUEADO`: depende de decisão ou estado externo.
- `CONCLUIDO`: critérios e testes registrados.
- `DISPENSADO`: retirado do escopo com justificativa.

O estado descreve a **execução**, não a existência do texto. Um prompt pode ter
texto completo e permanecer `BLOQUEADO` até suas dependências serem concluídas.

## Gates de decisão e de fase

| ID | Condição de fechamento | Estado | Evidência esperada |
|---|---|---|---|
| GATE-01 | Stack Python e ferramentas aceitas | ABERTO | ADRs aceitos |
| GATE-02 | Estratégia de identidade/autenticação aceita | ABERTO | ADR aceito |
| GATE-03 | Academia única ou multitenancy definido | ABERTO | ADR aceito |
| GATE-04 | Banco vetorial, provedores, corpus, bloqueios e MRF08–MRF15 decididos | ABERTO | ADRs e requisitos atualizados |
| GATE-05 | Política Git definida | ABERTO | ADR aceito |
| GATE-06 | Execução local das dependências antes do Docker definida | ABERTO | ADR e guia local |
| GATE-07 | Reserva/capacidade de aulas confirmada no escopo | ABERTO | RF/RN aprovados ou dispensa registrada |
| PG-01 | MVP funcional e testes críticos aprovados | ABERTO | relatório de aceite do MVP |
| PG-02 | Todos os módulos selecionados para a entrega final concluídos/dispensados | ABERTO | manifesto e rastreabilidade atualizados |

## Registro de execuções

| ID | Estado | Evidência |
|---|---|---|
| P00 | CONCLUIDO | Commits `a17b993` e `528a25c` no repositório remoto. |

## Ordem e dependências

### Fundação

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| P00 | Repositório, `AGENTS.md` e `.gitignore` | — | CONCLUIDO |
| FND-01 | Validar RF, RN, RNF, MRF e glossário | P00 | PRONTO |
| FND-02A | Elaborar propostas de ADR | FND-01 | BLOQUEADO |
| FND-02B | Aprovar ADRs e fechar gates | FND-02A | BLOQUEADO |
| FND-03 | Revisar MER e modelo lógico | FND-02B | BLOQUEADO |
| FND-04 | Scaffold do backend | FND-03, GATE-01, GATE-03, GATE-06 | PLANEJADO |
| FND-05 | PostgreSQL, ORM e migrations | FND-04 | PLANEJADO |
| FND-06 | Contratos REST, erros e testes base | FND-04 | PLANEJADO |
| FND-07 | Scaffold do frontend | FND-02B | PLANEJADO |
| FND-08 | Auditoria e eventos básicos | FND-05, FND-06 | PLANEJADO |

### Identidade e pessoas

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| IAM-01 | Adaptador de autenticação/OIDC | FND-06, GATE-02 | PLANEJADO |
| IAM-02 | Usuário, papéis e perfis | FND-05, IAM-01 | PLANEJADO |
| IAM-03 | Políticas de autorização | IAM-02 | PLANEJADO |
| IAM-04 | Sessão e rotas protegidas no frontend | FND-07, IAM-01 | PLANEJADO |
| PES-01 | Funcionários | IAM-02, IAM-03 | PLANEJADO |
| PES-02 | Clientes | IAM-02, IAM-03 | PLANEJADO |
| PES-03 | Designação cliente–instrutor | PES-01, PES-02 | PLANEJADO |
| NTF-01 | Notificações e e-mail abstraído | FND-08 | PLANEJADO |

### Onboarding e avaliação

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| ONB-02 | Onboarding versionado | PES-02, FND-05 | PLANEJADO |
| ONB-01 | Convite e token seguro | ONB-02, NTF-01 | PLANEJADO |
| ONB-03 | Formulário responsivo | ONB-01, ONB-02, IAM-04 | PLANEJADO |
| ONB-04 | Avaliação e acesso por designação | ONB-02, PES-03 | PLANEJADO |

### Exercícios, fichas e matrícula mínima

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| TRN-01 | Catálogo de exercícios | FND-05, IAM-03 | PLANEJADO |
| TRN-02 | Ficha manual e versionamento | TRN-01, ONB-02, PES-03 | PLANEJADO |
| TRN-03 | Revisão e aprovação profissional | TRN-02, PES-03 | PLANEJADO |
| TRN-04 | Visualização da ficha pelo cliente | TRN-03, IAM-04 | PLANEJADO |
| MEM-01 | Plano e matrícula manual | FND-05, PES-02 | PLANEJADO |

### IA e RAG

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| RAG-01 | Corpus e metadados | FND-03, FND-05, GATE-04 | PLANEJADO |
| RAG-02 | Cliente do banco vetorial | FND-04, FND-06, RAG-01 | PLANEJADO |
| RAG-03 | Extração PDF/TXT | FND-04, RAG-01 | PLANEJADO |
| RAG-04 | Chunking, embeddings e indexação | FND-05, RAG-02, RAG-03 | PLANEJADO |
| RAG-05 | Recuperação, filtros e citações | RAG-04 | PLANEJADO |
| AI-01 | Triagem e políticas estruturadas | ONB-04, GATE-04 | PLANEJADO |
| AI-02 | Schemas e orquestrador | AI-01, RAG-05 | PLANEJADO |
| AI-03 | Geração de proposta | AI-02, TRN-02 | PLANEJADO |
| AI-04 | Submeter proposta ao workflow profissional e avisar instrutor | AI-03, TRN-03, NTF-01 | PLANEJADO |
| AI-05 | Chat e adaptação versionada | AI-04, TRN-04 | PLANEJADO |
| AI-06 | Avaliação automatizada da IA | AI-01, AI-02, AI-03, AI-04, AI-05 | PLANEJADO |

### Controle de acesso

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| ACS-01 | Referência biométrica | PES-02, IAM-03 | PLANEJADO |
| ACS-02 | Contrato do evento facial externo | FND-06, ACS-01 | PLANEJADO |
| ACS-03 | Motor de decisão de acesso | ACS-02, MEM-01 | PLANEJADO |
| ACS-04 | Liberação manual auditada | ACS-03, FND-08 | PLANEJADO |
| ACS-05 | Frequência e lotação | ACS-03 | PLANEJADO |
| ACS-06 | Interfaces de acesso e lotação | ACS-05, FND-07 | PLANEJADO |

### Módulos complementares

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| EQP-01 | Equipamentos | IAM-03, FND-07 | PLANEJADO |
| AUL-01 | Agenda de aulas | IAM-03, FND-07 | PLANEJADO |
| AUL-02 | Reservas e capacidade, se aprovadas | AUL-01, GATE-07 | BLOQUEADO |
| DSH-01 | Dashboard-base | PES-02, ACS-05, MEM-01 | PLANEJADO |

### Financeiro tardio

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| FIN-01 | Cobranças e consulta | MEM-01 | PLANEJADO |
| FIN-02 | Pagamento externo idempotente | FIN-01 | PLANEJADO |
| FIN-03 | Indicadores financeiros | FIN-02, DSH-01 | PLANEJADO |

### Infraestrutura final

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| INF-01 | Dockerfiles frontend/backend | PG-01 | PLANEJADO |
| INF-02 | Compose dos serviços | INF-01 | PLANEJADO |
| INF-03 | Redes, volumes e healthchecks | INF-02 | PLANEJADO |
| INF-04 | Teste integrado e documentação | INF-03 | PLANEJADO |

### Validação final

| ID | Entrega | Depende de | Estado |
|---|---|---|---|
| VAL-01 | Rastreabilidade final | PG-02 | PLANEJADO |
| VAL-02 | Aceitação e segurança | VAL-01 | PLANEJADO |
| VAL-03 | Documentação e demonstração | VAL-02, INF-04 | PLANEJADO |

## Regra para criação dos próximos textos

Os textos completos de prompts de implementação devem ser escritos após FND-02B e
FND-03, evitando congelar framework, autenticação, tenancy ou banco vetorial por
suposição. O manifesto já reserva IDs, ordem e critérios mínimos de saída.
