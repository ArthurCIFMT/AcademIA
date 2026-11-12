# ADR-009 — Gemini API como candidato explícito de reserva

Status: ACEITA quanto à integração por solicitação do responsável em 2026-11-12.
A qualificação de qualidade/tempo continua dependente do AI-06 do próprio modelo.

O responsável forneceu credencial Gemini para avaliar uma reserva independente
da quota Groq. A chave foi validada por listagem autenticada de modelos e salva
apenas no .env local ignorado pelo Git. Não contratar cobrança, plano pago,
batch/flex, busca Google ou outra ferramenta. Não copiar a chave para o frontend.

Escolher o ID fixo gemini-3.5-flash-lite: retornado pela conta, com
[entrada/saída no nível gratuito](https://ai.google.dev/gemini-api/docs/pricing#gemini-3.5-flash-lite)
e [saída estruturada](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite).
Não usar aliases latest, preview ou redirecionamento de modelos antigos.
Os modelos 2.5 possuem restrições para novos projetos; não pressupor acesso por
aparecerem na listagem. Preço comercial publicado não autoriza ativar faturamento.

Integrar a API REST nativa generateContent por HTTPX já instalado. O adaptador
recebe as mesmas duas mensagens do prompt versionado e monta systemInstruction
mais um conteúdo user. responseMimeType=application/json, candidateCount=1,
thinkingLevel=minimal/includeThoughts=false; validar o conteúdo pelo schema do
backend. Não solicitar ferramentas, cachedContent, URL context ou grounding.
Metadados de raciocínio não são conteúdo público nem artefato de avaliação.

Usar [perfil reserva-gemini](../../requisitos/schemas/configuracao-ia-reserva-gemini-v2.json)
por ACADEMIA_LLM_PROFILE explícito. Principal permanece 120B. Configuração valida
provider/modelo/host/esforço em conjunto; perfil não aceita URL ou modelo arbitrário.
GEMINI_API_KEY nunca é substituída por GROQ_API_KEY. A fábrica escolhe um adaptador
por configuração, sem fallback ou nova chamada após falha.

Endpoint Google é HTTPS fixo, credencial em cabeçalho x-goog-api-key, sem query de
segredo. Redirects e proxies herdados do ambiente HTTP são desabilitados. Proxy de
saída usa apenas a configuração local confiável já existente. Reutilizar o slot
síncrono de uma chamada, limites de bytes/timeout/contexto e uma tentativa por
etapa. Resposta com modelo divergente, código, ferramenta, raciocínio, truncamento
ou consumo incoerente não é entregue ao domínio. Contabilizar tokens de resposta
mais pensamentos no total de saída; não esconder o custo de raciocínio mínimo.

Credenciais dos dois provedores são removidas dos relatórios e do processo de
testes do frontend. O E2E com IA controlada também remove ambas as chaves. Dados
reais de clientes não participam dos ensaios. Um teste mínimo de conexão confirma
apenas acesso/JSON, não adequação de fichas ou aprovação de corpus.

Identidade de AI-06 passa a incluir adaptadores, fábrica, configuração e composição
de geração. Relatórios de antes dessa integração permanecem históricos; seus hashes
não podem ser unidos à nova execução. Cada modelo precisa de amostra completa,
revisão semântica vinculada e ensaio determinístico próprio. Não mudar metas para
aprovar um modelo nem escolher resultados melhores entre provedores.

Quota, segurança e qualidade reais estão em [avaliação Gemini](../../testes/ai06-gemini.md).
Serviço nativo e parâmetros: [generateContent](https://ai.google.dev/api/generate-content),
[pensamento](https://ai.google.dev/gemini-api/docs/thinking) e
[limites](https://ai.google.dev/gemini-api/docs/rate-limits). A API não comprova fatura
ou plano financeiro da conta; registrar tokens, sem alegar custo monetário medido.
