# ADR-004 — RAG semântico, modelos e corpus

Status: ACEITA
Data: 2026-11-04
Origem: responsável delegou a seleção de frameworks, campos e regras técnicas;
academia única foi escolhida expressamente. Escolhas registradas sem exigir nova aprovação.

Decisão: Qdrant especializado por qdrant-client em modo local persistente no MVP,
sem servidor/Docker inicial; um singleton por processo e diretório local ignorado.
Não é mock nem PostgreSQL vetorial. Consultas/buscas por porta do módulo knowledge.
Na fase Docker, modo servidor Qdrant com testes de contrato e reindexação; não
compartilhar arquivo local entre vários processos. Configurar modo/path/url por ambiente.

Embeddings locais: intfloat/multilingual-e5-small, sentence-transformers, CPU,
384 dimensões normalizadas, cosseno. Prefixos query: e passage:. Baixar pesos só
na implementação RAG-04; registrar revisão exata do modelo e configuração.
Chunks de até 300 tokens do tokenizer E5, sobreposição alvo 48; incluir prefixo e
contexto de título no teto 512 do modelo. Respeitar página/seção, tabelas e ressalvas;
não cortar negação/unidade para satisfazer tamanho. Tabela indivisível excessiva
fica pendente de tratamento, sem truncamento silencioso.
Busca top-K=5, teto 8, deduplicação por fragmento/versão; mínimo cosseno inicial
0,80 como filtro experimental, nunca prova de suporte. Pacote deve ter evidência
pertinente identificada. Sem reranker ou reescritor LLM obrigatório.

LLM: API Groq, modelo inicial llama-3.3-70b-versatile, plano gratuito do titular,
chave GROQ_API_KEY em ambiente. Adaptador HTTPX, endpoint configurável. Modo
json_object + Pydantic/JSON Schema no backend: JSON válido não garante o schema.
Sem chave/quota, estado SERVICO_INDISPONIVEL; não simular sucesso. Não cadastrar
cartão, contratar plano ou trocar para provedor pago automaticamente. Mudança do
modelo é configuração/decisão registrada, não fallback oculto.
Qwen/Ollama não são obrigatórios: alternativa futura se hardware/ensaio justificar.

Conhecimento inicial é o corpus já reunido, não um livro inventado: seleção técnica
delegada registrada em materiais/rag/corpus-inicial.json e no catálogo. Documentos
aprovados para ingestão ainda passam por extração/proveniência e delimitação do
conteúdo útil; referências bibliográficas, instruções maliciosas e conteúdo fora
do escopo não se tornam recomendações. PDFs originais não são modificados.
Sem suporte para uma adaptação de saúde, abster-se e manter vigente.
Semântica e orquestrador fixo; nenhuma pesquisa agentiva/loop de reparo.
Limites e ensaios em [configuração IA](../../requisitos/configuracao-ia-rag.md).

Fontes: [Qdrant local](https://github.com/qdrant/qdrant-client#local-mode),
[E5](https://huggingface.co/intfloat/multilingual-e5-small),
[modelo Groq](https://console.groq.com/docs/model/llama-3.3-70b-versatile),
[limites](https://console.groq.com/docs/rate-limits),
[JSON](https://console.groq.com/docs/structured-outputs).
São escolhas técnicas; velocidade e qualidade não foram ensaiadas nesta entrega.
