# UX-06 · Fichas e histórico no celular

**Meus treinos** mostra um dia por vez. A navegação por teclado leva o
foco ao dia escolhido e a troca mantém os valores da ficha publicada.
A leitura distingue carga zero de ausência, identifica equipamento
indisponível e mantém as observações e o motivo do parecer.

O histórico identifica a versão vigente e permite voltar a ela. Uma
versão removida fica indisponível para leitura e exportação. Nas
fichas de IA, as fontes podem ser consultadas pelo contrato existente
de contexto. O aviso de alteração das fontes fica separado do parecer.

## Verificações

- **Frontend.** 112 testes aprovados em 21 arquivos. Cobertura de dias,
  histórico, prescrição, autoria, pareceres,
  fontes, expurgo e download autenticado. Lint, TypeScript e build
  aprovados.
- **Edge com fixtures.** Ficha e ação de exportação verificadas a 320,
  390, 768 e 1440 CSS px com os dados sintéticos do verificador visual.
- **E2E.** Oito jornadas aprovadas no Edge 158.0.4370.33. E2E-01
  confirma parecer pendente e rejeitado e baixa o JSON. E2E-04 troca
  de dia pelo teclado sem novo pedido de ficha, testa o conteúdo a
  320 CSS px com texto normal e ampliado, a página a 390 CSS px com
  texto a 200% e consulta as fontes sem POST. E2E-05 seleciona uma
  versão histórica rejeitada e verifica que, após expirar, ela sai
  do seletor e perde a exportação. O retorno à ficha vigente devolve
  o foco ao título. O banco usado é `academia_test`. A IA é
  controlada e não consome quota externa.

| Captura | Evidência com dados sintéticos |
|---|---|
| Antes | [Ficha do MVP a 390 px](../interface/evidencias-ux01/antes/ficha-390.png) |
| Escolha do dia | [320 px](../interface/evidencias-ux06/dia-320.png) |
| Texto ampliado | [390 px com texto a 200%](../interface/evidencias-ux06/ampliacao-390.png) |
| Parecer rejeitado | [Ficha e motivo a 390 px](../interface/evidencias-ux06/rejeitada-390.png) |
| Expurgo | [Histórico e retorno à vigente a 390 px](../interface/evidencias-ux06/expirada-390.png) |

O iniciador permanece compatível com os serviços e comandos locais.

Na primeira rodada, a combinação de 320 CSS px e texto a 200% cortou
parte da marca no cabeçalho compartilhado. A verificação distingue o
conteúdo da ficha nessa configuração da página completa a 390 CSS px
com texto a 200%. O cabeçalho compartilhado entra na revisão geral
[UX-09](../prompts/11-experiencia-interface/UX-09.md).

## Reprodução

Em `frontend/`, executar `npm test -- --maxWorkers=2`, `npm run lint`,
`npm run typecheck` e `npm run build`. Para a navegação integrada,
usar o [runner E2E](aceitacao-mvp.md) com uma pasta de saída nova.
O [verificador visual](../interface/verificar-ux02.cjs) usa builds
e capturas em pastas novas para conferir as quatro larguras.
