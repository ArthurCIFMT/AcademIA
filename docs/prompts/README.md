# Manifesto dos prompts

## Organização e uso

- [Mestre de planejamento](00-prompt-mestre.md): produz plano completo em chat,
  com resumo e detalhamento; o limite didático de 40 linhas foi retirado.
- [Contexto de execução](00-contexto-de-execucao.md): acompanha a tarefa escolhida.
- [Contrato operacional](00-contrato-operacional.md): regras comuns dos cartões.
- [Comparação com o professor](comparacao-modelo-professor.md).
- [Fluxos atualizados](../arquitetura/fluxos-atualizados.md): treino antes do parecer,
  matrícula sem pagamento obrigatório, API facial real e catraca fictícia.
- [Funcionamento da IA/RAG](../arquitetura/funcionamento-ia-rag.md): tabela dos
  macrorequisitos, evidência obrigatória para saúde e retenção de fichas rejeitadas.
- [Estratégia de testes](../testes/estrategia.md) e [comandos](../testes/comandos.md).
- [Revisão dos módulos](../arquitetura/revisao-modulos.md) e
  [análise do MER preservado](../arquitetura/revisao-mer.md).

Foram redigidos 61 prompts operacionais. P00 representa a preparação Git já
concluída. Os cartões escritos são documentos revisáveis; nenhum módulo funcional
foi implementado pela criação desses arquivos.

Leia AGENTS.md, contexto, contrato e cartão; resolva dependências/ADRs antes de
executar. O mestre de planejamento não é uma segunda tarefa a executar junto.
Cada cartão inclui módulo, requisitos, escopo, entregáveis, aceite e testes.

## Estados e redação

- PRONTO: dependências satisfeitas para iniciar a tarefa.
- BLOQUEADO: texto existe, mas faltam dependências ou decisões para executar.
- EM_EXECUCAO: implementação em andamento.
- CONCLUIDO: critérios/testes e evidência registrados.
- DISPENSADO: fora da entrega por decisão explícita.

Decisões abertas não impedem redigir os prompts. Antes de executar cada cartão,
atualize caminhos, contratos e comandos pelos ADRs/scaffolds aceitos. Não confunda
redação com aprovação da tecnologia ou conclusão do módulo.

A demonstração segue o escopo didático de AGENTS.md: nenhum gate exige laudo,
aprovação médica formal ou validação jurídica externa. Parecer posterior do
instrutor e conferência técnica de corpus/casos pelo responsável permanecem.

## Gates

| ID | Condição de fechamento | Evidência | Estado |
|---|---|---|---|
| GATE-01 | Stack Python e ferramentas | ADRs aceitos | FECHADO |
| GATE-02 | Identidade e recuperação de credenciais | ADR aceito | FECHADO |
| GATE-03 | Academia única ou múltipla | ADR aceito | FECHADO |
| GATE-04 | Provedores, banco vetorial, livro/corpus, política de triagem, resumo, limites por rota e métricas de MRF01–MRF15; fluxo semântico autorizado | ADRs e requisitos aprovados | FECHADO |
| GATE-05 | Branches, commits, push e integração | Política Git aceita | FECHADO |
| GATE-06 | Serviços e comandos locais antes do Docker | Guia local aceito | FECHADO |
| GATE-07 | Escopo e regras de reservas | RF complementar aceito ou dispensa | ABERTO |
| GATE-08 | CompreFace confirmado; hospedagem/versão/contrato/ensaio, matrícula sem pagamento, simulador e alternativa manual | Contrato/políticas e execução definidos antes do módulo | ABERTO |
| GATE-09 | Gateway/sandbox e política de pagamentos | Contrato aceito antes de FIN-02 | ABERTO |
| PG-01 | MVP funcionando localmente | TST-01 e evidências críticas aprovados | ABERTO |
| PG-03 | Maioria dos módulos implementada antes do Docker | PG-01 (inclui EQP-01), ACS-06, AUL-01 e DSH-01 concluídos; mudança de escopo explicitamente registrada | ABERTO |
| PG-02 | Módulos funcionais selecionados e infraestrutura aplicável concluídos ou dispensados; exclui VAL-01–VAL-03 | Manifesto, decisões e matriz de aceite com escopo explícito | ABERTO |

Gates iniciais foram fechados por delegação em [preparação técnica](../arquitetura/preparacao-implementacao.md).
Isso registra decisões e não instalação/ensaio. Gates de fases posteriores não impedem o trabalho
independente de fundação. FND-02B registra escolhas e pendências; não declara escolhas
adiadas como aprovadas. PG-01 exige testes do MVP e PG-03 também exige maioria dos
módulos antes de INF-01, conforme orientação do professor.

