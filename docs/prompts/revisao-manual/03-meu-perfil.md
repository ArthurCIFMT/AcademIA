# 03 — Meu perfil e endereço

**Estado da entrega: CONCLUÍDO.** Perfil próprio e endereço entregues. O endereço opcional é definido na migration `0028`.

Ao reusar o cartão, execute primeiro a verificação focal. A correção fica limitada aos caminhos abaixo e depende de uma regressão reproduzida.

## Tarefa

Entregar uma página autenticada de perfil para cliente, atendente, instrutor e administrador, com dados cadastrais próprios e endereço opcional editável pelo titular.

## Escopo permitido

- Nova feature em `frontend/src/features/profile/` e integração da rota e do link de perfil em `frontend/src/app/{AppRoutes.tsx,Frames.tsx}`.
- Serviço, DTOs e rota em `backend/app/modules/people/own_profile.py`. Em `backend/app/main.py`, apenas o registro dessa rota. Em `backend/app/modules/identity/models.py`, apenas o campo `endereco`.
- Se uma regressão demonstrar necessidade de ajuste de schema, use uma migration nova e atualize o modelo lógico, o dicionário e o contrato de perfil. Use a `0028_own_profile_address.py` para conferência histórica e preserve seu conteúdo.
- `backend/tests/people/test_clients.py`, `frontend/tests/auth/session.test.tsx` e o caso de perfil no E2E-08.

Mantenha a API de sessão, os papéis, a recuperação de senha e a edição administrativa atual. Foto pertence ao cartão 08. O endereço não entra em cadastros administrativos, relatórios, onboarding ou IA.

## Contexto e execução

Depende de 01 e 02. Leia ADR-002, RF-04/05, RN-01/04/05 e a documentação de pessoas. Exiba no cabeçalho o link funcional **Meu perfil**. Mostre nome, e-mail e os campos já existentes que se apliquem a cada papel. Mostre dados cadastrais existentes em leitura. Defina no contrato o conjunto de campos de endereço antes de implementá-lo. Use validação e preserve a opção de deixar o endereço em branco.

Use uma única associação à identidade `USUARIO`. Mudar de papel mantém o mesmo endereço. Use um contrato autenticado de perfil próprio, por exemplo `GET /api/v1/meu-perfil` e `PATCH /api/v1/meu-perfil/endereco`. Obtenha o titular da sessão. A escrita aceita só os campos de endereço e segue CSRF, origem e autorização usados no projeto. Retorno pessoal usa política de cache privada conforme o contrato vigente.

## Critérios de aceite

- Os quatro papéis abrem a própria tela. Contas com papéis acumulados mantêm um único perfil de endereço.
- O titular consegue cadastrar, revisar, corrigir e limpar o endereço. A edição persiste após recarga e novo login. Usuário antigo abre o perfil com estado vazio apropriado.
- A API recusa sessão ausente/inativa e tentativa de agir em nome de outro usuário. A condição vale também para administradores. Requisição de endereço não altera e-mail, papéis ou dados de terceiros.
- Modelo, migration e documentação refletem o dado novo. As consultas administrativas e a IA preservam seu escopo.

## Testes e entrega

Em `backend/` com PostgreSQL isolado e em `frontend/`, respectivamente:

```powershell
uv run --locked pytest -o addopts='' tests/people/test_clients.py::test_own_address_is_optional_and_private
npm test -- tests/auth/session.test.tsx
```

Confira a tentativa de edição pelo titular, omissão do endereço e rejeição do identificador ou campo extra no DTO. No Edge, use E2E-08 para salvar, recarregar e trocar de papel. No checklist visual, abra **Meu perfil** com os quatro papéis e verifique que uma conta sem endereço carrega normalmente. A rotina do Alembic no cartão 10 comprova o schema. Para defeito específico de compatibilidade, verifique uma conta sintética criada antes da `0028` em banco de teste.
