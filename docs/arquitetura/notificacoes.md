# Notificações e e-mail local

A composição de NTF-01 usa caminhos de ligação existentes. `backend/app/main.py`
monta a rota, `backend/app/modules/identity/composition.py` compartilha a fábrica
de sessões e `backend/app/modules/identity/roles.py` fornece a leitura de papéis
efetivos. `frontend/src/app/AppRoutes.tsx` conecta a lista às áreas protegidas.
A API reutiliza a autenticação do IAM. A migration vive em `database/`.
O teste de migração de identidade deixa a verificação global do Alembic
para o novo teste de `head`. O teste antigo continua exercitando a revisão 0003.

## Avisos persistentes

- `notify_workout_review(session, event_id, assigned_instructor_id)` registra
  a pendência para o instrutor designado informado pelo módulo responsável,
  se o papel estiver ativo. A designação continua sob responsabilidade do MOD-02.
- `notify_critical_change(session, event_id)` registra avisos para os
  administradores com conta e perfil ativos. Os produtores devem chamar o serviço
  ao confirmar alterações críticas de permissão, biometria e configuração.
- O chamador fornece o UUID estável do evento e usa sua transação de negócio.
  O evento pode ser registrado pela outbox na mesma transação. Repetir a criação
  conserva um único aviso por destinatário, evento e canal. O status do envio de
  e-mail é independente da pendência interna.

`GET /api/v1/notificacoes/pendentes` exige sessão ativa com papel de administrador
ou instrutor. Cada sessão recebe somente avisos internos do próprio usuário e dos
tipos permitidos por seus papéis efetivos. A resposta JSON contém `id`, `tipo`
e `criada_em` em ISO 8601 UTC. A lista fica disponível nas áreas administrativas
e de instrutor. Ela mostra a pendência de aviso. Revisão de treino e seu parecer
são estados do módulo dono da ficha.

## Envio pelo SMTP

`local_email_delivery(sessions)` cria o adaptador de SMTP da biblioteca padrão.
Chame `send(EmailRequest(...))` depois do commit da operação de origem. O produtor
fornece endereço, corpo e finalidade. O banco guarda estado, tentativas e
identificadores, sem endereço, corpo ou token. A operação devolve estado e
quantidade de tentativas para o produtor decidir como comunicar a falha.

A primeira chamada reserva `ENVIANDO` e confirma essa reserva antes da conexão
SMTP. Resposta positiva vira `ENVIADO`. Falha comprovada vira `FALHOU`.
`send(request, retry_after=N)` solicita a próxima tentativa após a falha de
número N. Repetir essa solicitação não envia outra vez. O limite é de três
tentativas por destinatário, evento e canal. Preserve o mesmo identificador e
conteúdo em um reenvio. O Message-ID permanece estável entre tentativas.

Em uma interrupção de rede durante a entrega, o SMTP pode ter aceitado a
mensagem. O estado fica `INCERTO`, ou `ENVIANDO` se o processo parar antes
de persistir o resultado. Esses estados exigem verificar o sink antes de
qualquer nova emissão. O módulo não repete automaticamente uma entrega ambígua.

## Ensaio local com Mailpit

Use o [binário nativo do Mailpit](https://mailpit.axllent.org/docs/install/).
O ensaio foi executado com a versão 1.32.0. Mantenha o sink em loopback, com
endereços sintéticos e sem relay, forwarding ou webhook de saída. Em PowerShell:

```powershell
mailpit --smtp 127.0.0.1:1025 --listen 127.0.0.1:8025 --disable-version-check --ignore-duplicate-ids --smtp-allowed-recipients '@example\.test$'
```

O navegador acessa a caixa de teste em `http://127.0.0.1:8025`. As variáveis
de ambiente estão em `.env.example`. Para executar o ensaio explícito no
diretório `backend/`:

```powershell
$env:ACADEMIA_TEST_MAILPIT = '1'
uv run --locked pytest -m integration tests/notifications/test_smtp.py
```

O teste envia a mensagem por SMTP e consulta a API do Mailpit para conferir uma
única captura. Os testes de integração com PostgreSQL verificam separadamente os
estados de falha, o reenvio e a autorização da API.