## Registro de execuções

| ID | Estado | Evidência |
|---|---|---|
| P00 | CONCLUIDO | Commits a17b993 e 528a25c: repositório e regras iniciais. |
| FND-01 | CONCLUIDO | Preparação delegada em 2026-11-04; [evidências](../arquitetura/preparacao-implementacao.md). |
| FND-02A | CONCLUIDO | Preparação delegada em 2026-11-04; [evidências](../arquitetura/preparacao-implementacao.md). |
| FND-02B | CONCLUIDO | Preparação delegada em 2026-11-04; [evidências](../arquitetura/preparacao-implementacao.md). |
| FND-03 | CONCLUIDO | Preparação delegada em 2026-11-04; [evidências](../arquitetura/preparacao-implementacao.md). |
| FND-04 | CONCLUIDO | 2026-11-07. [Guia do backend](../../backend/README.md) e [comandos](../testes/comandos.md). Python 3.12.14, uv 0.13.7, 3 testes BE, Ruff e mypy aprovados. Uvicorn local confirmou HTTP 200 no healthcheck e OpenAPI disponível. |
| FND-05 | CONCLUIDO | [Guia do banco](../../database/README.md) e [comandos](../testes/comandos.md). PostgreSQL 17.11 local, revisão 0001 aplicada em desenvolvimento, 4 BE, 1 DB e 1 INT aprovados. A role de teste foi recusada em desenvolvimento. Ruff, mypy e DOC aprovados. |
| FND-06 | CONCLUIDO | [Contrato REST](../arquitetura/contratos-rest.md) e [comandos](../testes/comandos.md). 9 API, 13 BE e 2 INT aprovados, incluindo falha real de PostgreSQL sem exposição de detalhes. Ruff, mypy e DOC aprovados. |
| FND-07 | CONCLUIDO | [Guia do frontend](../../frontend/README.md) e [comandos](../testes/comandos.md). Node 24.22.1 e npm 11.6.2. npm ci, 2 testes FE, lint, tipos, build e DOC aprovados. Vite serviu a SPA e encaminhou o healthcheck ao FastAPI real. |
| FND-08 | CONCLUIDO | [Auditoria e eventos](../arquitetura/auditoria-e-eventos.md). Revisão 0002 aplicada em desenvolvimento. 14 BE, 2 DB e 4 INT aprovados em PostgreSQL real quando aplicável. Ruff, mypy e DOC aprovados. |
| IAM-01 | CONCLUIDO | [Adaptador de autenticação](../arquitetura/autenticacao.md). Argon2id real e sessão opaca. 26 BE, 9 API e 7 DB/INT aprovados. A integração HTTP de identidade usa repositórios de teste; persistência e montagem das rotas na aplicação pertencem a IAM-02. Ruff, mypy e DOC aprovados. |
| IAM-02 | CONCLUIDO | [Autenticação persistente](../arquitetura/autenticacao.md) e [primeiro administrador](../instalacao/primeiro-administrador.md). Revisão 0003, 27 BE, 9 API e 12 DB/INT aprovados. Bootstrap repetido, disputa de e-mail, inativação, primeiro acesso e preservação da auditoria verificados. Ruff, mypy e DOC aprovados. |
| IAM-03 | CONCLUIDO | [Matriz de autorização](../arquitetura/autorizacao.md). 30 BE, 9 API e 13 DB/INT aprovados. O ensaio HTTP usou sessão e papéis no PostgreSQL e um adaptador de designação de teste. Ruff, mypy e DOC aprovados. |
| IAM-04 | CONCLUIDO | [Roteiro no navegador](../testes/iam-04-navegador.md). 11 FE, 9 API e ensaio Edge/Vite/FastAPI/PostgreSQL aprovados. Lint, tipos, build e DOC aprovados. |

Acrescente linha por tarefa realmente executada com comandos, resultado e commit
ou link de relatório. A numeração das seções não substitui as dependências.

