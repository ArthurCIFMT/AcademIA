# Orquestrador com RAG vetorial semântico

## Decisão vigente

A IA responde dúvidas, analisa resumo do onboarding e gera fichas com LLM.
Recuperação é semântica de fluxo fixo; agente orquestrador não significa Agentic RAG.
Substitui a pesquisa iterativa e a revisão parcial de fichas exclusivamente manuais.
[Macrorequisitos](../requisitos/macrorequisitos-ia-rag.md): MRF01–MRF15.

## Rotas

| Rota | Entradas e etapas | Saída e limite |
|---|---|---|
| Dúvida | Identidade → pergunta/histórico curto → busca → LLM → conferência | Resposta PT com fontes ou abstenção; até uma geração |
| Triagem | Snapshot concluído → resumo estruturado → regras → busca pertinente → análise LLM → decisão do backend | Insuficiente, bloqueado, requer avaliação ou elegível; até uma análise |
| Ficha/adaptação | Triagem válida → candidatos/recursos → busca especializada → geração → schema/regras → publicação MOD-04 | JSON validado, nova versão e parecer PENDENTE; até uma geração após triagem |

Etapas são predefinidas. Não há planner LLM, escolha autônoma de ferramentas,
reformulação em loop ou agentes biomecânico/periodização/revisor obrigatórios.
Reutilizar triagem só com snapshot/política/fontes relevantes válidos e iguais.
Falha de análise não equivale a elegibilidade. Mensagem comum não publica adaptação.

## Resumo do onboarding

MOD-03 fornece snapshot autorizado. MOD-06 projeta DTO estruturado minimizado,
sem nome/e-mail/biometria desnecessários. Preserva condições, medicamentos, lesões,
objetivos, experiência, limitações e estados ausente/desconhecido/negativo explícito.
Campos/unidades/obrigatoriedade dependem do esquema aprovado antes de ONB-02.
Não usar nova chamada LLM só para resumir: projeção em código com regras verificáveis.
Se não couber todo alerta pertinente, pedir complemento/revisão; não truncar alerta.
Relato novo que altera saúde exige confirmação/versionamento, não edição silenciosa.

## Conhecimento especializado e catálogo

Livro/literatura aprovados entram em ingestão offline com proveniência e licença
avaliada. Cada pedido recupera poucos blocos pertinentes, preservando ressalvas;
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
não acessa SQL, internet aberta ou escrita de domínio. Corpus recuperado é dado,
nunca instrução. Permissões são impostas pelo backend em toda consulta.

## Validação, saúde e publicação

Regras de bloqueio e limites clínicos exigem política revisada em GATE-04.
LLM sinaliza problemas declarados; não diagnostica, concede liberação médica nem
remove bloqueios. Dado necessário ausente/contraditório impede elegibilidade.
Backend confere schema, referências reais/vigentes, catálogo, recursos, limites
estruturados, snapshot e versão-base. Validação mecânica não prova segurança universal.
Não acrescentar revisor LLM ou reparo automático como atalho para corrigir erro.

MOD-04 publica conteúdo válido com parecer PENDENTE sem esperar aceite humano;
instrutor designado recebe aviso e pode aceitar/rejeitar/modificar ou criar manualmente.
Preservar retenção de 15 e substituição de rejeitada. Falha da IA mantém vigente.

## Orçamento e desempenho

Até uma geração por dúvida; até uma análise de triagem e uma geração por pedido
de ficha/adaptação. Orçamento global limita transporte/retries, tokens, tempo,
tamanho e custo quando mensurável; não reinicia em retomada. Valores em GATE-04.
Medir p50/p95 total por rota, busca, chamadas e tokens no provedor gratuito escolhido.
Busca p95 ≤ 2 s não é promessa de tempo total. Modelo/provedor gratuito e livro
definitivos continuam pendentes; não afirmar aceleração ou capacidade sem ensaio.
Não manter transação SQL durante rede; timeout/cancelamento invalida resposta tardia.

## Dados, testes e materiais

[Dados relacionais](modelo-de-dados/dados-rag-ia.md),
[testes](../testes/rag-ia-semantico.md),
[acervo](../../materiais/rag/README.md).
Literatura é compartilhada aprovada; conversas, snapshots, resumos e fichas são
dados privados operacionais. Retenção de execução não é o limite de 15 fichas.
Não executar implementação por apenas ler esta especificação.
