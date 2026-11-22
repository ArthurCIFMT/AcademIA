# UX-02 · Verificação da base visual

A entrega aplicou os tokens globais ao frontend e adicionou os
[componentes compartilhados](../interface/componentes.md). O build padrão
continua com a SPA como entrada. O mostruário usa outra entrada, própria
para a inspeção dos componentes.

## Resultado

- **Frontend:** 103 testes aprovados em 21 arquivos, incluindo cinco casos
  novos de submissão, ação pendente, associação de erro ao campo,
  semântica de tabela/avisos e devolução de foco. Lint, tipos e build passaram.
- **Edge 158.0.4370.33:** login, onboarding, dúvida, quota, ficha, revisão,
  cadastro administrativo e cadastro pelo atendente abriram a 320, 390,
  768 e 1440 CSS px. Ações principais permaneceram disponíveis com pelo menos
  44 × 44 CSS px. O formulário de cadastro foi aberto nas duas áreas e
  conferido nas quatro larguras. Nenhuma das páginas inspecionadas exigiu
  rolagem horizontal do documento.
- **Componentes no Edge:** validação e correção de e-mail, foco no campo
  inválido, abertura do menu por teclado e toque, Escape com retorno de
  foco e rolagem horizontal interna da tabela por teclado a 320 px.
  A ampliação de texto a 200% foi conferida no mostruário a 390 px.
  O primeiro ensaio encontrou largura excedente na tabela. O ajuste de
  dimensionamento foi verificado novamente em todas as larguras.
- **Contraste:** pares medidos no CSS computado. Texto principal 13,47:1,
  secundário 5,93:1, botões 8,45:1, borda de campo 4,32:1 e foco 6,61:1
  sobre o fundo da página. Sucesso, conflito e erro ficaram entre 7,19:1
  e 8,28:1. O [registro completo](../interface/evidencias-ux02/resultado.json)
  contém as dez medições e o roteiro observado.

| Captura | Evidência no navegador |
|---|---|
| Mostruário React | [320 px](../interface/evidencias-ux02/componentes-320.png) · [1440 px](../interface/evidencias-ux02/componentes-1440.png) |
| Login da SPA | [390 px](../interface/evidencias-ux02/entrada-390.png) |
| Onboarding da SPA | [390 px](../interface/evidencias-ux02/onboarding-390.png) |
| Cadastro da SPA | [390 px](../interface/evidencias-ux02/cadastro-390.png) |
| Revisão do instrutor na SPA | [1440 px](../interface/evidencias-ux02/parecer-1440.png) |

As capturas e interações usaram o código React construído e dados sintéticos.
O cenário móvel foi emulado no Edge. A inspeção de tela e semântica no
navegador complementa a validação UX-09 e não substitui testes com leitores
ou dispositivos físicos. A tabela bidimensional foi exercitada no mostruário,
pois o MVP exibe esses dados em listas.

## Reprodução

Em `frontend/`, com Node e dependências existentes:

```powershell
npm test -- --maxWorkers=2
npm run lint
npm run typecheck
npm run build
```

Na raiz, com Edge disponível e dois diretórios de saída novos:

```powershell
node docs/interface/verificar-ux02.cjs backend/data/ux02-build-N backend/data/ux02-rodada-N
python scripts/gerar_spec.py --check
python scripts/verificar_documentacao.py
git diff --check
```

O executor reaproveita as fixtures de UX-01 e serve o build em loopback.
HTTP do aplicativo é interceptado, as conexões externas são bloqueadas e
o mostruário funciona com estado local. A entrega não afeta serviços,
portas, healthchecks, dependências ou o iniciador. PostgreSQL, Mailpit,
API real e LLM não foram necessários para essa verificação.