## Fundação

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [FND-01](01-fundacao/FND-01-fontes-de-verdade.md) | Validar fontes, normalizações e glossário | MOD-00–MOD-12 | P00 | CONCLUIDO |
| [FND-02A](01-fundacao/FND-02A-propostas-de-adrs.md) | Propor decisões arquiteturais | MOD-00 | FND-01 | CONCLUIDO |
| [FND-02B](01-fundacao/FND-02B-aprovacao-dos-gates.md) | Registrar escolhas e fechar gates aplicáveis | MOD-00 | FND-02A | CONCLUIDO |
| [FND-03](01-fundacao/FND-03-modelo-logico.md) | Revisar MER e modelo lógico | MOD-01–MOD-12 | FND-01, FND-02B, GATE-01, GATE-02, GATE-03, GATE-05 | CONCLUIDO |
| [FND-04](01-fundacao/FND-04.md) | Scaffold do backend Python | MOD-00 | FND-03, GATE-01, GATE-03, GATE-06 | CONCLUIDO |
| [FND-05](01-fundacao/FND-05.md) | PostgreSQL de teste, ORM e migrations | MOD-00 | FND-04 | CONCLUIDO |
| [FND-06](01-fundacao/FND-06.md) | Convenções REST, contratos e testes de API | MOD-00 | FND-04, FND-05 | CONCLUIDO |
| [FND-07](01-fundacao/FND-07.md) | Scaffold React, TypeScript e Vite | MOD-00 | FND-02B | CONCLUIDO |
| [FND-08](01-fundacao/FND-08.md) | Auditoria e eventos duráveis mínimos | MOD-00, MOD-12 | FND-05, FND-06 | CONCLUIDO |

## MVP — identidade, pessoas e comunicação

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [IAM-01](02-identidade-pessoas/IAM-01.md) | Adaptador de autenticação | MOD-01 | FND-06, GATE-02, GATE-06 | CONCLUIDO |
| [IAM-02](02-identidade-pessoas/IAM-02.md) | Usuário, papéis e perfis de domínio | MOD-01 | FND-05, IAM-01 | CONCLUIDO |
| [IAM-03](02-identidade-pessoas/IAM-03.md) | Permissões e acesso a recursos | MOD-01 | IAM-02 | CONCLUIDO |
| [IAM-04](02-identidade-pessoas/IAM-04.md) | Login e sessão no frontend | MOD-01 | FND-07, IAM-01, IAM-02, IAM-03 | CONCLUIDO |
| [IAM-05](02-identidade-pessoas/IAM-05.md) | Recuperação de acesso por e-mail | MOD-01, MOD-12 | IAM-01, IAM-04, NTF-01 | BLOQUEADO |
| [PES-01](02-identidade-pessoas/PES-01.md) | Cadastro e manutenção de funcionários | MOD-01 | IAM-02, IAM-03, IAM-04, FND-08, NTF-01 | BLOQUEADO |
| [PES-02](02-identidade-pessoas/PES-02.md) | Cadastro e manutenção de clientes | MOD-01 | IAM-02, IAM-03, IAM-04, FND-08, NTF-01 | BLOQUEADO |
| [PES-03](02-identidade-pessoas/PES-03.md) | Designação de instrutor responsável | MOD-02 | PES-01, PES-02 | BLOQUEADO |
| [NTF-01](02-identidade-pessoas/NTF-01.md) | Notificações e adaptador de e-mail | MOD-12 | FND-08, IAM-02, IAM-04 | PRONTO |

## MVP — onboarding e avaliações

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [ONB-02](03-onboarding/ONB-02.md) | Persistência do onboarding e avaliações versionadas | MOD-03 | PES-02, FND-05 | BLOQUEADO |
| [ONB-01](03-onboarding/ONB-01.md) | Convite e acesso por link seguro | MOD-03, MOD-12 | ONB-02, NTF-01 | BLOQUEADO |
| [ONB-03](03-onboarding/ONB-03.md) | Formulário e consulta responsivos do onboarding | MOD-03 | ONB-01, ONB-02, IAM-04 | BLOQUEADO |
| [ONB-04](03-onboarding/ONB-04.md) | Avaliação profissional e acesso por designação | MOD-02, MOD-03 | ONB-02, PES-03, IAM-04 | BLOQUEADO |

## MVP — equipamentos

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [EQP-01](07-complementares/EQP-01.md) | Equipamentos disponíveis e cadastro administrativo | MOD-10 | FND-05, IAM-03, IAM-04 | PRONTO |

O caminho histórico 07-complementares foi preservado; a fase do cartão é MVP.
Dados de exemplo serão criados somente ao implementar os testes/seeds.

