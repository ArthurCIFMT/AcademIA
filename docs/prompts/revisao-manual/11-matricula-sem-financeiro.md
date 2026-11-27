# 11 — Corrigir o teste de matrícula sem módulo financeiro

## Tarefa

Corrigir a montagem de `test_attendant_enrolls_and_renews_without_financial_dependency` para testar a independência da matrícula com o schema atual de identidade e pessoas, inclusive quando as tabelas financeiras estiverem ausentes.

## Escopo permitido

- Teste de integração e fixtures estritamente necessárias em `backend/tests/memberships/test_memberships.py`.
- Registro da nova execução em `docs/testes/comandos.md` e recompilação da SPEC pelas fontes, se o registro mudar.

As migrations, o backend da aplicação, as regras de matrícula e cobrança, a interface, os iniciadores e o banco de uso ficam fora do escopo.

## Contexto e execução

Depende da [auditoria de 27/11](auditoria-2026-11-27.md). Leia RF-31, especialmente CA-31.1 e CA-31.5, RN-22, RN-24, MEM-01, FIN-02 e VAL-02. A variante sem financeiro monta `0024`, e o login do código atual consulta `usuario.endereco`, introduzida em `0028`. O HTTP 500 ocorre antes da matrícula. No schema atual, a auditoria já confirmou criação e renovação sem pagamento e sem consultas a tabelas financeiras.

1. Reproduza a variante antiga em um banco de teste descartável. Monte o head vigente nos três cenários. Mantenha o login real da API e os papéis diferentes.
2. Na variante sem módulo financeiro, isole a ausência na fixture de teste. Depois de aplicar o head e confirmar o destino com `check_database`, remova somente as tabelas financeiras de `academia` dentro da transação que será revertida. Confira as dependências declaradas e remova dependentes antes da tabela referenciada. No schema auditado, são `pagamento`, `cobranca_revisao` e `cobranca`. Use nomes explícitos, sem `CASCADE`, e confirme a ausência por inspeção.
3. Mantenha as variantes com pagamento pendente e recusado usando as tabelas financeiras reais no schema atual. Se a montagem sem tabelas encontrar dependência inesperada, registre a falha e o vínculo em vez de suprimir a exceção ou alterar migrations. Um cenário com zero pagamentos complementa a prova, mas não substitui o cenário sem tabelas financeiras.

## Critérios de aceite

- Com as tabelas financeiras ausentes, o login funciona e o atendente cria e renova pela API. A resposta e nova consulta confirmam a matrícula, o responsável, as datas e o histórico.
- Pagamento pendente ou recusado não bloqueia criação ou renovação. Mantêm-se as verificações de replay, sobreposição, plano inativo e revisões.
- Cliente, instrutor e administrador sem permissão de matrícula continuam recebendo a negativa prevista. Mutações mantêm sessão, origem e CSRF.
- A manipulação de schema afeta apenas o PostgreSQL de teste, com rollback confirmado. As três variantes executam sem `skip` ou `xfail` novos.

## Testes esperados

A partir de `backend/`, configure `ACADEMIA_TEST_DATABASE_URL` para o PostgreSQL isolado conforme `docs/testes/comandos.md`. Execute os testes relacionados com dados sintéticos.

```powershell
uv run --locked pytest -o addopts='' --tb=short tests/memberships/test_memberships.py
uv run --locked pytest -o addopts='' --tb=short tests/access/test_authorization.py tests/billing/test_checkout.py
```

Rode `git diff --check` e a verificação documental se registrar evidência. Corrija somente o que estiver no escopo. O aceite de VAL-02 continua uma verificação própria após as duas correções.

## Formato da resposta

Siga o `AGENTS.md`. Em até oito linhas, informe arquivos alterados, testes executados, resultados e pendências.
