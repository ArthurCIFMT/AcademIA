# RAG-03 — Extração PDF e TXT com proveniência

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-04, RAG-01.
- Requisitos: MRF01, MRF11, MRF15; MRF18 (apoio à leitura contextual).
- Módulos: MOD-05.

## Objetivo e contexto

Entregar extração pdf e txt com proveniência, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.
Consulte o [fluxo agentivo](../../arquitetura/agentic-rag.md), a
[extensão de dados](../../arquitetura/modelo-de-dados/extensao-agentic-rag.md)
e o [conjunto de testes](../../testes/agentic-rag.md). Suíte significa conjunto
organizado de testes; sigla de teste não é comando pronto de terminal.

## Escopo permitido

- `backend/app/modules/knowledge/ingestion/**`
- `backend/tests/knowledge/fixtures/**`
- `backend/tests/knowledge/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Extrair texto preservando página/seção, unidades, símbolos e origem.
2. Tratar arquivo corrompido, tamanho/tipo inválido e PDF sem camada textual.
3. Para PDF escaneado, registrar necessidade de OCR; só adicionar OCR se previsto no corpus aceito.

## Critérios de aceite

- Fixture PDF/TXT mantém símbolos como >=, <=, % e unidades relevantes.
- Mesmo documento não gera extrações duplicadas sem nova versão.
- Falha registra motivo e não publica conteúdo vazio como sucesso.

## Complementos obrigatórios para Agentic RAG

- Preservar relações entre tabelas, cabeçalhos, células, unidades e notas; manter
  recomendação, grau de certeza e ressalvas ligadas à localização correspondente.
- Identificar problemas de ordem de leitura, duas colunas e texto rotacionado;
  não ativar extração que inverta significado nem remover símbolos genericamente.
- Guardar referências de página/seção/vizinhança para a ferramenta contextual de
  RAG-05. Uma página de abertura com pouco texto não é automaticamente falha/OCR.
- Testar AR-04 com fixture conferida: fórmula e exceção devem ser recuperáveis
  juntas; conteúdo documental malicioso continua sendo dado, não instrução.

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
