# ACS-03 — Motor de autorização de entrada

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ACS-02, MEM-01.
- Requisitos: RF-21; RN-06, RN-07, RN-24, RN-35, RN-36.
- Módulos: MOD-07, MOD-08.

## Objetivo e contexto

Entregar motor de autorização de entrada, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/authorization/**`
- `backend/app/contracts/memberships/**`
- `backend/tests/access/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Aplicar identidade, conta, matrícula, validade, modalidade e limite por contrato.
2. Definir semântica de evento: tentativa/decisão é distinta de passagem confirmada pela catraca.
3. Retornar código de decisão e registrar regra/instante utilizados.

## Critérios de aceite

- Sem matrícula/vencida, modalidade incompatível ou limite excedido nega entrada.
- Reconhecimento válido sozinho não permite acesso.
- Concorrência não ultrapassa limite; recusa e falha externa não contam presença.

## Testes obrigatórios

BE com tabela de decisão e relógio; INT; API com casos limite.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Aplicar bloqueio financeiro não configurado ou calcular frequência de tentativa negada.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
