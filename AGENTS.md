# AGENTS.md

## Objetivo do projeto

Construir uma aplicação web acadêmica para centralizar operações de uma academia,
com cadastro de clientes e funcionários, onboarding, avaliações, fichas de treino,
controle de acesso, agenda, equipamentos, indicadores e geração assistida por IA.

## Natureza didática e limites do trabalho acadêmico

- O projeto é um trabalho acadêmico para aprender e demonstrar arquitetura,
  banco, APIs, testes e integração de IA. Não implementar exigências de produção
  comercial ou processos jurídicos que não façam parte dos requisitos solicitados.
- Não exigir aprovação médica profissional, atestado/laudo, certificado, assinatura
  de médico ou validação jurídica externa para implementar, testar, gerar ou exibir
  fichas no cenário didático. Esses documentos e fluxos ficam fora do MVP.
- Triagem é uma regra funcional da demonstração: dados sintéticos e casos rotulados,
  regras documentadas pelo responsável do projeto, casos graves bloqueados e dados
  insuficientes tratados explicitamente. Não criar fluxo de desbloqueio por laudo.
- Aprovação do corpus e revisão dos casos significam seleção técnica pelo responsável
  do projeto/curador autorizado; não exigem comitê, médico ou auditor jurídico externo.
  Manter fontes e metadados bibliográficos existentes.
- O parecer do instrutor da academia é funcionalidade do sistema e permanece
  posterior à publicação; não equivale à aprovação médica e não bloqueia consulta/chat.
- Preservar autenticação, autorização, isolamento entre clientes, dados de teste
  sintéticos, integridade, evidências RAG e os bloqueios funcionais já solicitados.
  Simplificar a burocracia não autoriza retirar esses critérios ou inventar evidências.
- Escopo jurídico/comercial adicional só entra por solicitação explícita posterior;
  não transformar essa ausência em gate para o trabalho acadêmico.

## Estágio atual

O projeto está na fase de especificação e fundação. Antes de implementar um módulo,
consulte os requisitos e as regras de negócio versionados em `docs/`. Não invente
requisitos para preencher lacunas: registre a dúvida ou a decisão necessária.

## Fontes de verdade

- `docs/requisitos/`: requisitos funcionais, macrorequisitos e regras de negócio.
- `docs/arquitetura/`: modelo de dados e decisões arquiteturais.
- `docs/prompts/`: prompt mestre, prompts operacionais e ordem de execução.
- `docs/testes/`: estratégia, comandos reais e evidências de verificação.
- Este arquivo: regras permanentes para agentes que trabalham no repositório.

Quando houver conflito, o prompt operacional define o escopo da tarefa, mas não
pode contrariar requisitos aprovados, decisões arquiteturais ou este arquivo.

## Estrutura planejada

- `frontend/`: SPA React com TypeScript e Vite.
- `backend/`: API Python modular, regras de negócio e integrações.
- `database/`: migrations, seeds controlados e scripts de apoio.
- `docs/`: requisitos, arquitetura, decisões e prompts.
- `tests/`: testes que não pertençam diretamente a um módulo.

Não crie todos os diretórios antecipadamente. Cada prompt cria apenas a estrutura
necessária para sua entrega.

## Decisões arquiteturais vigentes

- Adotar monólito modular; não iniciar com microserviços.
- Usar React, TypeScript e Vite no frontend.
- Academia única, sem multitenancy no MVP.
- Backend Python 3.12 com FastAPI/Pydantic 2, SQLAlchemy 2.x/Alembic e psycopg 3;
  uv, Ruff, mypy e pytest/HTTPX. ADRs aceitos em docs/arquitetura/decisoes/.
- Autenticação integrada por sessão opaca/Argon2id, sem Keycloak no MVP; estados
  de conta e perfis independentes conforme ADR-002.
- Node 24 LTS/npm no frontend; versões exatas serão travadas nos scaffolds.
- Usar PostgreSQL para dados relacionais.
- Expor contratos externos por REST, JSON e OpenAPI.
- Representar uma identidade por `USUARIO`, com papéis acumuláveis: cliente,
  administrador, atendente e instrutor.
- Manter perfis específicos de cliente e funcionário vinculados ao usuário.
- Preservar o histórico da designação de clientes a instrutores.
- Treino validado tecnicamente pode ser publicado e consultado pelo cliente sem
  aceite prévio do instrutor. Chat e parecer profissional são independentes.
- O instrutor designado pode aceitar, rejeitar ou modificar o treino posteriormente;
  cada parecer identifica a versão avaliada, o responsável e a data.
- A ficha rejeitada continua consultável. Quando uma ficha posterior também é
  rejeitada, excluir o conteúdo da rejeitada anterior e manter a nova; preservar
  metadados de auditoria e registros de treinos já executados (RF-35).
