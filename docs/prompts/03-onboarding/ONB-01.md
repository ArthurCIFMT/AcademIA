# ONB-01 — Convite e acesso por link seguro

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ONB-02, NTF-01.
- Requisitos: RF-09, RF-10; RN-05, RN-23; RNF-09, RNF-17.
- Módulos: MOD-03, MOD-12.

## Objetivo e contexto

Entregar convite e acesso por link seguro, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/onboarding/**`
- `backend/tests/onboarding/**`
- `backend/app/modules/notifications/templates/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar convite com token aleatório armazenado por hash, escopo de cliente e expiração.
2. Definir consumo/troca por sessão restrita sem impedir salvar/reabrir formulário editável.
3. Enviar link por adapter; reenvio segue política explícita de invalidação.

## Critérios de aceite

- Token válido acessa somente onboarding vinculado.
- Token inválido/expirado/revogado é recusado; sessão restrita não abre APIs administrativas.
- Falha de envio persiste e não marca onboarding concluído.

## Testes obrigatórios

BE; INT; API; integração com sink de e-mail.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Permitir token em logs ou link universal para qualquer cliente.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