## MVP — exercícios e fichas

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [TRN-01](04-treinos/TRN-01.md) | Catálogo de exercícios | MOD-04, MOD-10 | FND-05, IAM-03, IAM-04, EQP-01 | BLOQUEADO |
| [TRN-02](04-treinos/TRN-02.md) | Ficha manual e versões imutáveis | MOD-04 | TRN-01, ONB-02, PES-03 | BLOQUEADO |
| [TRN-03](04-treinos/TRN-03.md) | Publicação e avaliação posterior da ficha | MOD-04, MOD-02, MOD-12 | TRN-02, PES-03, NTF-01 | BLOQUEADO |
| [TRN-04](04-treinos/TRN-04.md) | Ficha atual no celular e exportação autorizada | MOD-04 | TRN-03, IAM-04 | BLOQUEADO |

## MVP — RAG, IA e aceite integrado

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [RAG-01](05-ia-rag/RAG-01.md) | Corpus, versões e aprovação documental | MOD-05 | FND-03, FND-05, IAM-03, GATE-04, IAM-04 | PRONTO |
| [RAG-02](05-ia-rag/RAG-02.md) | Conexão ao banco vetorial especializado | MOD-05 | FND-04, FND-06, RAG-01, GATE-06 | BLOQUEADO |
| [RAG-03](05-ia-rag/RAG-03.md) | Extração PDF e TXT com proveniência | MOD-05 | FND-04, RAG-01 | BLOQUEADO |
| [RAG-04](05-ia-rag/RAG-04.md) | Chunking, embeddings e indexação idempotente | MOD-05 | FND-05, RAG-02, RAG-03 | BLOQUEADO |
| [RAG-05](05-ia-rag/RAG-05.md) | Recuperação, citações e avaliação vetorial | MOD-05 | RAG-04 | BLOQUEADO |
| [AI-01](05-ia-rag/AI-01.md) | Triagem acadêmica do onboarding e regras de restrição | MOD-06, MOD-10 | ONB-04, TRN-01, EQP-01, GATE-04 | BLOQUEADO |
| [AI-02](05-ia-rag/AI-02.md) | Schemas, prompts e orquestrador de etapas fixas | MOD-06 | AI-01, RAG-05 | BLOQUEADO |
| [AI-03](05-ia-rag/AI-03.md) | Geração e persistência de proposta de treino | MOD-06, MOD-04, MOD-10 | AI-02, TRN-03, EQP-01 | BLOQUEADO |
| [AI-04](05-ia-rag/AI-04.md) | Solicitação, acompanhamento e comunicação com instrutor | MOD-06, MOD-04, MOD-12 | AI-03, TRN-03, NTF-01 | BLOQUEADO |
| [AI-05](05-ia-rag/AI-05.md) | Chat e adaptação versionada do treino | MOD-06 | AI-04, TRN-04, ONB-03 | BLOQUEADO |
| [AI-06](05-ia-rag/AI-06.md) | Avaliação automatizada da IA | MOD-05, MOD-06, MOD-04, MOD-10 | AI-01, AI-02, AI-03, AI-04, AI-05 | BLOQUEADO |
| [TST-01](05-ia-rag/TST-01.md) | Aceitação ponta a ponta do MVP | MOD-00, MOD-01, MOD-02, MOD-03, MOD-04, MOD-05, MOD-06, MOD-10, MOD-12 | IAM-05, PES-03, ONB-03, ONB-04, EQP-01, TRN-04, AI-06 | BLOQUEADO |

## Pós-MVP — matrícula e controle de acesso

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [MEM-01](06-acesso/MEM-01.md) | Planos e matrícula manual mínima, sem pagamento obrigatório | MOD-08 | FND-05, PES-02, IAM-04, GATE-08 | BLOQUEADO |
| [ACS-01](06-acesso/ACS-01.md) | Cadastro e substituição da referência biométrica | MOD-07 | PES-02, IAM-04, NTF-01, MEM-01, GATE-08 | BLOQUEADO |
| [ACS-02](06-acesso/ACS-02.md) | Captura facial e integração real de reconhecimento | MOD-07 | FND-06, ACS-01 | BLOQUEADO |
| [ACS-07](06-acesso/ACS-07.md) | API externa fictícia de catraca | MOD-07 | FND-06, GATE-08 | BLOQUEADO |
| [ACS-03](06-acesso/ACS-03.md) | Motor de autorização de entrada | MOD-07, MOD-08 | ACS-02, MEM-01, ACS-07 | BLOQUEADO |
| [ACS-04](06-acesso/ACS-04.md) | Liberação manual auditada | MOD-07, MOD-12 | ACS-03, FND-08, IAM-04, GATE-08 | BLOQUEADO |
| [ACS-05](06-acesso/ACS-05.md) | Frequência e lotação consistentes | MOD-07 | ACS-03 | BLOQUEADO |
| [ACS-06](06-acesso/ACS-06.md) | Interfaces de acesso, frequência e lotação | MOD-07 | ACS-05, IAM-04 | BLOQUEADO |

