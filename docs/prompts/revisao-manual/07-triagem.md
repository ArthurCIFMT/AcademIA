# 07 — Triagem e respostas “Não sei”

## Tarefa

Diferenciar incerteza essencial de informação complementar, evitando uma interrupção genérica por toda ocorrência de `NAO_SEI`. Manter os bloqueios de segurança e a origem dos dados.

## Escopo permitido

- `backend/app/modules/ai/triage/`, ajustes diretamente necessários em `backend/app/modules/ai/orchestration/` e schemas de onboarding se o contrato aprovado exigir.
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

Cubra a matriz de triagem com casos sintéticos em `test_triage.py`, `test_triage_integration.py`, testes de geração e jornadas afetadas. Rode a regressão determinística de IA conforme `docs/testes/comandos.md`. Ensaio real, se necessário, deve usar o protocolo e o orçamento aprovados do AI-06. Preserve os relatórios anteriores. Próximo 08 ou outra etapa elegível.
