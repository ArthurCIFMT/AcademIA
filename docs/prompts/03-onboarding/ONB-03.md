# ONB-03 — Formulário e consulta responsivos do onboarding

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ONB-01, ONB-02, IAM-04.
- Requisitos: RF-10, RF-11, RF-12, RF-13, RF-14; RN-05, RN-11; RNF-14.
- Módulos: MOD-03.

## Objetivo e contexto

Entregar formulário e consulta responsivos do onboarding, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `frontend/src/features/onboarding/**`
- `frontend/tests/onboarding/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar formulário pelo schema aprovado com validação e salvamento de rascunho.
2. Oferecer conclusão e consulta própria com dados retornados da API.
3. Tratar token inválido, expiração, rede e mensagens de erro sem perda silenciosa.

## Critérios de aceite

- Usuário preenche, salva, reabre e conclui em viewport móvel.
- Obrigatórios inválidos não concluem; erro de rede permite recuperar edição.
- Cliente não escolhe ID alheio para abrir onboarding.

## Testes obrigatórios

FE; API; roteiro navegador-backend com persistência.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Diagnóstico ou geração de treino na interface.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
