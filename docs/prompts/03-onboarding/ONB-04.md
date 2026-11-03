# ONB-04 — Avaliação profissional e acesso por designação

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ONB-02, PES-03, IAM-04.
- Requisitos: RF-12, RF-14, RF-34; RN-11, RN-21, RN-31, RN-33; MRF03, MRF12.
- Módulos: MOD-02, MOD-03.

## Objetivo e contexto

Entregar avaliação profissional e acesso por designação, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/onboarding/**`
- `backend/tests/onboarding/**`
- `frontend/src/features/assessments/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar consulta e registro de avaliação pelo instrutor designado.
2. Registrar responsável, data e histórico; expor snapshot autorizado ao módulo de IA.
3. Aplicar troca de designação sem conceder acesso ao antigo responsável indevidamente.

## Critérios de aceite

- Instrutor designado consulta/avalia; atendente sem necessidade funcional é recusado.
- Avaliações sucessivas mantêm ordem e autoria.
- Contexto de IA para cliente A jamais contém avaliação de B.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Inventar dados vitais ou assumir medições não coletadas.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
