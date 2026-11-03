# NTF-01 — Notificações e adaptador de e-mail

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-08, IAM-02.
- Requisitos: RF-09, RF-35; RN-23, RN-26, RN-27; RNF-09, RNF-17.
- Módulos: MOD-12.

## Objetivo e contexto

Entregar notificações e adaptador de e-mail, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/notifications/**`
- `backend/tests/notifications/**`
- `frontend/src/features/notifications/**`
- `database/**`
- `.env.example`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar aviso interno persistente, lista de pendências e estados de envio de e-mail.
2. Definir destinatários por tipo com responsável: instrutor designado para proposta, administrador para alterações críticas.
3. Implementar adapter de SMTP/API e reenvio limitado/idempotente em sink local.

## Critérios de aceite

- Falha externa registra falha e não apaga aviso/pedido pendente.
- Reprocessar evento não duplica a notificação.
- Somente destinatário autorizado consulta seu aviso; payload não revela anamnese.

## Testes obrigatórios

BE; INT; API; FE; integração com sink de teste.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Entregar e-mail a pessoas reais ou introduzir Docker nesta fase.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
