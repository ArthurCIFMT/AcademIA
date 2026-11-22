# UX-01 · Evidência da referência visual

Aplicativo de origem: commit `026ec35`. A linha de base usa o build da
SPA atual com respostas HTTP sintéticas e uma faixa de identificação
acrescentada durante a captura. A segunda coluna de cada largura usa o
[protótipo local](../interface/prototipo/index.html), com dados fixos e
navegação por fragmentos. Ambas as capturas foram feitas no Microsoft Edge
com viewport de 390 × 844 ou 1440 × 1000 CSS px e página inteira.
As rotas, perfis, versão do navegador e medidas estão no
[registro da execução](../interface/evidencias-ux01/resultado.json).

| Cena | MVP 390 | Protótipo 390 | MVP 1440 | Protótipo 1440 |
|---|---|---|---|---|
| Entrada | [MVP](../interface/evidencias-ux01/antes/entrada-390.png) | [Proposta](../interface/evidencias-ux01/prototipo/entrada-390.png) | [MVP](../interface/evidencias-ux01/antes/entrada-1440.png) | [Proposta](../interface/evidencias-ux01/prototipo/entrada-1440.png) |
| Onboarding | [MVP](../interface/evidencias-ux01/antes/onboarding-390.png) | [Proposta](../interface/evidencias-ux01/prototipo/onboarding-390.png) | [MVP](../interface/evidencias-ux01/antes/onboarding-1440.png) | [Proposta](../interface/evidencias-ux01/prototipo/onboarding-1440.png) |
| Dúvida sem evidência | [MVP](../interface/evidencias-ux01/antes/duvida-390.png) | [Proposta](../interface/evidencias-ux01/prototipo/duvida-390.png) | [MVP](../interface/evidencias-ux01/antes/duvida-1440.png) | [Proposta](../interface/evidencias-ux01/prototipo/duvida-1440.png) |
| Geração com quota atingida | [MVP](../interface/evidencias-ux01/antes/quota-390.png) | [Proposta](../interface/evidencias-ux01/prototipo/quota-390.png) | [MVP](../interface/evidencias-ux01/antes/quota-1440.png) | [Proposta](../interface/evidencias-ux01/prototipo/quota-1440.png) |
| Ficha vigente | [MVP](../interface/evidencias-ux01/antes/ficha-390.png) | [Proposta](../interface/evidencias-ux01/prototipo/ficha-390.png) | [MVP](../interface/evidencias-ux01/antes/ficha-1440.png) | [Proposta](../interface/evidencias-ux01/prototipo/ficha-1440.png) |
| Parecer do instrutor | [MVP](../interface/evidencias-ux01/antes/parecer-390.png) | [Proposta](../interface/evidencias-ux01/prototipo/parecer-390.png) | [MVP](../interface/evidencias-ux01/antes/parecer-1440.png) | [Proposta](../interface/evidencias-ux01/prototipo/parecer-1440.png) |
| Cadastro administrativo | [MVP](../interface/evidencias-ux01/antes/cadastro-390.png) | [Proposta](../interface/evidencias-ux01/prototipo/cadastro-390.png) | [MVP](../interface/evidencias-ux01/antes/cadastro-1440.png) | [Proposta](../interface/evidencias-ux01/prototipo/cadastro-1440.png) |

As sete cenas geraram 28 capturas. A inspeção de layout verificou as 38
vistas navegáveis do protótipo em 320, 390, 768 e 1440 CSS px: largura do
documento dentro do viewport e botões principais com pelo menos 44 px de
altura. A 390 px, Tab e Enter acionaram o salto ao conteúdo, abriram o menu,
seguiram para o assistente e deixaram foco no título com o menu recolhido.
Também foram conferidos o seletor de área, a navegação de convite fora do
menu autenticado e a ampliação de texto a 200% na etapa de dados físicos
do convite. As vistas são HTML de demonstração, por isso os testes dessas
transições não comprovam autorização, persistência ou chamadas ao modelo.

A luminância relativa das cores do CSS computado produziu **13,47:1**
para texto normal, **5,93:1** para o secundário e **8,45:1** para botão
principal. Os estados medidos ficam entre 7,19:1 e 8,28:1. A borda dos
campos obteve 4,32:1 e o anel de foco, 6,12:1 ou mais nas superfícies
verificadas. São medições dos pares escolhidos para o protótipo.

## Reprodução

Com Node 24, dependências já instaladas no frontend e Microsoft Edge:

```powershell
# Em frontend/, use um diretório de build descartável.
$env:VITE_API_BASE_URL = '/api'
$env:VITE_CORPUS_MAINTENANCE_ENABLED = 'false'
npm exec --no -- vite build --outDir ../backend/data/ux01-dist
# Na raiz, informe uma pasta de capturas ainda inexistente.
node docs/interface/verificar-ux01.cjs backend/data/ux01-dist backend/data/ux01-rodada-N
python scripts/gerar_spec.py --check
python scripts/verificar_documentacao.py
git diff --check
```

O [executor local](../interface/verificar-ux01.cjs) usa Playwright existente,
servidor de arquivos limitado ao loopback e fixtures em memória. O
navegador bloqueia conexões externas. Durante a preparação, o antivírus
deste Windows tentou injetar uma URL de script. O pedido foi bloqueado
sem mexer no antivírus e a captura foi repetida com política de conteúdo
local. PostgreSQL, API real, iniciador, Mailpit e LLM ficaram fora da
execução. A comparação visual da aplicação redesenhada e a regressão
integrada pertencem às entregas que mudarem o frontend e a UX-09.
