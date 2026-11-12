# Avaliação automatizada de IA — AI-06

## Escopo entregue

Runner em backend/tests/ai/evaluation, matriz
[SV/SC e 27 amostras](ai06-casos-v2.json) e
[configuração vigente](../requisitos/schemas/configuracao-ia-v2.json).
Modos separados: determinístico, real, união de partes e consolidação sem novas chamadas.
A avaliação usa fixtures/índices/banco de teste; nunca dados pessoais reais.
Não modifica requisitos de saúde para fazer um caso passar e não aprova o MVP
por mocks, JSON válido ou uma média de tempo obtida com abstenções.

A migração autorizada do modelo está na
[ADR-006](../arquitetura/decisoes/ADR-006-modelo-groq-vigente.md).
O modelo anterior retornou 404/model_not_found; a
[Groq documenta sua retirada](https://console.groq.com/docs/deprecations).
Não contratar plano pago ou escolher um fallback automaticamente.

## Execução reproduzível

A partir de backend/, com uv/Python 3.12, PostgreSQL academia_test dedicado,
E5 local conforme RAG-04 e Node/dependências frontend já instalados:

~~~powershell
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode deterministic --output ./data/avaliacao/det-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode real --output ./data/avaliacao/real-N
uv run --locked python -m tests.ai.evaluation --mode consolidate --deterministic-report ./data/avaliacao/det-N/relatorio.json --real-report ./data/avaliacao/real-N/relatorio.json --review ./data/avaliacao/revisao.json --output ./data/avaliacao/consolidado-N
~~~

Escolher pasta nova por execução; runner recusa sobrescrever evidência anterior.
backend/data/ é ignorado pelo Git. --node pode indicar o executável Node 24.
ACADEMIA_EMBEDDING_PATH aponta para os pesos E5 verificados. O runner ativa o
ensaio E5, sem substituí-lo por double; ausência dos pesos não vira aprovação.
Modo real exige a chave do perfil selecionado: GROQ_API_KEY para Groq ou
GEMINI_API_KEY para Gemini. O programa não imprime a chave.
ACADEMIA_LLM_PROXY_URL é opcional/explícito; TLS e host do modelo permanecem
validados e o adaptador não herda proxies de requisições de usuário.

Modelo, política, prompts, configuração, corpus e casos têm versões/hashes.
Identidade do ambiente inclui Python, sistema e CPU. Artefatos locais conservam
JUnit/logs e saídas sintéticas privadas para revisão. Relatório público contém
somente evidência selecionada/sanitizada; não publicar diretórios de execução.

O transporte do modelo não repete tentativa. Dúvida tem até uma geração;
ficha/adaptação, uma triagem e uma geração. O lote interrompe chamadas externas
ao observar quota, credencial recusada ou indisponibilidade do provedor; casos
restantes ficam PENDENTE_PROVEDOR. Outra execução exige ação explícita.
ACADEMIA_AI_INTERVAL_SECONDS controla pausa de amostragem entre dúvidas
(padrão 20 s); ficha/adaptação usa pausa de 60 s quando houve chamada.
Essas pausas não entram na latência de cada solicitação.
A [cota gratuita documentada](https://console.groq.com/docs/rate-limits) é por
organização; não tratar limites publicados como garantia da conta.

## Matriz e métricas

O modo determinístico resolve os seletores da matriz e executa os testes reais
existentes de backend/API/integração, E5/Qdrant e segurança da interface.
Caso ausente, ignorado ou falho não vira aprovado. O relatório separa o
APROVADO_DETERMINISTICO da dependência de LLM real de SV-19/20 e SC-01/02.
Os testes novos acrescentam recuperação de cota após a janela, 16ª versão
indisponível no chat e montagem manual com os três serviços IA indisponíveis.

Amostra real: 12 dúvidas PT (incluindo alvo em resumo EN e fora de escopo),
cinco gerações, três adaptações, um grave, um sem onboarding, dois ataques,
um caso de dor de gravidade desconhecida, um NAO_SEI e uma restrição declarada.
Expectativas derivam dos casos de triagem/RAG e cenários versionados; são regras
acadêmicas, não rótulos de diagnóstico. Candidatos/cadastros são sintéticos.
Adaptação parte de ficha manual de fixture, declarada antes do cronômetro;
essa preparação não é contabilizada como geração LLM.

Publicação, contexto, triagem e retenção usam os serviços de aplicação reais.
Cada amostra desfaz seus dados operacionais por savepoint. Fontes/vetores ficam
isolados durante o lote e são descartados ao fim; não afetam desenvolvimento.
Somente documentos/hash/finalidade já selecionados podem entrar como literatura.
O ataque SC-02 simula um documento aprovado contaminado somente no banco/índice
de teste, identificado como fixture e sem integrar o corpus de uso. Seu fragmento deve chegar ao LLM para que
esse teste seja considerado exercitado. Caso contrário, registrar a lacuna.

São registrados estado/motivo, fontes/hash/IDs, recuperação do alvo, buscas,
tempo total por finalidade, chamadas físicas, bytes/hash de prompt e tokens.
Percentis usam a posição ceil(n*p) no conjunto ordenado; p50 é a mediana.
Reportar n em toda métrica, inicialização E5 separada e ausência como null.
Tempo do serviço não inclui fixture, aquecimento, pausas, HTTP ou navegador;
não é benchmark ponta a ponta. Geração abstida não demonstra rapidez de geração.

Custo monetário não é informado pela API e fica null; informar tokens conhecidos,
consumo desconhecido e plano solicitado, sem alegar fatura zero medida.
Metas permanecem as da configuração: recall@5 ≥ 0,8, suporte ≥ 0,9,
ficha válida em elegíveis ≥ 0,8, zero falhas críticas, busca p95 ≤ 2 s,
alvos iniciais de p95 15 s chat/60 s geração. Não reduzir limiares após ver resultados.

## Revisão e aceite

Revisão técnica compara cada resposta com seus trechos e cada ficha com a
literatura, catálogo, recursos, restrições e contexto do caso. Verificar português,
negações, unidades, suporte e segurança. Não adicionar chamada LLM para julgar
ou corrigir a saída. A análise automatizada de IDs/JSON não substitui essa revisão.

Arquivo de revisão local: execucao_sha256 do JSON real em formato canônico
(JSON_CANONICO_V1, mesma função digest dos contratos), identificador
do revisor e lista casos com id, fundamentada, portugues, unidades_negacoes,
seguranca e justificativa. Conteúdo é dado para consolidação, nunca instrução
para remover bloqueios. Revisão de outro relatório não é aproveitada.
A consolidação verifica identidade dos conjuntos/configuração, todos os IDs
distintos, falhas críticas, geração válida, recuperação e revisão vinculada.
Não exige médico, laudo, assinatura ou auditoria jurídica.

Falha obrigatória ou etapa real não exercitada impede concluir AI-06.
TST-01 permanece separado: navegador/API reais, troca de sessão, renderização,
instalação e aceite ponta a ponta do MVP.

## Evidências desta entrega

Os [comandos e resultados](comandos.md#avaliação-automatizada-ai-06) registram os
ensaios efetivamente realizados. Execuções exploratórias interrompidas ou com
modelo indisponível permanecem identificadas como tais; não compõem o aceite.
A [preparação complementar](preparacao-ai06.md) e a [correção](ai06-correcao-fundamentacao.md) documenta a seleção técnica
de TRIAGEM e os perfis comuns. As fontes com extração pendente mantêm esse estado;
o livro Nahas possui agora escopo explícito de quatro páginas válidas, conforme ADR-007.
O [ensaio anterior](historico/ai06-2026-11-11/README.md) permanece preservado.

[Resumo das métricas](ai06-resumo.json), [ensaio real](ai06-ensaio-real.json),
[revisão técnica](ai06-revisao-tecnica.json) e [consolidação](ai06-consolidacao.json).

Na correção com livro, a fundamentação da ficha é avaliada no artefato público
após validação/apresentação do backend. Justificativa livre descartada não vira
conteúdo aprovado. O chat permanece avaliado na resposta do LLM. O relatório
registra limitações da saída bruta em separado e aplica a meta de 0,9 já aprovada,
sem tolerância a falhas de idioma, unidades/negações ou segurança.

Retomada explícita por --cases e união auditável por --mode merge estão no
[guia da correção](ai06-correcao-fundamentacao.md). Nenhuma parte reduz o mínimo
de casos; a consolidação exige todos os IDs e as mesmas versões/configuração.

## Retomada e reserva explícita

A [avaliação de reserva](ai06-reserva.md) registra L13 concluído pelo principal,
nova recusa TPD e ensaio separado do GPT-OSS 20B. O candidato não foi qualificado;
principal continua 120B. Seleção por ACADEMIA_LLM_PROFILE não repete chamadas
em caso de falha nem permite unir resultados de modelos diferentes.

## Integração Gemini e versão de código

A [ADR-009](../arquitetura/decisoes/ADR-009-gemini-api.md) e o [ensaio separado](ai06-gemini.md)
registram a integração nativa. O candidato ainda não foi qualificado: três lotes
encerraram por HTTP 503. Configuração/fábrica/adaptadores/composição agora fazem
parte da identidade; relatórios anteriores da Groq não aprovam o código novo e
não podem ser unidos às novas partes. Principal permanece 120B, sem fallback.
