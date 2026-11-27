# 02 — Navegação por papel

## Tarefa

Reduzir cliques entre tarefas, manter a área autenticada e fazer o destino ativo e o retorno previsíveis no desktop e celular.

## Escopo permitido

- `frontend/src/app/{AppRoutes.tsx,areaNavigation.ts,Frames.tsx,frames.css}`.
- Componentes de navegação diretamente usados pelas áreas e adaptação de rota do catálogo em `frontend/src/features/equipment/`, se necessária.
- `frontend/tests/auth/session.test.tsx`, testes de navegação e partes afetadas em `frontend/tests/e2e/{mvp,access}.spec.ts`.
- `docs/interface/navegacao-e-acesso.md`, requisitos de interface, testes e fontes do SPEC diretamente afetados.

Preserve as regras de autorização no backend, a sessão e os módulos de negócio. API de perfil e dados cadastrais pertencem ao cartão 03.

## Contexto e execução

Depende de 01. Leia UX-03, UX-09, RNF-14/19/20 e a documentação de navegação. Use a área atual para abrir uma tarefa sem voltar a um seletor. Para acesso inicial, use um destino útil por papel. Use **Painel** para administrador, **Clientes** para atendente, **Meus clientes** para instrutor e **Meus treinos** para cliente, com estado vazio utilizável. Quem tem vários papéis troca de área no cabeçalho e vai à tarefa principal da área escolhida. Preserve a rota direta e as permissões efetivas.

Mantenha navegação direta no desktop e atalhos para as tarefas mais usadas no celular. Preserve a moldura da conta no catálogo autenticado e a rota pública do visitante. Conserve seção ativa, foco, teclado e Voltar. Integre o link funcional de Meu perfil no cartão 03.

## Critérios de aceite

- De uma tarefa a outra no mesmo papel, um clique direto no desktop ou abrir o menu e escolher no celular. Sem tela de escolhas intermediária. Atalhos móveis permitem trocar entre as tarefas destacadas diretamente.
- Conta com um papel vai à tarefa inicial. Conta com papéis acumulados muda para uma área permitida sem misturar menus. Acesso por URL, recarga e retorno preservam a rota adequada.
- O visitante mantém o catálogo público. O cliente navega pelo catálogo autenticado com o menu da área. Logout e perda de permissão preservam as guardas e o retorno seguro.

## Testes e entrega

FE da sessão/navegação e E2E das jornadas afetadas, com teclado, viewport móvel e desktop. Rodar lint, tipos e build do frontend conforme `docs/testes/comandos.md`. Registrar divergências de cliques e resultados por papel. Próximo 03.
