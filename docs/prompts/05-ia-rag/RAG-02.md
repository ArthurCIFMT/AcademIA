# RAG-02 — Conexão ao banco vetorial especializado

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-04, FND-06, RAG-01, GATE-06.
- Requisitos: MRF01, MRF02; RNF-05, RNF-08, RNF-10.
- Módulos: MOD-05.

## Objetivo e contexto

Entregar conexão ao banco vetorial especializado, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/knowledge/vector/**`
- `backend/tests/knowledge/**`
- `.env.example`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar porta e adapter do banco vetorial aceito, inicialmente recomendado Qdrant.
2. Definir coleção, dimensão, modelo de embeddings e métrica cosseno por versão.
3. Documentar serviço local/remoto de teste antes do Docker e sua verificação de conexão.

## Critérios de aceite

- Coleção tem dimensão/métrica esperadas e dados persistem após nova conexão.
- Dimensão ou modelo incompatível retorna erro controlado sem misturar vetores.
- Serviço indisponível não causa fallback silencioso para recuperação falsa.

## Testes obrigatórios

BE com double; INT com banco vetorial real; API se exposto.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Docker Compose, troca silenciosa de banco ou dados pessoais indexados.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
