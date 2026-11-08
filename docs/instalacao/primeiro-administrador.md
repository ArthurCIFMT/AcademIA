# Primeiro administrador

Prepare o PostgreSQL e execute a revisão `0003` ou superior. O
[guia do banco](../../database/README.md) reúne os comandos de conexão e
migration. No `.env` local da raiz, mantenha a URL de desenvolvimento e
configure a origem do navegador conforme `.env.example`.

Na pasta `backend/`, informe ao processo o e-mail, o nome e a data de admissão
do responsável pelo ambiente. Escolha credenciais próprias ou dados sintéticos
para a demonstração acadêmica.

```powershell
$env:ACADEMIA_BOOTSTRAP_EMAIL = 'admin@academia.example.test'
$env:ACADEMIA_BOOTSTRAP_NOME = 'Admin de demonstração'
$env:ACADEMIA_BOOTSTRAP_DATA_ADMISSAO = '2026-11-07'
uv run --locked --env-file ../.env python -m scripts.bootstrap_admin
```

O comando solicita a senha sem eco. Em automação, a variável externa
`ACADEMIA_BOOTSTRAP_SENHA` fornece a senha. Repetir o comando com o mesmo
e-mail retorna sucesso e preserva a conta. O bootstrap recusa outro e-mail
quando já existe um administrador e recusa promoção de conta preexistente.

## Ensaio do primeiro login

Inicie a API pelo [guia do backend](../../backend/README.md). O exemplo abaixo
lê a senha no terminal e envia o DTO JSON com a origem configurada. Ajuste
`$origem` se o ambiente usar outro endereço.

```powershell
$origem = 'http://127.0.0.1:5173'
$segredo = Read-Host 'Senha do administrador' -AsSecureString
$senha = [System.Net.NetworkCredential]::new('', $segredo).Password
$corpo = @{ email = $env:ACADEMIA_BOOTSTRAP_EMAIL; senha = $senha } | ConvertTo-Json
$null = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8000/api/v1/auth/login' -Headers @{ Origin = $origem } -ContentType 'application/json' -Body $corpo -SessionVariable academiaSessao
$sessao = Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/auth/session' -WebSession $academiaSessao
$sessao | Select-Object user_id, expires_at
$senha = $null
$corpo = $null
```

A interface do IAM-04 vai usar os mesmos contratos. O provisionamento de
outras contas gera um token de primeiro acesso para o funcionário autorizado
encaminhar pelo módulo responsável. O cliente define a senha usando esse
token antes de entrar. [Contratos de autenticação](../arquitetura/autenticacao.md)
