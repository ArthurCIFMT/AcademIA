# Execução do cartão 12 — Segurança básica

**27/11/2026 · revisão `3c9d785b5fb2cfb976f487d3bb448b83df09bc84` · APROVADA no recorte do cartão.**

A [revisão 12](../prompts/revisao-manual/12-seguranca-basica.md) foi executada
em cópia isolada no Windows, com PostgreSQL `academia_test` em loopback,
Mailpit de teste e contas sintéticas. As transações de teste foram revertidas
e os processos isolados foram encerrados ao final.

| Item | Resultado | Evidência |
|---|---|---|
| SEG-01 · Sessão | Aprovado | Perfil próprio retorna 401 sem sessão e após logout. Login, sessão restaurada e perfil próprio retornam 200 para o titular. Escrita sem CSRF retorna 403 sem alterar o perfil. Os testes também cobrem expiração, revogação, conta inativa e origem. |
| SEG-02 · Permissões | Aprovado | Testes de papéis e designações conferem as permissões diretamente na API. Consulta alheia no ensaio retorna 403. E2E-02 verifica isolamento de dados e E2E-08 verifica navegação sem acesso administrativo indevido. |
| SEG-03 · Exposição de dados | Aprovado | O ensaio inspecionou login, sessão, cadastro, perfil e recuperação com dados sintéticos. Senha, hash, chave e token de recuperação ficaram ausentes do corpo. A resposta de recuperação foi igual para conta conhecida e desconhecida. A miniatura privada foi verificada com dublê. |
| SEG-04 · Erros | Aprovado | A aplicação de teste foi instanciada com depuração desabilitada. O teste de falha de PostgreSQL retornou 500 com envelope e correlação. O marcador interno ficou fora da resposta e do log, e o healthcheck seguiu respondendo. |
| SEG-05 · Segredos no Git | Aprovado | Os arquivos de configuração privada estão ignorados. Nos caminhos examinados, a árvore e o histórico rastreiam apenas os exemplos. A triagem na árvore, no índice e em 2.563 blobs textuais da `main` até a revisão auditada não retornou candidatos para os formatos do cartão. |

## Resultados da execução

- Backend com os seletores do cartão 12 e PostgreSQL isolado. **31 aprovados**,
  sendo 18 de sessão e permissões, três de dados sensíveis e dez de erros e contratos.
- Frontend com `tests/auth/session.test.tsx`. **11 aprovados**.
- Runner do MVP no Edge. **8 jornadas aprovadas**, incluindo E2E-02 e E2E-08.
  A jornada usa respostas controladas de IA.
- Ensaio adicional via API com contas sintéticas. **12 respostas conferidas**,
  incluindo cadastro 201, recuperação 202, logout 204 e negativas 401/403.
  O ensaio conferiu os campos sem registrar seus valores e verificou
  `HttpOnly`, `Secure` e a política de cache privada onde aplicáveis.

A triagem de conteúdo histórico cobriu formatos conhecidos do cartão em blobs
textuais de até 2 MiB. A inspeção de nomes considerou os caminhos privados
indicados no roteiro. A rodada valida as rotas e os cenários selecionados.

A próxima verificação do responsável está no [checklist manual final](checklist-manual-final.md).
