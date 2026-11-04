# RAG-03 — Extração PDF e TXT com proveniência

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-04, RAG-01.
- Requisitos: MRF01, MRF11, MRF15.
- Módulos: MOD-05.

## Referências de arquitetura

[Fluxo semântico](../../arquitetura/rag-semantico.md),
[dados](../../arquitetura/modelo-de-dados/dados-rag-ia.md) e
[testes](../../testes/rag-ia-semantico.md).

## Objetivo e contexto

Entregar extração pdf e txt com proveniência, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/knowledge/ingestion/**`
- `backend/tests/knowledge/fixtures/**`
- `backend/tests/knowledge/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Extrair texto preservando página/seção, unidades, símbolos e origem.
2. Tratar arquivo corrompido, tamanho/tipo inválido e PDF sem camada textual.
3. Para PDF escaneado, registrar necessidade de OCR; só adicionar OCR se previsto no corpus aceito.

## Finalidades e limites

Expor recuperação para dúvidas, triagem do resumo e geração de ficha, por
contratos de MOD-05; este módulo não implementa LLM/planner nem decide aptidão.
Aprovação é por versão; revogação invalida novo uso/cache, mesmo antes da remoção
vetorial. Livro/literatura dependem de curadoria; inventário e clientes não são
indexados como literatura compartilhada. Não enviar documento inteiro por pedido.

## Critérios de aceite

- Fixture PDF/TXT mantém símbolos como >=, <=, % e unidades relevantes.
- Mesmo documento não gera extrações duplicadas sem nova versão.
- Falha registra motivo e não publica conteúdo vazio como sucesso.

## Testes obrigatórios

BE; INT; fixtures pequenas com expectativas textuais conferidas.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Remover genericamente caracteres especiais ou declarar PDF escaneado processado sem OCR.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
