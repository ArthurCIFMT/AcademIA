# Configuração de IA e critérios de avaliação

Status: DEFINIDA por delegação em 2026-11-04.
Valores canônicos: [configuração v2](schemas/configuracao-ia-v2.json).
[Triagem e onboarding](onboarding-e-triagem.md), [ADR](../arquitetura/decisoes/ADR-004-rag-llm-e-corpus.md).

A configuração fixa modelos, limite por rota, chunking/busca, retenção e metas.
GROQ_API_KEY é credencial pessoal de ambiente, não criada/versionada por esta entrega.
JSON Object Mode não garante aderência ao schema; validar no backend e encerrar
erro sem segunda geração automática. No máximo uma análise + uma geração em ficha.
Não enviar 24000 bytes só porque o teto permite: são limite máximo, não alvo.
Bytes/caracteres não são tokens; registrar tokens reais do provedor por etapa.
Teto de prompt é validado antes da chamada; não retirar alerta para caber. Se
candidatos ou evidências suficientes não couberem, encerrar com limitação.

Retorno de ficha: schema JSON versionado com dias (1–6), até 6 itens/dia (máximo
36), cada item com exercicio_id, ordem, series, repeticoes, carga_kg opcional,
cadencia opcional, intervalo_segundos e observacoes. Números são validados por
tipo/faixas técnicas (séries 1–10, repetições 1–100, carga >=0, intervalo 0–600);
essas faixas não prescrevem dose nem substituem o suporte da literatura/política.
repeticoes é string inteira ou intervalo A-B, com 1<=A<=B<=100 e sem texto livre;
backend valida o intervalo. carga_kg é decimal não-negativo ou null.
Sem inventar carga individual: pode ser null para determinação pelo instrutor.
Prompt usa IDs/descrições compactas de até 40 candidatos viáveis; validação final
verifica IDs e inventário atual. Sem conjunto suficiente, não gerar seleção falsa.
Schema de saída materializado em [AI-02](../arquitetura/orquestracao-ia.md) e
[contratos JSON](schemas/execucao-ia-v1.schema.json), a partir destes campos.
Toda adaptação de saúde liga evidência pertinente à intervenção/ressalva.

Dados brutos de chat/execução expiram em 90 dias (comando de manutenção e teste);
metadados mínimos de auditoria ligados à ficha não são apagados por essa limpeza.
Não duplicar conteúdo de ficha eliminada como execução consultável. Retenção de
15 versões permanece independente. Diretórios locais e pesos fora do Git.

Avaliação: mínimo 24 casos revisados, incluindo o conjunto SV-01–SV-24 e perguntas
PT/EN adequadas. Recordar top-K contra fragmentos esperados, suporte/fidelidade
das respostas e saída válida em casos elegíveis. Critérios de sucesso constam no
JSON: bloqueios críticos, mistura de clientes ou recurso inexistente têm tolerância zero.
Amostra maior e relatório por rota devem informar numerador/denominador e falhas.
Metas de p95 total são objetivos iniciais (15 s chat, 60 s ficha), não resultados;
se não atendidas, relatar e ajustar configuração por decisão registrada, não mentir
sobre desempenho. p95 vetorial ≤2 s permanece requisito no cenário de ensaio.
Nenhuma avaliação real foi executada nesta preparação.

## Proteção contra abuso no chat

A configuração vigente define até **6 novas execuções em 60 segundos**, em janela
móvel por cliente autenticado, compartilhada entre dúvidas e adaptações
iniciadas pelo chat. A cota é reservada de forma atômica para que requisições
concorrentes com chaves diferentes não ultrapassem o teto. Ao atingir o
limite, a API devolve HTTP 429 com `Retry-After` e encerra antes de chamar
embeddings, recuperação vetorial ou LLM. Replay idempotente só consulta a
execução do próprio cliente e não abre outra execução nem consome nova vaga.
Os demais limites de tamanho, tempo, contexto e chamadas continuam aplicáveis.
Os casos de regressão estão na
[matriz de segurança](../testes/rag-ia-semantico.md#segurança-do-chat-e-do-rag).

## Migração de modelo em AI-06

Por autorização expressa em 2026-11-11, a
[ADR-006](../arquitetura/decisoes/ADR-006-modelo-groq-vigente.md) substitui o
modelo inicial descontinuado por openai/gpt-oss-120b na configuração v2,
com reasoning_effort=low/include_reasoning=false. A v1 permanece histórica.
Demais limites/metas não foram afrouxados; ausência de evidência continua abstenção.

## Perfil de reserva em avaliação

Por solicitação do responsável em 2026-11-12, a [ADR-008](../arquitetura/decisoes/ADR-008-reserva-llm-explicita.md)
prepara a [configuração candidata GPT-OSS 20B](schemas/configuracao-ia-reserva-groq20b-v2.json).
ACADEMIA_LLM_PROFILE=principal é o padrão; reserva-groq20b é seleção explícita,
sem fallback/retry automático. Todos os demais parâmetros e limiares permanecem
iguais. Não altera a configuração principal nem aprova qualidade por herança.
Conferir [estado do ensaio](../testes/ai06-reserva.md) antes de usar a reserva.
