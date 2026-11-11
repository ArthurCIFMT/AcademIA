# Orquestrador com RAG vetorial semântico

## Decisão vigente

A IA responde dúvidas, analisa resumo do onboarding e gera fichas com LLM.
Recuperação é semântica de fluxo fixo; agente orquestrador não significa Agentic RAG.
Substitui a pesquisa iterativa e a revisão parcial de fichas exclusivamente manuais.
[Macrorequisitos](../requisitos/macrorequisitos-ia-rag.md): MRF01–MRF15.
Escopo didático: ver [AGENTS.md](../../AGENTS.md). Revisão do corpus e dos casos
significa conferência técnica do projeto, sem validação médica/jurídica externa.

## Rotas

| Rota | Entradas e etapas | Saída e limite |
|---|---|---|
| Dúvida | Identidade → pergunta/histórico curto → busca → LLM → conferência | Resposta PT com fontes ou abstenção; até uma geração |
| Triagem | Snapshot concluído → resumo estruturado → regras → busca pertinente → análise LLM → decisão do backend | DADOS_INSUFICIENTES, BLOQUEADO_POR_SEGURANCA ou ELEGIVEL_PARA_GERACAO; até uma análise |
| Ficha/adaptação | Triagem válida → candidatos/recursos → busca especializada → geração → schema/regras → publicação MOD-04 | JSON validado, nova versão e parecer PENDENTE; até uma geração após triagem |

Etapas são predefinidas. Não há planner LLM, escolha autônoma de ferramentas,
reformulação em loop ou agentes biomecânico/periodização/revisor obrigatórios.
Reutilizar triagem só com snapshot/política/fontes relevantes válidos e iguais.
Falha de análise não equivale a elegibilidade. Mensagem comum não publica adaptação.

## Resumo do onboarding

MOD-03 fornece snapshot autorizado. MOD-06 projeta DTO estruturado minimizado,
sem nome/e-mail/biometria desnecessários. Preserva condições, medicamentos, lesões,
objetivos, experiência, limitações e estados ausente/desconhecido/negativo explícito.
Campos/unidades/obrigatoriedade estão no [esquema v1](../requisitos/onboarding-e-triagem.md).
Não usar nova chamada LLM só para resumir: projeção em código com regras verificáveis.
Se não couber todo alerta pertinente, pedir complemento/revisão; não truncar alerta.
Relato novo que altera saúde exige confirmação/versionamento, não edição silenciosa.

## Conhecimento especializado e catálogo

Livro/literatura selecionados pelo responsável/curador entram em ingestão offline
com proveniência e metadados de licença registrados, sem auditoria jurídica externa. Cada pedido recupera poucos blocos pertinentes, preservando ressalvas;
não envia todo livro, anamnese ou histórico completo. Sem suporte pertinente para
adaptação por saúde, abster-se. Não presumir que os PDFs atuais cobrem todo caso.

MOD-04 fornece IDs ativos e requisitos de exercícios; MOD-10 fornece disponibilidade.
Recursos devem estar cadastrados, ativos e operacionais; alternativas completas
e dispensa explícita de equipamento são respeitadas. O RAG não define inventário.
Reduzir candidatos de forma determinística sem excluir alternativas necessárias;
caso não caiba conjunto suficiente, retornar limitação sem inventar IDs.

## Contratos conceituais

| Interface | Proprietário | Dados essenciais |
|---|---|---|
| ObterSnapshotAutorizado | MOD-03 | cliente autorizado, versão, dados/estados de preenchimento |
| RecuperarEvidencias | MOD-05 | finalidade, consulta minimizada, corpus/versão, top-K; retorna chunks e proveniência |
| ObterCandidatos | MOD-04 com leitura MOD-10 | IDs ativos/viáveis e revisão do inventário |
| AnalisarResumo | MOD-06 / adaptador LLM | resumo, política e evidências; sinais/motivos estruturados |
| GerarFicha | MOD-06 / adaptador LLM | resumo elegível, candidatos e evidências; JSON da ficha |
| PublicarVersao | MOD-04 | conteúdo validado, versões-base e correlação idempotente |

