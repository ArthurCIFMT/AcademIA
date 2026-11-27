# 12 — Revisão reutilizável de segurança básica

**Estado do cartão: PRONTO.** Registre o resultado de cada rodada para a revisão
Git e o ambiente examinados.

## Tarefa

Verificar a autenticação, as permissões, a exposição de dados sensíveis, o
tratamento de erros e o versionamento de segredos do AcademIA. Use este cartão
antes da demonstração ou após mudanças em identidade, permissões, DTOs, rotas,
erros ou configuração.

## Escopo permitido

- Inspeção em leitura de `backend/app/core/http.py`, módulos de identidade,
  pessoas e autorização, contratos OpenAPI, configuração de execução e arquivos
  rastreados ou indexados no Git.
- Testes existentes e checklist no navegador, em ambiente isolado com contas e
  dados sintéticos. Registre a evidência sanitizada no relatório da rodada.
- Encaminhe uma falha ao cartão dono da rota ou da configuração. Este cartão
  autoriza revisão e evidência. Alterações de código, permissões, firewall,
  credenciais, histórico Git ou implantação exigem uma tarefa própria.

## Contexto e preparação

Leia IAM-02/03/04/05, INF-03, RN-02/04/05/10/11/23/28/29/34,
RNF-08, a estratégia de testes e os comandos em `docs/testes/`.
Para o chat e o RAG, use a matriz especializada de
`docs/testes/rag-ia-semantico.md` quando a rodada incluir esses fluxos.

Identifique o commit, o ambiente e as rotas avaliadas. Use PostgreSQL de teste
e duas contas sintéticas com papéis ou titularidades diferentes. Nesta
aplicação, a sessão é opaca e usa cookie. Valide origem e CSRF nas mutações
autenticadas. Registre apenas caminhos, códigos HTTP e nomes de campos.
Mantenha senhas, hashes, cookies, tokens, fotos e dados de saúde fora das
capturas e dos relatórios.

## Checklist e critérios de aceite

| ID | Cenário verificável | Resultado esperado |
|---|---|---|
| SEG-01 | Acesse uma rota protegida com sessão válida, sem sessão e após logout. Use os casos automatizados de sessão expirada ou revogada e de CSRF ausente em escrita. | A sessão válida permite a ação autorizada. A API recusa sessão ausente ou inválida e bloqueia mutação sem a proteção exigida, sem persistir a escrita. |
| SEG-02 | Compare uma ação própria com a mesma consulta sobre outra conta sintética. Confira uma operação permitida para o papel correto e uma chamada direta sem essa permissão. Inclua perfil, ficha/exportação ou miniatura privada quando a rodada envolver esses dados. | Só o titular ou papel autorizado obtém o dado ou realiza a ação. A API retorna a negativa do contrato, normalmente 403 ou 404. As guardas da interface são conferidas junto à API. |
| SEG-03 | Inspecione os campos das respostas de login, sessão, cadastro, perfil e recuperação. Compare a resposta permitida com a resposta negada quando houver dados pessoais. | Senhas, hashes, chaves e tokens de recuperação ficam ausentes do corpo público. Saúde, biometria e dados de outra pessoa ficam fora da resposta indevida. |
| SEG-04 | Rode a validação REST e o teste de falha de banco. Confira que o modo de execução usado para entrega tem depuração desabilitada. | Erros de entrada e de dependência retornam o envelope do contrato. A resposta 500 contém identificador de correlação e mensagem genérica, sem stack trace, SQL, caminhos internos ou dados enviados. |
| SEG-05 | Confira arquivos ignorados, árvore rastreada e índice do Git. Verifique que os exemplos de configuração contêm apenas valores de exemplo. | Arquivos privados ficam fora da árvore e do índice. Nenhuma credencial real identificada fica versionada. Registre o recorte de histórico que foi coberto. |

No navegador, use contas sintéticas para abrir a rota permitida, sair e
reabrir a mesma URL. Confira também a negativa ao tentar uma rota de outro
papel. Registre o comportamento e o código da API sem copiar a sessão.
O runner do README permite conferir E2E-02 e E2E-08 quando a rodada for ampliada.

## Testes esperados

Em `backend/`, com a URL de `academia_test` configurada no processo:

```powershell
uv run --locked pytest -o addopts='' tests/identity/test_identity.py tests/authorization/test_access.py tests/identity/test_accounts.py::test_bootstrap_authenticates_and_inactivation_denies_old_cookie
uv run --locked pytest -o addopts='' tests/people/test_clients.py::test_own_address_is_optional_and_private 'tests/access/test_facial_reference.py::test_register_replace_and_preserve_consistency[double]' tests/identity/test_recovery.py::test_failed_delivery_is_recorded_without_changing_public_response
uv run --locked pytest -o addopts='' tests/contracts/test_rest_contract.py tests/integration/test_database_error_http.py
```

Em `frontend/`:

```powershell
npm test -- tests/auth/session.test.tsx
```

Na raiz, confira nomes de arquivos e indicadores de segredos sem imprimir
conteúdo sensível:

```powershell
git check-ignore -- .env frontend/.env.local iniciador.local.json
git ls-files -- '.env' '.env.*' ':(glob)**/.env' ':(glob)**/.env.*' iniciador.local.json
git diff --cached --name-only
git log --all --format= --name-only -- '.env' '.env.*' ':(glob)**/.env' ':(glob)**/.env.*' iniciador.local.json
$securitySecretPattern = 'gsk_[A-Za-z0-9]{35,}|AQ\.[A-Za-z0-9_-]{30,}|github_pat_[A-Za-z0-9_]{35,}|ghp_[A-Za-z0-9]{25,}|-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----'
git grep -l -I -E -- $securitySecretPattern
git grep --cached -l -I -E -- $securitySecretPattern
```

No `git grep`, código 1 indica ausência de correspondência e código maior que 1
indica erro. Uma correspondência identifica um arquivo para inspeção reservada.
Confirme falsos positivos sem reproduzir o valor. Os padrões são uma triagem
da árvore e do índice. O `git log` verifica os nomes no histórico das referências
locais. Para avaliar o histórico de conteúdo, use um scanner com redação de
segredos se já estiver disponível e registre o intervalo analisado.

## Evidência e formato da resposta

Marque cada item como aprovado, falhou ou pendente. Para cada resultado,
registre a revisão, o cenário, o teste ou a observação e o motivo da negativa
quando aplicável. Um teste pulado mantém o item dependente pendente na rodada.
Ao encontrar exposição real, registre apenas tipo e caminho e encaminhe a
correção pelo fluxo responsável. Use o formato em até oito linhas do AGENTS.md.
