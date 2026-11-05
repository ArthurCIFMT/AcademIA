# ADR-002 — Identidade integrada e papéis

Status: ACEITA
Data: 2026-11-04
Origem: responsável delegou a seleção de frameworks, campos e regras técnicas;
academia única foi escolhida expressamente. Escolhas registradas sem exigir nova aprovação.

Decisão: autenticação integrada, sem Keycloak/OIDC no MVP. Senhas Argon2id por
pwdlib; sessão opaca aleatória de 32 bytes, persistir apenas hash SHA-256 do token.
Cookie HttpOnly, SameSite=Lax, Secure em HTTPS; localhost HTTP permitido só no
desenvolvimento. Expiração absoluta 12 h e inatividade 30 min. Logout/redefinição
de senha revogam sessões. Não colocar credenciais em localStorage.
CSRF de sessão em cabeçalho e validação de Origin nas mutações; login também
valida origem. Vite proxy /api em desenvolvimento e mesma origem no deploy final.
Login REST JSON: email/senha. Erros 401/403 distintos, sem enumeração de e-mail na
recuperação. Limite configurável de login: 5 falhas por conta/IP em 15 min.
Senha 10–128 caracteres, sem regra artificial de composição; Argon2 recomendado
pela biblioteca, não registrar senha/token em log.

USUARIO.email é único após trim/lowercase, inclusive inativos; não remover pontos
ou sufixos específicos do provedor. UUID interno é identidade. Sem CPF obrigatório.
Uma conta acumula CLIENTE/ADMINISTRADOR/ATENDENTE/INSTRUTOR.
Conta INATIVA/BLOQUEADA impede toda sessão; perfil cliente inativo remove só
capacidades de cliente, perfil funcionário inativo remove capacidades operacionais.
Demais perfis ativos continuam, desde que conta ativa. Mudança de papéis/estado
é aplicada no backend em cada requisição, não apenas na interface.
Último administrador operacional ativo não pode ser removido pelo fluxo comum;
bootstrap CLI idempotente por configuração, nunca senha padrão fixa ou endpoint público.

Primeiro acesso: funcionário autorizado provisiona conta e envia link para definir
senha (24 h). Recuperação: token de uso único (30 min). Onboarding: convite separado
(48 h) e sessão restrita; não cria sessão geral. Todos aleatórios, só hash no banco.
Sem laudos, registros profissionais externos ou aprovação médica.

Alternativa OIDC foi descartada no MVP para reduzir serviços antes do Docker.
Fonte para hashing: [FastAPI / pwdlib](https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/).
Sessão opaca/CSRF acima são decisões do projeto; não se afirma que sejam o fluxo
JWT do tutorial.
