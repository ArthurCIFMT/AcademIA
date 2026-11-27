# 03 — Meu perfil e endereço

## Tarefa

Entregar uma página autenticada de perfil para cliente, atendente, instrutor e administrador, com dados cadastrais próprios e endereço opcional editável pelo titular.

## Escopo permitido

- Nova feature em `frontend/src/features/profile/` e integração de rota/menu em `frontend/src/app/`.
- Serviço, DTOs e rota de perfil próprio em `backend/app/modules/people/` e composição em `backend/app/main.py`.
- Migration nova em `database/migrations/versions/`, modelo lógico, dicionário, requisitos e contratos afetados. Testes do perfil e navegação correspondente.

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

BE do DTO e autorização, INT com PostgreSQL de teste, contrato OpenAPI, FE do formulário e E2E com dois usuários e papéis acumulados. Verificar migration com contas já existentes. Rodar suites relacionadas, lint, tipos, build e DOC/SPEC conforme o projeto. Avance em 04. O cartão 08 depende do aceite deste cartão.
