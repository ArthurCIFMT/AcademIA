# FND-05 — PostgreSQL de teste, ORM e migrations

## Metadados

- Fase: Fundação.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-04.
- Requisitos: RNF-03, RNF-07, RNF-10, RNF-16; RN-33.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar postgresql de teste, orm e migrations, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/database/**`
- `backend/tests/database/**`
- `database/**`
- `backend/pyproject.toml`
- `backend/*lock*`
- `.env.example`
- `AGENTS.md`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Configurar ORM/migrations aceitos e separar URLs de desenvolvimento e teste.
2. Criar migration técnica mínima; entidades de negócio entram nos prompts próprios.
3. Definir unidade de trabalho/transação e fixtures para PostgreSQL real sem Docker.

## Critérios de aceite

- Migration aplica em banco vazio e reaplicação não duplica estruturas.
- Rollback de teste não deixa cadastro parcial; a conexão de teste não usa banco de desenvolvimento.
- Evolução/reversão permitida é documentada sem apagar bancos compartilhados.

## Testes obrigatórios

DB; INT; DOC. Registrar comandos reais de banco/migration e fixtures de integração.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Criar todo o MER antecipadamente ou usar SQLite como comprovação de PostgreSQL.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