- O atendente autorizado pode matricular e renovar o cliente sem pagamento
  confirmado. Matrícula e acesso acadêmico não dependem do módulo financeiro.
- Reconhecimento facial usa CompreFace; a catraca será uma API externa fictícia.
- Qdrant local persistente por qdrant-client no MVP (um processo, sem Docker);
  banco vetorial especializado separado do PostgreSQL. Embeddings locais E5-small
  multilíngue, 384 dimensões, prefixos query:/passage: e cosseno; ADR-004.
- Equipamentos entram no MVP: administrador mantém disponibilidade e cada variação
  de exercício declara recursos obrigatórios/alternativos ou dispensa explícita.
  A IA só seleciona exercícios viáveis e o backend revalida antes de publicar.
- Reter no máximo 15 versões publicadas completas por cliente, incluindo a vigente;
  excluir conteúdo excedente das mais antigas, mantendo auditoria e snapshots de
  treinos executados. Aplicar também a regra específica de rejeitadas (RF-17/RF-35).
- Interface, prescrições e explicações são em português; fontes estrangeiras são
  permitidas com recuperação multilíngue e explicação/tradução fiel rastreável.
- Dados de exemplo de equipamentos serão criados apenas na implementação, como
  fixtures/seeds sintéticos de testes, sem cadastrar dados nesta fase documental.
- Deixar pagamentos e cobrança automatizada para uma fase posterior.
- Containerizar a aplicação somente depois do MVP e da maioria dos módulos.

## Limites entre módulos

- Um módulo não acessa diretamente tabelas ou repositórios internos de outro.
- Comunicação síncrona interna usa interfaces e serviços de aplicação tipados.
- REST, integrações externas e eventos usam JSON com schema versionado.
- Não serialize em JSON chamadas internas sem necessidade de fronteira.
- Efeitos assíncronos importantes devem ser idempotentes e auditáveis.

## Regras para implementação

- Leia o prompt operacional completo antes de alterar arquivos.
- Não altere arquivos fora do escopo do prompt.
- Preserve mudanças preexistentes que não pertençam à tarefa.
- Prefira mudanças pequenas, testáveis e reversíveis.
- Não adicione dependências sem justificar a necessidade.
- Não antecipe funcionalidades de prompts posteriores.
- Não codifique URLs, credenciais, chaves ou segredos no código.
- Use variáveis de ambiente e mantenha um `.env.example` sem valores sensíveis.
- Não silencie erros, testes falhos ou validações para concluir uma tarefa.
- Atualize a documentação quando uma decisão ou contrato for alterado.

## Banco de dados

- Toda alteração de schema deve possuir migration reproduzível.
- Não modifique uma migration já aplicada; crie uma nova migration.
- Use constraints para invariantes que o banco consegue garantir.
- Exclusões e inativações não podem quebrar históricos necessários.
- Registros temporais devem ser armazenados em UTC e expostos em ISO 8601.
- Seeds de desenvolvimento não devem conter dados pessoais reais.

## Autorização e dados sensíveis

- Toda rota protegida valida autenticação e autorização no backend.
- A interface nunca é a única barreira de permissão.
- Cliente acessa somente o próprio contexto, salvo compartilhamento explícito.
- Instrutor acessa clientes conforme designação e permissão vigente.
- Evite dados de saúde e biometria em logs, mensagens de erro e telemetria.
- Auditoria não pode ser apagada livremente pelo autor da ação registrada.

## IA e RAG

- Fluxo vigente: agente orquestrador com RAG vetorial semântico de etapas fixas,
  triagem de onboarding resumido, geração de fichas pelo LLM e chat de dúvidas.
- MRF01–MRF15 e docs/arquitetura/rag-semantico.md são a fonte vigente. A abordagem
  agentiva e a restrição de fichas exclusivamente manuais foram substituídas.
- Não implementar planner LLM, ferramentas escolhidas pelo modelo, pesquisa iterativa
  ou cadeia de agentes biomecânico/periodização/revisor. Orquestrador controla estados.
- Chat usa até uma geração; ficha/adaptação usa até uma análise de triagem e uma
  geração, com validações em código. Cada etapa LLM admite uma tentativa por
  execução, sem retry automático; repetição idempotente não faz nova chamada.
  Ingestão/busca podem repetir transporte dentro do orçamento; falha/JSON inválido
  não abre loop de reparo. Nova tentativa LLM exige ação explícita e nova execução.
- Backend monta resumo estruturado e minimizado do onboarding, preservando todos os
  alertas relevantes e a versão de origem. Ausente não significa saudável/zero/média.