## Pós-MVP — complementares

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [AUL-01](07-complementares/AUL-01.md) | Agenda de aulas por ocorrências | MOD-09 | IAM-03, IAM-04 | PRONTO |
| [AUL-02](07-complementares/AUL-02.md) | Reserva e capacidade de aulas opcionais | MOD-09 | AUL-01, GATE-07 | BLOQUEADO |
| [DSH-01](07-complementares/DSH-01.md) | Dashboard administrativo base | MOD-11 | PES-02, PES-01, ACS-05, MEM-01, IAM-04 | BLOQUEADO |

## Financeiro tardio

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [MEM-00](06-acesso/MEM-00.md) | Registro manual opcional de pagamento | MOD-08 | MEM-01, IAM-04 | BLOQUEADO |
| [FIN-01](08-financeiro/FIN-01.md) | Cobranças e consulta financeira | MOD-08 | MEM-01, IAM-04 | BLOQUEADO |
| [FIN-02](08-financeiro/FIN-02.md) | Compra e confirmação por gateway | MOD-08 | FIN-01, NTF-01, GATE-09 | BLOQUEADO |
| [FIN-03](08-financeiro/FIN-03.md) | Indicadores financeiros | MOD-08, MOD-11 | FIN-02, DSH-01 | BLOQUEADO |

## Infraestrutura final

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [INF-01](09-infraestrutura/INF-01.md) | Dockerfiles da aplicação | MOD-00 | PG-01, PG-03 | BLOQUEADO |
| [INF-02](09-infraestrutura/INF-02.md) | Compose dos serviços selecionados | MOD-00 | INF-01 | BLOQUEADO |
| [INF-03](09-infraestrutura/INF-03.md) | Rede, volumes e restrição de exposição | MOD-00 | INF-02 | BLOQUEADO |
| [INF-04](09-infraestrutura/INF-04.md) | Instalação e teste integrado em Docker | MOD-00 | INF-03, TST-01 | BLOQUEADO |

## Validação final

| ID / texto | Entrega | Módulos | Depende de | Estado |
|---|---|---|---|---|
| [VAL-01](10-validacao-final/VAL-01.md) | Rastreabilidade e escopo final | MOD-00–MOD-12 | PG-02 | BLOQUEADO |
| [VAL-02](10-validacao-final/VAL-02.md) | Aceitação e regressão dos módulos finais | MOD-00–MOD-12 conforme escopo | VAL-01 | BLOQUEADO |
| [VAL-03](10-validacao-final/VAL-03.md) | Documentação e roteiro de demonstração acadêmica | MOD-00 | VAL-02, INF-04 | BLOQUEADO |

## Fronteira do MVP

Fundação + IAM + PES + NTF + ONB + EQP-01 + TRN + RAG + AI + TST-01 compõem o MVP.
O cenário central vai do cadastro ao treino publicado e chat antes do parecer,
com avaliação posterior, bloqueio de saúde, equipamentos disponíveis, retenção de
15 versões, saída em português, ficha manual e adaptação versionada.
MEM/ACS e demais módulos entram após esse aceite.
A matriz detalhada do MVP está na estratégia de testes e nos cartões.
AUL-02 é opcional e depende de requisito complementar. Financeiro permanece tardio.
MEM-00 é opcional nessa fase, com caminho preservado; matrícula/acesso não dependem
dele nem de pagamento confirmado.
INF-01 exige PG-01 e PG-03; testes ocorrem desde a fundação, antes de Docker.

## Leitura antes da implementação

Consultar a [revisão vigente](../testes/revisao-dos-prompts.md), depois mestre,
contexto/contrato e o cartão escolhido. São 15 MRFs/67 critérios; fontes e decisões
funcionais já autorizadas não precisam ser reaprovadas. GATE-01–GATE-06 estão
fechados documentalmente. A preparação FND-01–FND-03, a estrutura do backend
FND-04 e a base PostgreSQL FND-05 estão concluídas. FND-06 concluiu os contratos REST. FND-07 concluiu a base do frontend. FND-08 concluiu auditoria e eventos. A fundação e IAM-01 a IAM-04 estão concluídos. NTF-01 é o próximo prompt
recomendado para o MVP. Gates pós-MVP e marcos
de execução permanecem abertos até suas evidências reais.

PG-02 não depende dos próprios cartões VAL. Reservas e financeiro opcionais/adiados
exigem registro explícito de escopo/dispensa; não omitir requisitos silenciosamente.
