# MEM-00 — Confirmação manual de pagamento antes da matrícula

## Metadados

- Fase: Pós-MVP / base do acesso.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, PES-02, IAM-04, GATE-08.
- Requisitos: RF-26 parcialmente, RF-31; RN-04, RN-27, RN-33.
- Módulos: MOD-08.

## Objetivo e contexto

Entregar confirmação manual de pagamento antes da matrícula, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte requisitos citados, modelo lógico, ADRs aceitos e os
[fluxos atualizados](../../arquitetura/fluxos-atualizados.md).
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/billing/payments/**`
- `backend/tests/billing/**`
- `frontend/src/features/payment-confirmation/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Registrar confirmação manual de pagamento com cliente, valor, data, método,
   referência/comprovante e funcionário responsável, sem checkout nem gateway.
2. Definir estados e correções auditáveis; preservar confirmação anterior e impedir
   que simples declaração do cliente seja tratada como confirmação operacional.
3. Expor contrato para MEM-01 verificar confirmação elegível do cliente e evitar
   reaproveitamento incompatível; a forma exata é fechada em GATE-08.
4. Preparar o mesmo contrato para confirmação externa futura em FIN-02.

## Critérios de aceite

- Funcionário com permissão registra confirmação; cliente e funcionário sem permissão são recusados.
- Confirmação consulta-se após recarga e não cria nem ativa matrícula sozinha.
- Pendente, recusado ou confirmação de outro cliente não satisfaz MEM-01.
- Repetição/correção não duplica crédito nem apaga autoria/histórico.
- Dados fictícios bastam para o ensaio; não movimentar dinheiro real.

## Testes obrigatórios

BE; INT; API; FE; DB, com duplicidade, autorização e vínculo incorreto.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Checkout, gateway, conciliação completa e criar matrícula automaticamente.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
