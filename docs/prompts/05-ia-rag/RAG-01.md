# RAG-01 — Corpus, versões e aprovação documental

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-03, FND-05, IAM-03, GATE-04, IAM-04.
- Requisitos: MRF01, MRF11, MRF15; RN-23, RN-28.
- Módulos: MOD-05.

## Referências de arquitetura

[Fluxo semântico](../../arquitetura/rag-semantico.md),
[dados](../../arquitetura/modelo-de-dados/dados-rag-ia.md) e
[testes](../../testes/rag-ia-semantico.md).

## Objetivo e contexto

Entregar corpus, versões e aprovação documental, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/knowledge/**`
- `backend/tests/knowledge/**`
- `frontend/src/features/corpus/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Registrar documento, fonte, hash, versão, estado, origem e responsável pela aprovação.
2. Criar fluxo de quarentena/publicação e tela de manutenção autorizada.
3. Separar documentos de teste e corpus aprovado; guardar páginas/seções para citação.

## Finalidades e limites

Expor recuperação para dúvidas, triagem do resumo e geração de ficha, por
contratos de MOD-05; este módulo não implementa LLM/planner nem decide aptidão.
Aprovação é por versão; revogação invalida novo uso/cache, mesmo antes da remoção
vetorial. Livro/literatura dependem de curadoria; inventário e clientes não são
indexados como literatura compartilhada. Não enviar documento inteiro por pedido.

## Critérios de aceite

- Documento novo não participa da busca antes de aprovado.
- Arquivo repetido é reconhecido por hash; nova edição cria versão rastreável.
- Revogar versão impede novas recuperações sem apagar referências históricas.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Inventar literatura validada ou aceitar aprovação sem responsável.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
