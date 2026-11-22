# UX-08 · Cadastros, catálogos e operação administrativa

Clientes, funcionários, designações, equipamentos e exercícios passaram
a usar cartões, avisos e paginação com os padrões visuais do AcademIA.
Os formulários agrupam dados cadastrais, papéis, estado do perfil,
imagem e recursos conforme a operação. A pesquisa usa os filtros já
disponíveis no servidor. A entrega mantém as permissões por papel.

## Verificações

- **Frontend.** 116 testes aprovados em 21 arquivos. O catálogo preserva
  identificação e descrição quando a foto está ausente ou indisponível.
  Lint, TypeScript e build aprovados.
- **Inspeção visual.** Treze rotas no Edge 158.0.4370.33 a 320, 390, 768
  e 1440 CSS px. A verificação abre os formulários administrativos e de
  atendimento e confere a largura da página e os alvos das ações.
- **Fluxos no navegador.** Oito jornadas aprovadas, com reversão do banco
  confirmada. E2E-01 percorre a validação de cargo, a busca
  de cliente por e-mail, a mensagem de falha do convite e seu reenvio.
  O estado de falha é controlado somente na resposta apresentada à
  SPA. O cadastro e o reenvio passam pela API do teste e pelo Mailpit.
  E2E-06 usa a segunda página do inventário e verifica a retirada de
  um equipamento indisponível do catálogo público e da seleção de
  exercícios. E2E-08 inativa um perfil de cliente pela interface e
  confirma que o papel de atendente continua autorizado.
- **Backend.** Duas integrações com PostgreSQL de teste confirmam o
  registro da falha de convite, o reenvio e a invalidação do link anterior.
  O transporte de e-mail desses dois casos é controlado.

| Captura | Evidência com dados sintéticos |
|---|---|
| Antes | [Cadastro original a 390 px](../interface/evidencias-ux02/cadastro-390.png) |
| Clientes | [Resultado da busca a 390 px](../interface/evidencias-ux08/clientes-390.png) |
| Funcionários | [Cadastro salvo com falha de convite a 390 px](../interface/evidencias-ux08/convite-390.png) |
| Equipamentos | [Segunda página do inventário a 390 px](../interface/evidencias-ux08/inventario-390.png) |
| Exercícios | [Alternativa indisponível a 1280 px](../interface/evidencias-ux08/exercicios-1280.png) |

O backend continua em Python/FastAPI. O iniciador é compatível com
os serviços, portas e comandos locais usados nesta entrega.

## Reprodução

Em `frontend/`, executar `npm test -- --maxWorkers=2`, `npm run lint`,
`npm run typecheck` e `npm run build`. Usar o
[runner E2E](aceitacao-mvp.md) com uma pasta de saída nova e o
[verificador visual](../interface/verificar-ux02.cjs) para conferir
cadastros administrativos e atendimento nas quatro larguras.

Os testes `test_failed_invite_can_be_reissued_and_old_link_is_revoked`
e `test_failed_invite_can_be_reissued_with_new_token` ficam em
`backend/tests/people/` e usam o ambiente de integração documentado.
