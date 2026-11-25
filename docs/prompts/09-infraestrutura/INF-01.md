# INF-01 — Pré-requisitos e build para instalação local

## Metadados

- Fase: Infraestrutura final.
- Estado de execução: consulte o manifesto.
- Dependências: PG-01, PG-03.
- Requisitos: RNF-10, RNF-11; RNF-08.
- Módulos: MOD-00.

## Objetivo e contexto

Verificar instalação e build locais com os lockfiles já adotados.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `docs/instalacao/**`
- Guias de testes e escopo transversal do iniciador conforme contrato comum.

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Conferir instruções para Python/uv, Node/npm, PostgreSQL e Mailpit.
2. Verificar build frontend e inicialização do backend usando os lockfiles.
3. Conferir arquivos de configuração de exemplo e dados locais ignorados pelo Git.
4. Executar e registrar comandos INF de build e smoke nesta entrega;
   INF-04 amplia a verificação integrada sem ser pré-condição dos testes daqui.

## Critérios de aceite

- Build frontend e smoke backend passam com dependências instaladas localmente.
- O guia identifica migrations, dados de exemplo e corpus como preparo explícito.
- O iniciador continua compatível com os pré-requisitos documentados.

## Testes obrigatórios

INF: build e smoke locais; suites afetadas; DOC.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Containerização do AcademIA ou alteração do CompreFace local.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
