# 10 — Corrigir a verificação da revisão do Alembic

## Tarefa

Corrigir `test_migration_roundtrip_and_metadata` para verificar a revisão efetivamente declarada pelo Alembic. Preserve o teste de ida e volta e a comparação do schema físico com os modelos.

## Escopo permitido

- Função `test_migration_roundtrip_and_metadata` e imports necessários em `backend/tests/ai/test_generation.py`.
- Registro da nova execução em `docs/testes/comandos.md` e recompilação da SPEC pelas fontes, se o registro mudar.

Migrations aplicadas, código da aplicação, modelos, regras de IA e dados de uso ficam fora do escopo. Preserve as evidências da auditoria original.

## Contexto e execução

Depende da [auditoria de 27/11](auditoria-2026-11-27.md). Leia FND-05, VAL-02, a estratégia de testes e o modo de isolamento da fixture de migration. A revisão auditada chegou a `0029` e o teste ainda esperava literalmente `0026`.

1. Reproduza a falha em PostgreSQL de teste, com transação isolada e rollback.
2. Obtenha a revisão esperada pela configuração e pelos scripts do Alembic, usando o grafo de migrations. Exija um head único e compare o head esperado com a revisão instalada. Mantenha explícito o ponto histórico `0013` e confira que o downgrade realmente o alcançou.
3. Compare os metadados do schema `academia` antes do downgrade e após o novo upgrade. Preserve o filtro de schema e falhe diante de divergência. A revisão instalada é a saída verificada, não a origem do valor esperado.

## Critérios de aceite

- O teste sobe até o head declarado, reverte a `0013` e retorna ao mesmo head.
- A comparação de metadados passa nos dois pontos e identifica divergência como erro.
- A asserção final funciona com a próxima migration válida sem atualizar um número fixo. Heads múltiplos inesperados permanecem visíveis como falha.
- O ambiente de teste confirma rollback. A aplicação, as migrations e os resultados anteriores permanecem preservados.

## Testes esperados

A partir de `backend/`, configure `ACADEMIA_TEST_DATABASE_URL` para o PostgreSQL isolado conforme `docs/testes/comandos.md`. Rode os testes relacionados.

```powershell
uv run --locked pytest -o addopts='' --tb=short tests/ai/test_generation.py::test_migration_roundtrip_and_metadata
uv run --locked pytest -o addopts='' -m database --tb=short
```

Rode `git diff --check` e as verificações documentais se houver atualização de evidência. Corrija somente o que estiver no escopo. Registre falhas de ambiente ou divergência de schema separadamente.

## Formato da resposta

Siga o `AGENTS.md`. Em até oito linhas, informe arquivos alterados, testes executados, resultados e pendências.
