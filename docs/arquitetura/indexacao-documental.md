# Indexação documental — RAG-04

MOD-05 transforma uma seleção técnica de literatura aprovada em fragmentos e
vetores persistentes. Entrega MRF01/MRF11/MRF15 e RNF-17; não chama LLM, decide
triagem ou implementa busca semântica. Recuperação/citações são RAG-05.

## Entrada e delimitação

O serviço Indexer recebe ExtractionResult CONCLUIDA, Selection e curador ativo
(administrador, conforme a política MANAGE_CORPUS). Reconsulta papéis e aprovação
vigente no PostgreSQL antes da preparação, dos lotes e da conclusão. Documento
TESTE ou versão revogada não pode ativar ingestão de literatura.

Selection é JSON estrito, schema_version=1, com finalidade aprovada no documento,
motivo_curadoria e trechos de parágrafos/tabelas selecionados. Seu
[JSON Schema](../requisitos/schemas/selecao-indexacao-v1.schema.json) integra a SPEC.
Cada trecho declara página física PDF (1-based) ou null para TXT, offsets inicio
inclusivo/fim exclusivo em caracteres do texto extraído, seção e tipo
PARAGRAFO/TABELA. Offsets não são bytes nem a numeração impressa do livro.
A seleção é feita sobre o artefato de extração, sem editar o PDF original.

Cabe ao curador selecionar conteúdo útil inteiro e conferir sua leitura. Não
promover bibliografia, rodapés, tabelas partidas ou colunas intercaladas apenas
porque o texto pôde ser extraído. O motivo e a seleção ficam na configuração
imutável da ingestão. Um conjunto concluído cobre essa seleção explícita, não
significa que todas as páginas do livro foram indexadas. Outra seleção/configuração
produz nova identidade e exige indexação completa independente.

## Fragmentação e proveniência

- Conteúdo: até 300 tokens do tokenizer E5. Entrada completa com título/seção,
  prefixo passage: e tokens especiais: até 512. Não há truncamento silencioso.
- Respeitar página, seção, parágrafo e tabela. Junção apenas de átomos contíguos
  separados por espaços/quebras; conservar texto, símbolos, unidades e negações.
- Sobreposição alvo 48 tokens, usando átomos inteiros: pode ser zero ou superar
  48 para não quebrar contexto, mantendo o teto de 300.
- Parágrafo/tabela indivisível acima do limite, origem inválida ou contexto de
  título excessivo deixa PENDENTE_TRATAMENTO, sem vetores ativos. Corrigir/revisar
  a seleção ou a extração; não descartar ressalvas para caber no limite.
- Payload versionado contém texto/hash, metadados bibliográficos, finalidade,
  versão/aprovação, ingestão/fragmento, configuração/espaço, página ou linhas TXT,
  offsets e seção. PG guarda os vínculos/checkpoints; texto/vetor ficam no Qdrant.

## Modelo local e dependências

E5-small multilíngue CPU, 384 dimensões normalizadas e cosseno; query: para
perguntas e passage: para documentos. Revisão fixa
614241f622f53c4eeff9890bdc4f31cfecc418b3. Os
[hashes e versões](../requisitos/schemas/embedding-e5-v1.json) permitem reprodução.

