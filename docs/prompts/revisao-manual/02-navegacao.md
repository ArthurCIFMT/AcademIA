# 02 — Navegação por papel

**Estado da entrega: CONCLUÍDO.** Navegação corrigida e jornadas de sessão e navegação aprovadas.

Ao reusar o cartão, execute primeiro a verificação focal. A correção fica limitada aos caminhos abaixo e depende de uma regressão reproduzida.

## Tarefa

Reduzir cliques entre tarefas, manter a área autenticada e fazer o destino ativo e o retorno previsíveis no desktop e celular.

## Escopo permitido

- `frontend/src/app/{AppRoutes.tsx,areaNavigation.ts,Frames.tsx,frames.css}`.
- `frontend/src/ui/primitives.tsx` apenas para foco ou comportamento do menu compartilhado, se demonstrado, e `frontend/src/features/equipment/EquipmentPages.tsx` apenas para a rota do catálogo.
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

Em `frontend/`:

```powershell
npm test -- tests/auth/session.test.tsx src/features/equipment/EquipmentPages.test.tsx
```

O teste de sessão deve passar para acesso por URL, troca de papel, catálogo autenticado, logout e perda de acesso. No runner de Edge do README, confira E2E-08 para conta com dois papéis, recarga e teclado, e E2E-06 para o catálogo público. Confira os demais destinos iniciais com contas sintéticas dos quatro papéis. Registre o destino inicial, o estado do item ativo e a quantidade de cliques até a tarefa no desktop e no celular. Se corrigir a interface, rode também `npm run lint`, `npm run typecheck` e `npm run build`.
