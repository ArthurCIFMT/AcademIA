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
   Cada compra referencia cliente/plano ativo/valor contratado; materializar plano_id
   em pagamento conforme o modelo lógico, sem perder histórico ao editar/inativar plano.
3. Registrar confirmação validada pelos contratos financeiros; compatibilizar com
   MEM-00 somente se implementado. Tratar falhas/eventos fora de ordem; matrícula
   continua ação independente do atendente, sem pagamento obrigatório.

## Critérios de aceite

- Cobrir CA-31.7–CA-31.9: compra própria de plano ativo, confirmação confiável,
  callback repetido/fora de ordem e matrícula posterior por atendente. Plano
  inativo não origina checkout e compra não permite acesso antes da matrícula.

- Retorno visual do navegador não ativa matrícula por si.
- Webhook duplicado não duplica confirmação; assinatura inválida é rejeitada.
- Pagamento recusado/pendente não é registrado como confirmado, mas não impede
  matrícula/renovação manual nem invalida matrícula vigente no escopo acadêmico.
- Gateway indisponível não bloqueia a ação do atendente; confirmação válida
  atualiza financeiro sem criar/renovar matrícula ou liberar acesso sozinha.

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
