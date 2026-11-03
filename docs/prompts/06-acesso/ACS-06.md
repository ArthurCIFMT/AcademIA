# ACS-06 — Interfaces de acesso, frequência e lotação

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ACS-05, IAM-04.
- Requisitos: RF-23, RF-25; RN-04, RN-05, RN-28, RN-34; RNF-14.
- Módulos: MOD-07.

## Objetivo e contexto

Entregar interfaces de acesso, frequência e lotação, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/queries/**`
- `backend/tests/access/**`
- `frontend/src/features/attendance/**`
- `frontend/src/features/occupancy/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Expor consulta agregada de lotação e histórico autorizado.
2. Criar tela móvel de lotação e tela de frequência por contexto.
3. Tratar atualização por nova consulta e ausência de eventos.

## Critérios de aceite

- Nova consulta reflete entrada/saída confirmada.
- Cliente não consulta frequência de terceiro.
- Lotação agregada não expõe identidade ou biometria das pessoas presentes.

## Testes obrigatórios

API; INT; FE e roteiro de evento até a tela.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Streaming obrigatório ou exibir fotos de quem está na academia.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
