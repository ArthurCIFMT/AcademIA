# RAG-01 — Corpus, versões e aprovação documental

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-03, FND-05, IAM-03, GATE-04, IAM-04.
- Requisitos: MRF01, MRF11, MRF15; RN-23, RN-28; MRF17, MRF19 (apoio à aprovação e revogação).
- Módulos: MOD-05.

## Objetivo e contexto

Entregar corpus, versões e aprovação documental, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.
Consulte o [fluxo agentivo](../../arquitetura/agentic-rag.md), a
[extensão de dados](../../arquitetura/modelo-de-dados/extensao-agentic-rag.md)
e o [conjunto de testes](../../testes/agentic-rag.md). Suíte significa conjunto
organizado de testes; sigla de teste não é comando pronto de terminal.

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

## Critérios de aceite

- Documento novo não participa da busca antes de aprovado.
- Arquivo repetido é reconhecido por hash; nova edição cria versão rastreável.
- Revogar versão impede novas recuperações sem apagar referências históricas.

## Complementos obrigatórios para Agentic RAG

- Manter aprovação/revisão da versão documental como autoridade relacional, sem
  atribuir ao agente permissão de curadoria. Originais e histórico permanecem.
- Expor por contrato a validação de vigência/revisão de documentos e trechos para
  RAG-05 e publicação de AI-03; não permitir leitura de versão revogada por ID antigo.
- Revogação invalida uso ativo/cache e resultados obtidos anteriormente; remoção
  vetorial eventualmente pendente não torna uma fonte revogada utilizável.
- Critérios adicionais: AR-16 impede publicação após revogação entre busca e
  publicação; tentativa do agente de aprovar fonte é negada. Testar revisão da
  aprovação e falha parcial entre metadados e índice sem apagar proveniência.
- Persistência fica limitada a conhecimento/ingestão de MOD-05; execução privada
  do cliente pertence a AI-03/MOD-06. Não criar segundo mecanismo de publicação.

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
