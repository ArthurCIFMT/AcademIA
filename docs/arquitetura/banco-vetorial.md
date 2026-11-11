# Banco vetorial — RAG-02 e RAG-04

MOD-05 usa qdrant-client 1.20.0 em modo local persistente, conforme ADR-004/005.
É o engine vetorial real da biblioteca, separado do PostgreSQL; não exige serviço
HTTP, contêiner, credencial ou chave de LLM no MVP. Requisitos: MRF01/MRF02,
RN-39 e RNF-05/08/10. Fontes oficiais da integração:
[cliente e modo local](https://github.com/qdrant/qdrant-client/tree/v1.20.0),
[coleções e metadados](https://github.com/qdrant/qdrant-client/blob/v1.20.0/qdrant_client/qdrant_client.py)
e [distribuição Python](https://pypi.org/project/qdrant-client/1.20.0/).

## Escopo entregue e porta

A porta interna VectorStore fornece check() → CollectionStatus e close().
QdrantStore implementa essa porta; tipos públicos não importam classes Qdrant.
O estado informa coleção, modelo/revisão, dimensão, métrica, fingerprint e contagem.
RAG-02 não criou rota REST ou tabela PostgreSQL. RAG-04 estende a porta
VectorIndex com present(payloads esperados) e upsert(points), sem expor tipos SDK;
a migration 0013 registra plano e checkpoints no PG. Não há busca pública nesta fase.
A composição do FastAPI fecha o recurso no shutdown; esse ponto fora da pasta
vector/ é necessário ao ciclo de vida da conexão previsto pelo cartão.

RAG-03 entregou extração e RAG-04 entregou [embeddings/indexação](indexacao-documental.md).
Payload versionado e seu checksum ligam cada vetor ao texto/hash e à versão,
configuração, finalidade, página/linhas e seção. present verifica esses vínculos,
dimensão e normalização; upsert é idempotente por ID. Nenhuma dessas operações
aprova a literatura. Recuperação e avaliação semântica são RAG-05.
Testes usam diretórios temporários; o ensaio E5 real não publica literatura
sintética no banco de desenvolvimento. Esta entrega não chama LLM.

## Configuração e identidade da coleção

Valores vêm de ambiente (padrões técnicos aceitos nos ADRs e no .env.example).
Caminho relativo é resolvido a partir do processo; o guia inicia em backend/.
Recomenda-se caminho absoluto local se o diretório de execução puder variar.

| Variável | Padrão/semântica |
|---|---|
| ACADEMIA_VECTOR_MODE | local; qualquer outro modo é recusado nesta fase |
| ACADEMIA_VECTOR_PATH | data/qdrant; persistente, específico, não :memory: nem raiz de unidade |
| ACADEMIA_VECTOR_COLLECTION | academia_rag_e5_v2; nome deve terminar em _vN |
| ACADEMIA_VECTOR_EMBEDDING_MODEL | intfloat/multilingual-e5-small |
| ACADEMIA_VECTOR_DIMENSION | 384 |
| ACADEMIA_VECTOR_MODEL_REVISION | 614241f622f53c4eeff9890bdc4f31cfecc418b3, igual ao encoder fixado |

Métrica cosseno, normalização e prefixos query:/passage: são parte do espaço
versionado, conforme a configuração canônica. Não mudar modelo/dimensão por
fallback. Alterações de configuração seguem o protocolo da SPEC e a decisão
aprovada; parâmetros futuros não significam autorização para trocar a arquitetura.
ACADEMIA_VECTOR_URL não é usada para abrir servidor: se informada, gera erro de
configuração. Modo servidor e migração/reindexação ficam para a infraestrutura final.

Cada coleção guarda nos próprios metadados um schema_version e o embedding_space:
modelo, revisão, dimensão, métrica, normalização e prefixos, mais SHA-256 da
serialização JSON canônica desse espaço. O schema da identidade é 1. A coleção _v1 foi criada para a conexão inicial
sem revisão; _v2 fixa os pesos reais. Configurações diferentes exigem nova coleção.

A abertura verifica tanto os parâmetros físicos (vetor denso único, dimensão,
cosseno, sem multivetor/esparso) quanto a identidade registrada. Coleção existente
sem metadados ou incompatível é recusada, inclusive se vazia. Não adotar vetores
por terem apenas a mesma dimensão. Não sobrescrever identidade, recriar coleção,
apagar pontos, reindexar ou trocar nome automaticamente para esconder conflito.

A v1 sem revisão permanece preservada. RAG-04 usa por padrão a v2 compatível
com a revisão real fixada; apontar a configuração nova para a v1 deve retornar
CONFIGURACAO_INCOMPATIVEL. Não apagar/recriar a coleção antiga para contornar a
verificação. Ingestão recusa revisão nula ou divergente do encoder. Ingestão
completa e proveniência continuam sendo condições adicionais ao uso.

## Ciclo de vida, concorrência e falhas

get_vector_store() mantém singleton por processo, protegido por lock. A instância
é criada sob demanda e só abre Qdrant na primeira operação check(). A importação
da aplicação e rotas manuais não abrem o índice nem validam sua configuração.
O engine mantém exclusão entre processos no diretório; usar um worker Uvicorn.
Não compartilhar esse diretório entre backend, ferramenta de manutenção ou outro
worker. Uma instância herdada de outro PID é recusada antes do acesso ao engine.

O adaptador serializa operações em RLock; o cliente é habilitado para chamadas
em threads distintas somente porque esse lock controla todo acesso interno.
No shutdown do FastAPI, close_vector_store() fecha a conexão e libera o diretório.
A CLI também fecha o recurso ao terminar. Após alterar variáveis, reinicie o
processo para não substituir a configuração de uma conexão já em uso.

| Código | Situação | Resultado |
|---|---|---|
| CONFIGURACAO_INVALIDA | Modo, URL, nome, dimensão ou revisão inválidos | Não abrir engine |
| CONFIGURACAO_INCOMPATIVEL | Coleção com espaço/parâmetros diferentes | Preservar coleção/pontos e interromper operação |
| SERVICO_INDISPONIVEL | Diretório ocupado/inacessível, erro do engine ou instância de outro processo | Falha técnica explícita; não retornar recuperação vazia ou fictícia |

A verificação de conexão não repete automaticamente operações. Nova ação explícita
pode tentar reconectar; não existe fallback para memória, PostgreSQL, outro modelo
ou coleções de teste. Erros públicos não incluem caminhos, segredos ou exceções
brutas do SDK. Falhas futuras de busca deverão manter a distinção entre ausência
de evidência e indisponibilidade. Rotas de treino manual continuam independentes.

## Execução e verificação local antes do Docker

Com a API parada, a partir de backend/ e com o ambiente do projeto configurado:

```powershell
uv sync --locked
uv run --locked --env-file ../.env python -m app.modules.knowledge.vector
```

O comando cria a coleção vazia se inexistente e confere a existente. Sucesso retorna
JSON status=OK com a configuração e points; falha retorna JSON status=ERRO,
code/message em português e exit code 1. JSON usa escapes ASCII, compatíveis com
UTF-8 e pipes do Windows. Não imprime caminho físico. Execute novamente depois
para comprovar reabertura; não apagar meta.json ou arquivos de lock manualmente.

Durante a API em execução, futuros consumidores internos usam a porta singleton;
a CLI em outro processo será recusada enquanto a mesma pasta estiver ocupada.
Para inspecionar simultaneamente sem interferir no acervo, configure diretório
exclusivo de teste em ACADEMIA_VECTOR_PATH. Diretórios padrão ficam fora do Git.
Variáveis de URL/chave de um servidor remoto não são necessárias neste MVP.

## Curadoria e próximos passos

A conexão não decide aprovação de corpus. RAG-04 combina a identidade
do espaço com [referências aprovadas e revalidação](corpus.md#integração-e-invalidação),
extração/indexação completa e proveniência. RAG-05 deve reusar esse gate.
Qdrant não é a autoridade de aprovação;
metadados vetoriais não desbloqueiam versão revogada nem documentos TESTE.
Não indexar onboarding, dados biométricos, inventário ou conversas como literatura.

A dependência qdrant-client é necessária para o engine real e traz nove pacotes
novos no lockfile, incluindo ela própria; versões preexistentes foram preservadas.
Esse registro se refere à entrega RAG-02; RAG-04 adiciona as dependências CPU
justificadas no [contrato de indexação](indexacao-documental.md). Não usar
fastembed ou outro modelo como fallback.
Testes e evidências estão no [registro de comandos](../testes/comandos.md#conexão-vetorial-local).
