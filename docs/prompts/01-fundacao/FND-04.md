# FND-04 — Scaffold do backend Python

## Metadados

- Fase: Fundação.
- Estado de execução inicial: PRONTO — dependências documentais concluídas.
- Dependências: FND-03, GATE-01, GATE-03, GATE-06.
- Requisitos: RNF-02, RNF-04, RNF-07, RNF-08, RNF-10.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar scaffold do backend python, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/**`
- `.env.example`
- `AGENTS.md`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar projeto Python no framework aceito e estrutura modular mínima, com configuração por ambiente.
2. Configurar runner de testes, lint e tipos adotados; registrar comandos BE no guia e em AGENTS.md.
3. Expor healthcheck mínimo e documentar inicialização local.

## Critérios de aceite

- Instalação em ambiente isolado reproduz dependências fixadas e API inicia pelo comando documentado.
- Healthcheck retorna resposta contratada; configuração obrigatória ausente falha de forma compreensível.
- Um teste mínimo verifica a resposta e lint/tipos configurados passam.

## Testes obrigatórios

BE; DOC. Esta entrega configura BE e registra comando real antes de declarar sucesso.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Entidades de negócio, login, Docker e integração de IA.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
