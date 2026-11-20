# Histórico do chat e regressão completa do MVP — 2026-11-19

## Entrega

O histórico deixava de mostrar mensagens após gerar/adaptar uma ficha porque a
consulta filtrava apenas a versão vigente. Agora a consulta inclui todos os
contextos do próprio cliente nos últimos 90 dias, em páginas de 20 turnos. A tela
identifica conversas anteriores à ficha atual. Não há limite de 15 mensagens:
15 é a retenção de versões completas de ficha, independente da paginação do chat.

Novas perguntas continuam enviando ao modelo somente a janela de até três
perguntas do contexto vigente; leitura/recarga não chamam RAG/LLM. GET histórico
funciona sem reexecutar o POST antigo, que conserva suas guardas de contexto e
idempotência. Conta de outro cliente permanece sem acesso. Se a ficha de origem
foi expurgada ou sua evidência foi revogada, a resposta/fontes ficam ocultas;
a pergunta/recibo continuam conforme o prazo do chat. Não se restaura conteúdo.

CA-18.9/CA-18.10, MRF14.5, arquitetura, AI-05, schema JSON e SPEC acompanham a
correção. Campos aditivos opcionais: versao_contexto_id e contexto_anterior.
Sem migration, novo modelo LLM, mudança de prompt enviado ao LLM, corpus ou UX
planejada. Os testes também continuam verificando exercícios por ID e recursos
viáveis do catálogo na publicação, conforme o contrato de treinos existente.

## Verificação executada

| Verificação | Resultado desta entrega |
|---|---|
| Backend completo: unitários/contratos | 354 aprovados, nenhum ignorado/falho |
| Backend completo: integração/banco | 179 aprovados, 3 opt-in de LLM real ignorados, nenhuma falha final |
| Frontend completo | 94 aprovados em 20 arquivos |
| Focal de chat | 20 aprovados, já incluídos nos comandos completos; não somar novamente |
| Backend estático | Ruff, formato e mypy (236 fontes) aprovados |
| Frontend estático/build | Lint, tipos e build aprovados |

Dados sintéticos no academia_test, migrations reais com rollback, Qdrant temporário,
E5 CPU e Mailpit reais. O Mailpit usa caixa sintética separada, sem relay para
e-mails externos. Nenhuma conta ou cadastro de desenvolvimento foi alterado.
API e frontend de uso manual permaneceram desligados. PostgreSQL/Mailpit foram
iniciados para os testes e encerrados depois, com as cinco portas locais verificadas.

Foram exercitados identidade/sessão/autorização, pessoas, designações, onboarding,
avaliações, equipamento/catálogo, treino manual/publicação/parecer/retenção,
notificações/auditoria, ingestão/busca RAG e orquestração/geração/chat/quotas,
incluindo isolamento, concorrência e idempotência dos cenários existentes.
Os provedores LLM usam respostas controladas nesta regressão. Três testes
opt-in de provedor real foram ignorados intencionalmente; chaves Groq/Gemini
removidas do processo. Nenhuma quota foi consumida. Não mede disponibilidade,
qualidade ou latência atuais do modelo gratuito; não é novo aceite AI-06/TST-01,
ensaio de carga ou nova navegação E2E. Evidências históricas não foram substituídas.

Falhas intermediárias preservadas: a primeira execução unitária teve 46 erros de
setup por faltar o diretório pai de basetemp; após criá-lo, os 354 passaram. A
primeira execução completa de integração teve 178 aprovados/uma falha/três skips:
um teste ainda exigia histórico vazio após expirar a 16ª ficha. A expectativa foi
atualizada para manter o recibo visível e verificar expressamente ABSTENCAO,
contexto anterior e ausência de resposta/fontes; as demais guardas permanecem.
A repetição completa acima passou. Não houve remoção ou relaxamento de bloqueios.

## Reprodução

Na raiz, verificar SPEC e documentação. Em backend/, usar uv/Python 3.12, ambiente
de teste configurado e diretório temporário existente; executar sem chamar os
testes reais de LLM. Em PowerShell, depois de carregar a configuração, remover
GROQ_API_KEY/GEMINI_API_KEY e as flags de ensaio real do ambiente do processo.
Definir ACADEMIA_AI_REAL=0, ACADEMIA_LLM_PROFILE=principal,
ACADEMIA_TEST_MAILPIT=1, ACADEMIA_TEST_EMBEDDINGS_REAL=1 e o caminho dos pesos E5
locais. O .env não deve reintroduzir chaves: os comandos abaixo pressupõem o
ambiente já carregado e sanitizado, sem --env-file no subprocesso.

```powershell
uv run --locked pytest -q --junitxml ./data/unitarios-N.xml
uv run --locked pytest -o addopts='' -m 'integration or database' -q --junitxml ./data/integracao-N.xml
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

A execução desta entrega usou o Python do .venv já sincronizado, cópia temporária
dos fontes e wrappers locais para carregar/sanitizar ambiente sem expor chaves;
isso não acrescenta scripts de manutenção pontual ao repositório.
No frontend: npm test -- --run --maxWorkers=1, npm run lint,
npm run typecheck e npm run build. Não instalar dependências novas.

Regressões novas em backend/tests/ai/test_chat_history.py e
frontend/src/features/training-chat/TrainingChat.test.tsx: duas publicações,
pergunta antes da primeira ficha, 23 mensagens/duas páginas, janela do modelo,
zero chamadas em leitura, outro cliente, retenção e recarga da tela.
Os testes existentes cobrem revogação e 16ª versão expurgada.

O [registro estruturado](historico-chat-mvp-20261119.json) contém hashes dos
fontes e JUnits/JSON frontend, contagens e limites; relatórios brutos e logs ficam
locais, sem credenciais/dados reais no Git. O registro focal de 20 inclui o teste
de retenção já existente; a correção posterior da expectativa da 16ª ficha foi
exercitada na repetição completa, não naquele primeiro comando focal.

## Modelagem

A [avaliação do MER](../analises/2026-11-19-tamanho-modelagem.md) distingue 18
entidades conceituais, 43 tabelas planejadas e 32 implementadas. O schema é
justificável pelo escopo; propostas de reduzir duplicação de triagem/consumo,
FK redundante e tabela conversa não foram aplicadas. A imagem original,
DBML/JSON lógico e migrations permanecem intactos.
