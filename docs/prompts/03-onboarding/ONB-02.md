# ONB-02 — Persistência do onboarding e avaliações versionadas

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: PES-02, FND-05.
- Requisitos: RF-11, RF-12, RF-13, RF-14; RN-11, RN-21, RN-32, RN-33; MRF03.
- Módulos: MOD-03.

## Objetivo e contexto

Entregar persistência do onboarding e avaliações versionadas, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Pré-condição de domínio

Antes de implementar, registrar esquema de onboarding aprovado: campos, tipos,
unidades, obrigatoriedade, validações e origem declarada/medida. Sua ausência
bloqueia a parte afetada, sem exigir fechar provedores ou todo GATE-04. Não inventar
questionário clínico. O checklist da revisão documental identifica essa pendência.

## Escopo permitido

- `backend/app/modules/onboarding/**`
- `backend/tests/onboarding/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar schema aprovado de dados físicos, queixas, medicações e condições.
2. Salvar rascunho e concluir atomicamente, registrando data, versão e responsável.
3. Expor consulta própria e snapshot versionado para futuras gerações.

## Critérios de aceite

- Campo obrigatório ausente impede conclusão mas permite rascunho autorizado.
- Reabrir rascunho recupera valores; conclusão registra instante.
- Atualização posterior não muda snapshot já usado por ficha.

## Testes obrigatórios

BE; INT; API; DB com dados sintéticos.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Inventar questionário clínico completo ou decisões de elegibilidade.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
