# 07 — Triagem e respostas “Não sei”

**Estado da entrega: CONCLUÍDO.** Política v2 e regressão determinística aprovadas na revisão.

Ao reusar o cartão, execute primeiro a verificação focal. A correção fica limitada aos caminhos abaixo e depende de uma regressão reproduzida.

## Tarefa

Diferenciar incerteza essencial de informação complementar, evitando uma interrupção genérica por toda ocorrência de `NAO_SEI`. Manter os bloqueios de segurança e a origem dos dados.

## Escopo permitido

- `backend/app/modules/ai/policies/triage.py` para a política e sua versão e `backend/app/modules/ai/triage/` para decisão, motivos e contratos. Em `backend/app/modules/ai/orchestration/`, somente a propagação do resultado de triagem, se a quebra estiver reproduzida.
- `frontend/src/features/ai-training/`, `training-chat/` e `onboarding/` somente para mostrar pendência e abrir a etapa correspondente.
- Testes focais em `backend/tests/ai/`, `backend/tests/onboarding/`, FE dos estados e jornada E2E-03. Atualizações de política/especificação, RF-12/13/15/19, RN-13/15/16 e MRF03/08/14 afetados.

Orçamento de chamadas, provedor, fallback, evidências RAG, publicação, permissões e escopo etário permanecem conforme o SPEC. Dados desconhecidos devem continuar reconhecíveis no DTO e no histórico.

## Contexto e execução

Depende de 01. Use snapshots com idade válida para isolar o comportamento de triagem. Confira AI-01/05/06, a política vigente e as razões retornadas pelo motor. Antes de alterar código, explicite quais perguntas e combinações a política considera essenciais e quais são complementares, com base nos requisitos vigentes. Caso uma situação de saúde ainda precise de decisão, preserve o bloqueio atual desse caso e registre a lacuna. Casos graves declarados ou sinais relevantes mantêm precedência.

Preserve `NAO_SEI` no snapshot e no resumo da IA. Quando o dado for essencial, retorne `DADOS_INSUFICIENTES` e indique ao titular o campo a completar, com link à etapa e preservação das demais respostas. Quando for complementar e os dados restantes sustentarem a decisão, permita seguir as etapas normais com a incerteza explícita. Adaptação por condição de saúde continua exigindo evidência pertinente. Distinga estado de dados, bloqueio de segurança e erro técnico.

## Critérios de aceite

- Um único desconhecido complementar autorizado pela política pode seguir sem conversão para “Não”. Uma pendência essencial indica o campo e não publica ficha enquanto faltar dado.
- Caso grave com informação desconhecida continua bloqueado. Ausência de idade, onboarding inválido e falha do provedor permanecem distinguíveis.
- Reabrir e confirmar o formulário cria nova versão conforme contrato. Não há nova chamada automática, bypass dos limites ou readaptação silenciosa da ficha.
- Resultado para adaptação sem evidência suficiente permanece abstenção. O treino manual continua disponível.

## Testes e entrega

Em `backend/` com PostgreSQL isolado:

```powershell
uv run --locked pytest -o addopts='' tests/ai/test_triage.py tests/ai/test_triage_integration.py tests/ai/test_generation.py::test_persistent_service_blocks_grave_or_unknown_before_network
```

Em `frontend/`:

```powershell
npm test -- src/features/ai-training/AITraining.test.tsx src/features/training-chat/TrainingChat.test.tsx tests/onboarding/Onboarding.test.tsx
```

Confira na política v2 a medicação desconhecida isolada com respostas essenciais negativas e observações vazias. Depois exercite desconhecido essencial, evento grave e falha técnica. A primeira variante segue para análise com incerteza explícita. Os demais casos retornam o bloqueio, a pendência ou a falha correspondentes. E2E-03 confirma a experiência de bloqueio e E2E-04 confirma a revisão de dados. Se a política mudar, rode a avaliação determinística documentada, com modelos controlados e E5 local. Um ensaio com provedor real segue o orçamento aprovado de AI-06.
