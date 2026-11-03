# FND-08 — Auditoria e eventos duráveis mínimos

## Metadados

- Fase: Fundação.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, FND-06.
- Requisitos: RN-23, RN-26, RN-27, RN-32, RN-33; RNF-06, RNF-15, RNF-17.
- Módulos: MOD-00, MOD-12.

## Objetivo e contexto

Entregar auditoria e eventos duráveis mínimos, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/audit/**`
- `backend/app/events/**`
- `backend/tests/audit/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Persistir evento com ator, ação, recurso, correlação e instante sem copiar conteúdo médico.
2. Expor porta para publicação/consumo de evento JSON versionado e reprocessamento idempotente.
3. Se efeito externo exigir garantia transacional, criar outbox mínima sem broker obrigatório.

## Critérios de aceite

- Evento e transação de origem ficam consistentes em sucesso e rollback.
- Mesmo identificador reprocessado não duplica efeito auditável.
- Usuário comum não exclui evidência própria; payload não expõe segredos.

## Testes obrigatórios

BE; INT; DB; API quando houver rota administrativa.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Mensageria distribuída, ferramentas comerciais de auditoria e regras de módulos futuros.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
