# VAL-01 — Rastreabilidade e escopo final

## Metadados

- Fase: Entrega final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: PG-02.
- Requisitos: RF-01–RF-35; RN-01–RN-36; RNF-01–RNF-17; MRF01–MRF15 conforme aceite.
- Módulos: MOD-00–MOD-12.

## Objetivo e contexto

Entregar rastreabilidade e escopo final, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `docs/arquitetura/rastreabilidade.md`
- `docs/requisitos/**`
- `docs/prompts/README.md`
- `docs/testes/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Relacionar requisito a implementação, prompt, teste/evidência e estado.
2. Registrar pendente/dispensado sem omitir requisito original.
3. Conferir que texto, MER, modelo lógico e migrations correspondem à entrega.

## Critérios de aceite

- Todo requisito selecionado tem evidência ou justificativa de não execução.
- Itens opcionais/derivados têm decisão rastreável.
- Nenhuma tarefa é marcada concluída somente por existir arquivo de prompt.

## Testes obrigatórios

DOC; conferência de evidências reais e links.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Executar funcionalidades faltantes como parte da auditoria documental.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
