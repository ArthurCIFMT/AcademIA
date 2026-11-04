# VAL-03 — Documentação e roteiro de demonstração acadêmica

## Metadados

- Fase: Entrega final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: VAL-02, INF-04.
- Requisitos: RNF-10, RNF-11; contexto acadêmico.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar documentação e roteiro de demonstração acadêmica, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `README.md`
- `docs/instalacao/**`
- `docs/demonstracao/**`
- `docs/arquitetura/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Preparar instalação, comandos, perfis sintéticos e roteiro de demonstração.
2. Explicar módulos, agentes, corpus, publicação/parecer posterior, API facial
   real e catraca fictícia, conforme escopo entregue e limitações conhecidas.
3. Referenciar modelo atual e histórico sem expor segredos ou dados reais.

## Critérios de aceite

- Roteiro reproduz cadastro até treino e chat antes do parecer, avaliação posterior
  e caso bloqueado; extensão de acesso demonstra matrícula sem pagamento e biometria real.
- README aponta comandos reais e fontes de documentação atualizadas.
- Limitações e módulos adiados estão explícitos e coerentes com a matriz.

## Testes obrigatórios

DOC; execução manual do roteiro no ambiente validado.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Publicar credenciais de uso real ou apresentar módulo planejado como concluído.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