JSON Schema nas fronteiras e objetos tipados internos. Modelo não escolhe cliente,
não acessa SQL, internet aberta ou escrita de domínio. Permissões são impostas
pelo backend em toda consulta.

O MOD-05 consulta o índice aprovado e retorna trechos com proveniência dentro do
limite de recuperação. O MOD-06 decide quando consultar essa porta e envia ao
LLM somente a entrada autorizada para a etapa em execução. Mensagens e trechos
recuperados são dados externos ao prompt de controle. O LLM não pode consultar
o índice diretamente, trocar a identidade do cliente nem decidir permissões.
O backend valida resultados e mantém as decisões de bloqueio e publicação.
A [matriz de segurança do chat](../testes/rag-ia-semantico.md#segurança-do-chat-e-do-rag)
verifica separadamente recuperação, orquestração, API e navegador.

## Validação, saúde e publicação

As regras de bloqueio da demonstração são documentadas pelo responsável em GATE-04
com casos sintéticos e fontes pertinentes. Trabalho didático não exige laudo,
atestado ou aprovação médica/jurídica externa. LLM sinaliza informações declaradas,
sem diagnóstico. Não existe estado ou rota de desbloqueio por documento médico.
Caso grave permanece bloqueado; falta/contradição de dado necessário gera
DADOS_INSUFICIENTES, com complemento dos dados pelo próprio cliente ou revisão
da avaliação pelo instrutor. Parecer do instrutor não remove bloqueio de caso grave.

Backend confere schema, referências reais/vigentes, catálogo, recursos, limites
estruturados, snapshot e versão-base. Validação mecânica não prova segurança universal.
Não acrescentar revisor LLM ou reparo automático como atalho para corrigir erro.

MOD-04 publica conteúdo válido com parecer PENDENTE sem esperar aceite humano;
instrutor designado recebe aviso e pode aceitar/rejeitar/modificar ou criar manualmente.
Preservar retenção de 15 e substituição de rejeitada. Falha da IA mantém vigente.

## Orçamento e desempenho

Até uma geração por dúvida; até uma análise de triagem e uma geração por pedido
de ficha/adaptação. Cada etapa LLM tem uma tentativa por execução, sem retry
automático. Pedido repetido com mesma chave reusa execução; nova tentativa exige
ação explícita e novo ID. Ingestão/busca podem repetir transporte sob orçamento.
Orçamento global limita tokens, tempo, tamanho, chamadas e custo quando mensurável;
não reinicia em retomada. Valores em GATE-04.
Medir p50/p95 total por rota, busca, chamadas e tokens no provedor gratuito escolhido.
Busca p95 ≤ 2 s não é promessa de tempo total. Modelos e corpus iniciais foram definidos em
[ADR-004](decisoes/ADR-004-rag-llm-e-corpus.md); não afirmar aceleração ou capacidade sem ensaio.
Não manter transação SQL durante rede; timeout/cancelamento invalida resposta tardia.

## Dados, testes e materiais

[Dados relacionais](modelo-de-dados/dados-rag-ia.md),
[testes](../testes/rag-ia-semantico.md),
[acervo](../../materiais/rag/README.md).
Literatura é compartilhada aprovada; conversas, snapshots, resumos e fichas são
dados privados operacionais. Retenção de execução não é o limite de 15 fichas.
Não executar implementação por apenas ler esta especificação.

## Conexão vetorial implementada

RAG-02 entregou a [porta Qdrant local persistente](banco-vetorial.md), com
identidade por coleção, conexão sob demanda, singleton e erros controlados.
Não corresponde ainda à extração/indexação ou recuperação semântica.

## Configuração inicial aceita

Qdrant local persistente (um processo), E5-small/384/cosseno, chunks 300 tokens
com sobreposição 48 e top-K 5. LLM Groq/Llama 3.3 70B com json_object validado.
Ver [configuração canônica](../requisitos/configuracao-ia-rag.md) e
[corpus selecionado](../../materiais/rag/corpus-inicial.json). Modo local é engine
especializada persistente para protótipo; modo servidor só na fase apropriada.