sentence-transformers 6.2.0 executa o modelo; torch 2.15.0 é a runtime CPU;
tokenizers conta a entrada sem truncamento; huggingface-hub 2.4.0 provisiona os
arquivos fixados. São dependências necessárias desta entrega; uv.lock fixa as
transitivas. Não se instala GPU, provedor pago, OCR ou LLM.
Fontes técnicas: [modelo E5](https://huggingface.co/intfloat/multilingual-e5-small),
[SentenceTransformer](https://sbert.net/docs/package_reference/sentence_transformer/model.html)
e [SDK Qdrant](https://github.com/qdrant/qdrant-client/tree/v1.20.0).

O provisionamento explícito baixa apenas uma lista de arquivos do commit fixado,
sem credencial, gera academia-model.json e verifica SHA-256. Na primeira carga o
encoder confere os arquivos contra o manifesto. Na inferência, arquivos são locais,
HF offline, trust_remote_code=False e pesos safetensors; não há download automático.
Modelo roda em subprocesso persistente, serializado, limitado a CPU e threads.
Timeout encerra o subprocesso; uma resposta tardia não publica conteúdo. Shutdown
libera worker e Qdrant. Importar a API não carrega pesos nem abre o índice.

## Persistência, retomada e ativação

Migration 0013 cria INGESTAO e FRAGMENTO, sem modificar migrations anteriores.
IDs UUID5 derivam da versão/configuração e ordem/hash do texto. A configuração
fixa extração/hash, seleção, modelo/revisão/espaço, coleção e limites. Unicidade
versão+config_hash e ingestão+ordem impede duplicação. Proveniência é imutável;
checkpoints e estados mudam controladamente, com revisão e auditoria.

1. Preparar plano completo no PG, adquirir lock por ingestão e validar espaço.
2. Conferir pontos existentes pelo ID, payload/hash, dimensão e normalização.
3. Gerar somente faltantes, fazer upsert e confirmar recibo no Qdrant.
4. Persistir checkpoint por fragmento; ativar CONCLUIDA somente com todos os
   pontos confirmados e versão ainda aprovada. Trigger confere contagem SQL.

Não há transação distribuída PG/Qdrant. Se o processo parar após gravar vetor e
antes do checkpoint, a retomada reconhece o ponto íntegro e evita novo embedding.
Replay completo não duplica pontos nem evento de conclusão. Vetor ausente/inválido
exige reparo dos faltantes; estado retorna PROCESSANDO até concluir.

Lotes padrão 8 (configurável 1–32), timeout 60 s por tentativa (máximo 180 s),
orçamento 180 s por lote e até 3 tentativas para erro transitório/rate limit,
com backoff 1/2 s. JSON/vetor inválido não abre loop de reparo. O modelo local
não depende de rate limit remoto; o contrato/teste mantém essa falha explícita.
Falha do Qdrant fica registrada, com retomada por ação explícita. Não reiniciar
orçamento do lote ao repetir transporte. Nenhuma transação SQL fica aberta
aguardando embeddings ou Qdrant.

Estados: PROCESSANDO, FALHA, CONCLUIDA, PENDENTE_TRATAMENTO e REVOGADA.
Falha/resultado parcial nunca é ativo. available_ingestions combina CONCLUIDA,
coleção/espaço, ambiente LITERATURA e revisão de aprovação atual no PG. Revogar
retira elegibilidade imediatamente, mesmo com vetores físicos ainda presentes;
RAG-05 deve usar esse gate, não confiar apenas no payload. Literatura nunca recebe
onboarding, biometria, inventário ou conversas privadas.

## Operação local

A partir de backend/, configurar .env conforme o exemplo, aplicar migration 0013
e parar a API antes de abrir o mesmo diretório Qdrant em uma CLI:

~~~powershell
uv sync --locked
uv run --locked --env-file ../.env python -m app.modules.knowledge.embeddings.provision
uv run --locked --env-file ../.env python -m app.modules.knowledge.ingestion --actor UUID_CURADOR --version UUID_VERSAO --selection CAMINHO_JSON
~~~

O primeiro comando de módulo precisa de internet apenas para obter os pesos.
O segundo requer banco configurado, versão aprovada e seleção técnica real;
responde JSON com identidade, estado/contagens/erro controlado. Só CONCLUIDA
retorna exit code 0. Caminhos relativos partem de backend/. Pesos, locks, extrações
e índice ficam ignorados pelo Git; não publicar esses diretórios.

Coleção padrão academia_rag_e5_v2 fixa a revisão. A v1 de RAG-02 sem revisão é
preservada; trocar revisão mantendo coleção incompatível falha, sem apagar dados.
Um worker por diretório local; não executar API e manutenção simultaneamente.

## Evidências e pendências

[Testes e comandos](../testes/comandos.md#indexação-e-embeddings-locais) incluem
falhas/retomada, crash entre vetor e checkpoint, imutabilidade SQL, migração de
ida/volta, Qdrant real, E5 CPU real e pipeline PG/Qdrant/E5 com texto sintético.
Teste com double não demonstra qualidade do modelo. O ensaio real comprova
indexação técnica, não pertinência ou latência de recuperação/chat.

O [relatório RAG-03](../testes/extracao-corpus-rag03.json) mantém quatro fontes
REVISAO_NECESSARIA: BR-MS-001, INT-BJSM-001, INT-SPMED-001 e BR-SBC-001.
Não foram promovidas por esta entrega. As três extrações concluídas ainda exigem
seleção de trechos úteis; não houve carga automática integral do acervo no banco
de desenvolvimento. Não existe avaliação semântica de RAG-05 ou ensaio LLM de AI-06.
