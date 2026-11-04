# FIN-02 — Compra e confirmação por gateway

## Metadados

- Fase: Financeiro tardio.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FIN-01, NTF-01, GATE-09.
- Requisitos: RF-31; RN-22, RN-24, RN-35; RNF-17.
- Módulos: MOD-08.

## Objetivo e contexto

Entregar compra e confirmação por gateway, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/billing/payments/**`
- `backend/tests/billing/**`
- `frontend/src/features/checkout/**`
- `database/**`
- `.env.example`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Escolher gateway/sandbox e contrato antes de codificar; registrar política de validade/renovação/cancelamento.
2. Criar checkout e webhook autenticado com idempotência, tentativas e vínculo externo.
3. Registrar confirmação de pagamento validada pelo mesmo contrato de MEM-00;
   tratar falhas/eventos fora de ordem. Matrícula/renovação exige ação do atendente.

## Critérios de aceite

- Retorno visual do navegador não ativa matrícula por si.
- Webhook duplicado não duplica confirmação; assinatura inválida é rejeitada.
- Pagamento recusado/pendente não permite matrícula; confirmação válida habilita
  ação do atendente, mas não cria/renova matrícula nem libera acesso sozinha.

## Testes obrigatórios

BE; INT; API; FE; contrato e sandbox real documentados.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Cobrar dinheiro real nos testes ou armazenar dados completos de cartão.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
