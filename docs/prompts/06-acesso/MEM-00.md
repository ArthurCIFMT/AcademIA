# MEM-00 — Registro manual opcional de pagamento

## Metadados

- Fase: Financeiro tardio / capacidade opcional.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: MEM-01, IAM-04.
- Requisitos: RF-26 parcialmente; RN-04, RN-27, RN-33.
- Módulos: MOD-08.

## Objetivo e contexto

Entregar registro manual opcional de pagamento na fase financeira tardia.
Este cartão não é pré-condição de matrícula nem de acesso acadêmico. O ID/caminho
foi preservado para manter referências; a fase e o manifesto definem sua ordem.
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
3. Expor consulta financeira autorizada e impedir duplicidade de registro; não
   exigir consulta desse contrato para matricular ou autorizar acesso acadêmico.
4. Compatibilizar com os contratos financeiros de FIN-01/FIN-02 quando existirem,
   sem obrigar a executar este cartão para implementar a integração por gateway.

## Critérios de aceite

- Funcionário com permissão registra confirmação; cliente e funcionário sem permissão são recusados.
- Confirmação consulta-se após recarga e não cria nem ativa matrícula sozinha.
- Confirmação pertence ao cliente correto; estado financeiro não bloqueia matrícula
  nem invalida matrícula vigente. MEM-01 funciona sem este cartão.
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