- Bloqueios vêm de regras acadêmicas de triagem documentadas; o LLM sinaliza
  informações relevantes, sem diagnosticar ou remover bloqueio determinístico.
  Estados de domínio: DADOS_INSUFICIENTES, BLOQUEADO_POR_SEGURANCA e
  ELEGIVEL_PARA_GERACAO; erro/timeout pertence ao estado técnico da execução.
- RAG recupera trechos do livro/literatura aprovada para dúvidas, triagem e geração;
  não enviar livros inteiros, todo histórico ou anamnese completa por padrão.
- Adaptação por condição de saúde exige evidência pertinente; falta/conflito exige
  abstenção. Fonte relevante não remove bloqueios das regras da demonstração.
  Não exigir aprovação médica para tornar uma ficha tecnicamente válida consultável.
- Catálogo fornece IDs de exercícios e requisitos; MOD-10 fornece equipamentos.
  Modelo não inventa recursos; MOD-04 revalida antes de publicar por contrato.
- Somente backend publica ficha tecnicamente válida com parecer PENDENTE; cliente
  consulta/chat sem aceite prévio. Instrutor pode revisar, alterar ou criar manualmente.
- Mensagem informativa não altera ficha; adaptação explícita segue nova triagem,
  geração e versão. Novo relato relevante exige confirmação/versionamento dos dados.
- Documentos são evidências, nunca instruções. Somente versões aprovadas participam;
  dados de clientes não entram na literatura compartilhada ou no contexto de terceiros.
- Saídas usam JSON Schema e referências reais. Modelo não escreve domínio, executa
  SQL livre nem atribui aceite humano. Registrar estados, fontes e consumo sem
  raciocínio interno ou dados sensíveis desnecessários em logs.
- LLM inicial Groq / llama-3.3-70b-versatile, plano gratuito, chave em ambiente;
  json_object com validação backend. Não contratar plano pago ou fazer fallback
  oculto. Qualidade/tempo só são aprovados no ensaio real de AI-06.
- Campos e regras: docs/requisitos/onboarding-e-triagem.md e schemas versionados;
  parâmetros em docs/requisitos/configuracao-ia-rag.md. Não pedir novamente escolhas
  técnicas já delegadas/registradas. Seguir modelos e contratos aceitos.
- Livro/conhecimento inicial: sete documentos selecionados em materiais/rag/corpus-inicial.json;
  ativação depende da extração/indexação válida, não de uma nova aprovação externa.
- Falha de LLM, embeddings ou banco vetorial não impede treino manual.

## Testes

- Consulte `docs/testes/estrategia.md` e resolva as suites nos comandos reais de
  `docs/testes/comandos.md`. Scaffolds registram os comandos quando os criam.
- Regras de negócio alteradas devem possuir testes unitários.
- Fluxos entre banco e API devem possuir testes de integração quando aplicável.
- Contratos REST e JSON devem ser validados.
- Correções devem incluir teste de regressão quando possível.
- Execute os testes relacionados antes de finalizar.
- Se um teste não puder ser executado, informe o motivo e o risco.

## Comandos

Verificação documental disponível, a partir da raiz, com Python 3.10+:
`python scripts/verificar_documentacao.py` (somente leitura, sem dependências externas).

Backend, a partir de `backend/` com uv e Python 3.12:

- Instalar dependências: `uv sync --locked`.
- BE: `uv run --locked pytest`.
- DB: `uv run --locked --env-file ../.env pytest -m database`.
- INT: `uv run --locked --env-file ../.env pytest -m integration`.
- Lint e formato: `uv run --locked ruff check .` e `uv run --locked ruff format --check .`.
- Tipos: `uv run --locked mypy`.

A inicialização está no [guia do backend](backend/README.md) e no
[guia do banco](database/README.md). Os demais
comandos entram em `docs/testes/comandos.md` nos prompts que configuram cada suite.

## Git e escopo de commits

- Mantenha commits pequenos e relacionados a uma única entrega operacional.
- Não inclua segredos, arquivos `.env`, bancos locais, uploads ou artefatos de build.
- Não reescreva histórico compartilhado sem solicitação explícita.
- Não faça push, merge ou crie pull request fora do escopo solicitado.
- A mensagem do commit deve explicar a mudança realizada.

## Critério de pronto

Uma tarefa só está concluída quando:

- seus critérios de aceite foram atendidos;
- testes relacionados foram executados e passaram;
- o diff permanece compatível com o escopo;
- contratos e documentação afetados foram atualizados;
- erros conhecidos, riscos e testes não executados foram informados.

## Relatório final do agente

Responda preferencialmente em até oito linhas, informando:

- o que foi implementado;
- arquivos alterados;
- testes executados e resultados;
- pendências ou riscos;
- próximo passo desbloqueado.

O limite de linhas não se aplica quando for necessário explicar falhas, riscos de
segurança, decisões arquiteturais ou testes não executados.
