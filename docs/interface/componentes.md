# UX-02 · Base visual e componentes

A interface usa [tokens CSS](../../frontend/src/styles/tokens.css) derivados
da [referência UX-01](README.md). Fundo, texto, paleta, tipografia, escala,
raios, larguras e foco têm uma fonte no frontend. Regras de apresentação
dos componentes ficam em [ui.css](../../frontend/src/styles/ui.css).

O CSS global já aplica tipografia, cores de fundo, links, foco, botões e a
largura máxima dos controles ao aplicativo. As páginas continuam na
estrutura estreita de 48 rem do MVP. O limite de 72 rem está disponível para
o futuro layout por perfil. Seções, navegação, regras de formulário e
envio de dados continuam sob responsabilidade de cada fluxo.

## Uso nos próximos cartões

Importe os componentes de [ui/primitives](../../frontend/src/ui/primitives.tsx).

| Peça | Uso e contrato |
|---|---|
| `Button` | Ação principal, secundária ou destrutiva. O padrão é `type="button"`. Especifique `type="submit"` em formulários. Passe `pending` e um rótulo de progresso ligado ao estado real da operação. Em andamento, o botão é desabilitado e recebe `aria-busy`. |
| `FormField` | Entrega ao controle o ID, a classe, o atributo obrigatório e os vínculos com ajuda e erro. Use um único controle por campo e aplique os atributos recebidos. Em um envio inválido, o formulário decide para onde mover o foco. |
| `StatusMessage` | Use `empty` para uma lista vazia, `loading` durante uma consulta, `success` para resultado confirmado, `conflict` para versão superada e `error` para falha. O título descreve o estado, e o complemento sugere a ação disponível. Conflito e falha usam alerta, carregamento e sucesso usam região de status. |
| `Card` | Agrupa conteúdo com título semântico. Use cabeçalho de página acima dos painéis e mantenha as ações relacionadas junto ao seu conteúdo. |
| `ResponsiveTable` | Recebe cabeçalhos e linhas de uma tabela com legenda. Em uma largura insuficiente para colunas que precisam ser comparadas, a rolagem fica na região nomeada e focável. Use cartões/listas quando a relação entre linhas e colunas for dispensável. |
| `NavigationDisclosure` | Abre e fecha pelo controle nativo. Escape fecha e devolve o foco ao resumo. A rota ativa, a autorização e a troca entre áreas pertencem à navegação de UX-03. |

```tsx
<FormField label="E-mail" required error={emailError}>
  {control => <input {...control} name="email" type="email" autoComplete="email" />}
</FormField>
<Button type="submit" pending={saving} pendingLabel="Salvando…">Salvar</Button>
```

Use `.ac-ui` em uma área que recebe componentes fora da estrutura da
aplicação, para compartilhar a mesma indicação de foco. O
[mostruário React](../../frontend/src/ui/preview/index.html) é uma entrada
de desenvolvimento separada da aplicação. Ele ilustra a validação de um
campo, os estados, a rolagem da tabela e a abertura do menu por toque e
teclado. Para reproduzir a inspeção e o build do mostruário, veja
[os comandos do UX-02](../testes/ux02-base-visual.md).

Duplicidade de envio, ciclo de sessão e permissão continuam sujeitos aos
controles dos fluxos e do backend. Um menu recolhido ou botão desabilitado
serve à interação. Nenhum fluxo dos próximos cartões exige modal nesta
etapa. A avaliação de um diálogo nativo pode acompanhar a primeira
necessidade concreta desse componente.
