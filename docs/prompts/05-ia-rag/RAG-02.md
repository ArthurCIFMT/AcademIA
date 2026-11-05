# RAG-02 — Conexão ao banco vetorial especializado

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-04, FND-06, RAG-01, GATE-06.
- Requisitos: MRF01, MRF02; RN-39; RNF-05, RNF-08, RNF-10.
- Módulos: MOD-05.

## Referências de arquitetura

[Fluxo semântico](../../arquitetura/rag-semantico.md),
[dados](../../arquitetura/modelo-de-dados/dados-rag-ia.md) e
[testes](../../testes/rag-ia-semantico.md).

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

1. Implementar porta e adapter Qdrant local persistente, um singleton por processo,
   conforme ADR-004. Caminho ignorado no Git; testes usam diretório separado.
   Sem servidor/Docker inicial, sem compartilhar diretório entre processos.
2. Definir coleção, dimensão, modelo de embeddings e métrica cosseno por versão.
3. Documentar serviço local/remoto de teste antes do Docker e sua verificação de conexão.

## Finalidades e limites

Expor recuperação para dúvidas, triagem do resumo e geração de ficha, por
contratos de MOD-05; este módulo não implementa LLM/planner nem decide aptidão.
Aprovação é por versão; revogação invalida novo uso/cache, mesmo antes da remoção
vetorial. Livro/literatura dependem de curadoria; inventário e clientes não são
indexados como literatura compartilhada. Não enviar documento inteiro por pedido.

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

## Idioma e configuração da recuperação

Selecionar configuração de embeddings/recuperação capaz de avaliar consultas em
português contra fontes PT/EN, mantendo modelo, dimensão e espaço vetorial
compatíveis. Isso não escolhe fornecedor nem fecha GATE-04. Preferir português
na curadoria; não traduzir/regravar PDFs como parte da conexão ao banco.
