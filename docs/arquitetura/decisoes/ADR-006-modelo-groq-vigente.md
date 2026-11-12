# ADR-006 — Migração explícita do modelo Groq

Status: ACEITA por autorização expressa do responsável em 2026-11-11.
Escopo adicional ao AI-06: migrar para GPT-OSS 120B e repetir a avaliação.

O ensaio autenticado retornou 404/model_not_found para o modelo anterior.
A Groq [documenta sua retirada dos planos gratuito/developer](https://console.groq.com/docs/deprecations)
em 2026-08-16. A chave foi validada sem ser publicada. Não há fallback oculto.

Modelo vigente: openai/gpt-oss-120b na Groq, uso do plano gratuito já solicitado,
configuração [v2](../../requisitos/schemas/configuracao-ia-v2.json).
A [v1](../../requisitos/schemas/configuracao-ia-v1.json) é histórica; não é carregada
pelo runtime. Seus hashes/commits anteriores continuam reproduzíveis.
E5/Qdrant/corpus, fronteiras, etapas e bloqueios não mudam.

JSON Object Mode continua com validação backend. reasoning_effort=low;
include_reasoning=false. Sem ferramentas, browser, SQL, pesquisa ou novos agentes.
[Parâmetros do provedor](https://console.groq.com/docs/reasoning) e
[modelo](https://console.groq.com/docs/model/openai/gpt-oss-120b).
Limites anteriores de contexto/chamadas/tempo permanecem até evidência justificar
nova decisão; tokens de raciocínio podem consumir a cota mesmo sem serem retornados.
Não registrar raciocínio interno nem considerar JSON válido prova de fundamentação.

O ensaio usou o proxy de saída configurado neste ambiente após uma falha de
transporte. Isso não prova que todo ambiente exija proxy. ACADEMIA_LLM_PROXY_URL
é opcional, somente ambiente confiável, oculta na representação e fora de Git.
Não herdar proxy arbitrário de requisição/usuário ou trocar o host do modelo.
TLS continua validado, redirects desabilitados e retries de transporte LLM=0.
Configuração local do proxy não é serviço pago alternativo.

A aprovação do modelo/configuração não aprova qualidade, latência ou segurança
semântica. Esses critérios continuam sujeitos ao AI-06 e TST-01.
