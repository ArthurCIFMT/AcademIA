# Configuração de IA e critérios de avaliação

Status: DEFINIDA por delegação em 2026-11-04.
Valores canônicos: [configuração v1](schemas/configuracao-ia-v1.json).
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
Schema de saída detalhado será materializado em AI-02 a partir destes campos.
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
