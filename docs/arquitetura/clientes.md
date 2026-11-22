# Cadastro e manutenção de clientes

PES-02 monta as rotas no ponto de composição `backend/app/main.py` e liga
a tela às áreas administrativa e de atendimento em `frontend/src/app/AppRoutes.tsx`.
O módulo reutiliza o cliente HTTP da SPA e a tela pública de primeiro acesso.
Os serviços de convite de PES-01 e PES-02 ficam em `backend/app/modules/people/`
e usam as portas de identidade e notificações. A alteração de PES-01 se limita
a essa extração e mantém o contrato de funcionários.

## API e dados cadastrais

| Rota | Operação |
|---|---|
| GET /api/v1/clientes | Lista paginada. `busca` filtra parte do nome ou e-mail e ignora diferenças de maiúsculas. `pagina` começa em 1, com 20 resultados por padrão e máximo de 100. |
| GET /api/v1/clientes/{user_id} | Consulta o cadastro, o estado da conta e do perfil e a entrega do último convite. |
| POST /api/v1/clientes | Cria o cadastro e devolve 201. `vincular_existente` permite anexar o perfil à conta de funcionário identificada pelo e-mail. |
| PUT /api/v1/clientes/{user_id} | Atualiza nome, nascimento, telefone, CPF e estado do perfil. Exige a `revisao` da consulta. |
| POST /api/v1/clientes/{user_id}/convite | Emite outro convite de primeiro acesso. Exige conta convidada, perfil ativo e a `revisao` da consulta. |

Administrador e atendente ativos acessam as rotas. O backend verifica
permissões da sessão e exige origem e CSRF nas mutações. Nome, e-mail e
data de nascimento são obrigatórios. No cadastro e na atualização, a data civil
de referência é a de São Paulo. A interface e a API rejeitam nascimento futuro
ou idade de 100 anos completos ou mais. A tela informa data inválida quando
necessário, sem lembrete permanente sobre idade. O telefone é opcional. O e-mail é o
identificador da conta e permanece fixo na edição cadastral deste módulo.
A listagem e o detalhe retornam `idade` em anos completos, calculada a cada
consulta pela data civil de São Paulo. A idade muda no aniversário, sem gravação
periódica e sem mudar a revisão do cadastro. A data de nascimento fica no detalhe.
A operação de vínculo exige indicação explícita, conta ativa ou convidada,
perfil de funcionário existente e ausência de perfil de cliente. A criação
normal recusa e-mail em uso em qualquer estado de conta. Duplicidade e
revisão desatualizada retornam 409.

O CPF é opcional e aceita onze dígitos ou a forma pontuada. A API verifica
os dígitos e normaliza o valor para onze caracteres numéricos, incluindo zeros
à esquerda. Valor inválido retorna 422. A unicidade vale inclusive para perfis
inativos, e duplicidade retorna 409 sem criar conta ou emitir convite.
Uma atualização que omite `cpf` preserva o valor. Enviar `null` ou vazio
remove o valor cadastrado. O campo aparece em respostas de detalhe e mutação
destas rotas, com acesso administrativo ou de atendimento e `Cache-Control:
no-store`. Listagem, busca, autenticação, onboarding, IA, e-mails e auditoria
ficam fora desse tratamento.

O cadastro usa as tabelas da revisão 0003, com CPF em `cliente` desde a
revisão 0017. Conta, perfil e papel são escritos
na mesma transação com auditoria. A inativação muda somente o perfil cliente,
preserva histórico e mantém as permissões de eventual perfil de funcionário
ativo. A elegibilidade para acesso físico pertence aos módulos de matrícula e
biometria. O cadastro pode ser iniciado antes da matrícula, foto e onboarding.

## Primeiro acesso

A UX-08 organiza resultados por nome, idade, e-mail e situação do perfil.
A busca mantém o filtro ao paginar. Na edição, dados cadastrais, conta e
convite aparecem em áreas próprias. **Convite de primeiro acesso** mostra
o estado retornado pelo servidor e orienta como consultar o Mailpit. As
telas administrativas usam dados cadastrais. O onboarding profissional
continua acessível pelo fluxo de designação.

Uma conta nova recebe o mesmo fluxo de credencial já usado para funcionários.
Ao vincular uma conta ativa, a pessoa mantém a credencial que já possui.
O envio ocorre após o commit e o resultado aparece no cadastro. Falha
de entrega preserva a conta convidada. O reenvio invalida o link anterior
e permite até três emissões por identidade em 24 horas, compartilhadas com
o cadastro de funcionários. O backend armazena apenas o hash do token e o
convite usa o [Mailpit local](notificacoes.md#ensaio-local-com-mailpit).

O convite de credencial abre `/primeiro-acesso` e expira em 24 horas.
O backend exige a finalidade `PRIMEIRO_ACESSO` para definir a senha.
O convite de onboarding pertence a ONB-01 e tem finalidade e sessão próprias.
