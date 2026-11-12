# ADR-008 — Modelo de reserva explícito para avaliação

Status: ACEITA quanto ao mecanismo por solicitação do responsável em 2026-11-12.
A qualificação do modelo de reserva depende de seu próprio AI-06.

O responsável autorizou retomar AI-06 e avaliar outras LLMs gratuitas se necessário.
A Groq voltou a recusar o GPT-OSS 120B por tokens diários, mesmo com tokens por
minuto disponíveis. Trocar de chave na mesma organização não resolve esse limite.

Preparar o candidato openai/gpt-oss-20b na mesma Groq, reutilizando a credencial
já configurada, sem nova dependência ou conta. A documentação oficial apresenta
[JSON Object Mode](https://console.groq.com/docs/model/openai/gpt-oss-20b) e
[limites gratuitos por modelo/organização](https://console.groq.com/docs/rate-limits).
Disponibilidade e quota efetiva não são garantidas. Os preços comerciais da
página do modelo não autorizam contratar plano pago; manter a conta gratuita.

ACADEMIA_LLM_PROFILE escolhe somente principal (padrão, GPT-OSS 120B) ou
reserva-groq20b (candidato GPT-OSS 20B). O perfil usa configuração versionada própria:
[principal](../../requisitos/schemas/configuracao-ia-v2.json) e
[reserva](../../requisitos/schemas/configuracao-ia-reserva-groq20b-v2.json).
Provider, endpoint, corpus, prompts, regras, parâmetros e orçamento não mudam.
Perfil desconhecido falha fechado. Não aceitar modelo, caminho ou host arbitrário.

Não implementar troca automática, retries, corrida de provedores ou uma segunda
chamada após falha. O perfil é escolhido explicitamente antes da execução/processo;
uma nova tentativa tem novo ID. Registrar modelo e fingerprint da configuração.
Replay continua pertencendo à execução original. Não alterar .env do responsável
para ativar a reserva durante o ensaio, nem expor escolha de provedor ao cliente.

Ensaio de cada modelo inclui todos os casos. A união/consolidação exige a mesma
configuração e recusa misturar modelos, escolher melhores respostas ou reaproveitar
aprovação de outro modelo. Modelo menor pode falhar em qualidade; menor tamanho
não é evidência de aprovação. Sem AI-06 aprovado, reserva permanece candidata.

Mesmo provedor não oferece independência contra indisponibilidade da Groq.
Gemini API/OpenRouter são alternativas futuras com chave própria, contrato,
configuração e ensaio separados; não foram conectados nem receberam dados.
Sem reserva qualificada, preservar falha controlada e treino manual disponível.

Evolução posterior em 2026-11-12: [ADR-009](ADR-009-gemini-api.md) implementa a
integração Gemini após fornecimento da chave; isso não qualifica automaticamente
nenhum modelo nem altera a escolha padrão.
