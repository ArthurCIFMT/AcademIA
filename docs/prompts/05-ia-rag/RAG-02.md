# RAG-02 — Conexão ao banco vetorial especializado

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-04, FND-06, RAG-01, GATE-06.
- Requisitos: MRF01, MRF02; RN-39; RNF-05, RNF-08, RNF-10; MRF17 (infraestrutura da ferramenta).
- Módulos: MOD-05.

## Objetivo e contexto

Entregar conexão ao banco vetorial especializado, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.
Consulte o [fluxo agentivo](../../arquitetura/agentic-rag.md), a
[extensão de dados](../../arquitetura/modelo-de-dados/extensao-agentic-rag.md)
e o [conjunto de testes](../../testes/agentic-rag.md). Suíte significa conjunto
organizado de testes; sigla de teste não é comando pronto de terminal.

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

## Complementos obrigatórios para Agentic RAG

- Adapter vetorial recebe filtros/limites já validados pelo serviço de conhecimento;
  conexão/segredos e seleção de coleção não são argumentos livres do LLM.
- Retornar IDs, scores e metadados suficientes à validação da proveniência; a
  versão aprovada em MOD-05 continua autoridade mesmo com índice desatualizado.
- Testar filtro obrigatório contra remoção/alteração por payload e erro separado
  de resultado vazio. Manter integração com banco vetorial real, sem Docker antecipado.
- Não implementar planejador/loop LLM neste cartão: ele pertence a AI-02. Assim,
  o recuperador pode ser testado isoladamente e não cria dependência circular.

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
