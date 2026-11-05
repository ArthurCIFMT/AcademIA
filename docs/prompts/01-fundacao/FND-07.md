# FND-07 — Scaffold React, TypeScript e Vite

## Metadados

- Fase: Fundação.
- Estado de execução inicial: PRONTO — dependências documentais concluídas.
- Dependências: FND-02B.
- Requisitos: RNF-01, RNF-07, RNF-08, RNF-10, RNF-14.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar scaffold react, typescript e vite, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `frontend/**`
- `.env.example`
- `AGENTS.md`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar SPA com dependências fixadas, estrutura de features e cliente HTTP configurável.
2. Configurar componentes, tipos, lint e build; registrar comandos FE.
3. Documentar execução local e estados base de carregamento/erro.

## Critérios de aceite

- Instalação reproduzível inicia a SPA e build passa.
- URL da API vem da configuração e erro de rede apresenta estado controlado.
- Teste de componente verifica renderização e fallback de erro.

## Testes obrigatórios

FE; DOC, mais lint, tipos e build reais configurados nesta entrega.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Telas finais de domínio, autenticação simulada permanente e Docker.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
