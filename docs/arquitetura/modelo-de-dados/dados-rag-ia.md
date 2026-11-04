# Dados do orquestrador, RAG e IA

Especificação para FND-03 e migrations futuras; não é schema físico implementado.
MER original permanece preservado. Substitui a extensão agentiva.

| Conceito | Proprietário / persistência | Relações e invariantes |
|---|---|---|
| Documento e versão | MOD-05 / PostgreSQL | fonte, hash, idioma, licença, estado, aprovação/revogação |
| Ingestão e fragmento | MOD-05 / metadados relacionais + banco vetorial especializado | versão documental, página/seção, configuração/embedding; ingestão idempotente |
| Conversa e mensagem | MOD-06 / PostgreSQL | cliente autorizado, ordem, estados, correlação; histórico paginado e janela limitada no LLM |
| Execução | MOD-06 / PostgreSQL | finalidade dúvida/triagem/ficha/adaptação, pedido idempotente, estado, modelo/prompts/política/corpus e orçamento |
| Resumo e decisão de triagem | MOD-06 / PostgreSQL | snapshot MOD-03, projeção estruturada/versionada, dados ausentes e alertas preservados; decisão/motivos sem diagnóstico |
| Etapa e evidência usada | MOD-06 / PostgreSQL | busca/análise/geração/validação; fonte/trecho e versões reais; consumo/tempo sem raciocínio interno |
| Exercício/variação e recursos | MOD-04 / PostgreSQL | catálogo separado de ITEM_FICHA, relação com recursos MOD-10; dispensa explícita |
| Versão e item de ficha | MOD-04 / PostgreSQL | origem IA/manual, autoria humana quando aplicável, execução de origem, snapshot e parecer separados |

Não criar plano de pesquisa, questões de agente, catálogo de ferramentas dinâmicas
ou avaliação de próximas ações: não pertencem ao fluxo atual. Estado/etapas da
execução são suficientes para rastrear o orquestrador sem loop de pesquisa.
Limites, tentativas e reserva de consumo não reiniciam em retomada. Rede fora de
transação longa; publicação idempotente por contrato MOD-04.

Livro/conteúdo especializado vai ao corpus; inventário e dados privados não vão
ao índice compartilhado. Revogação invalida novo uso/cache, sem apagar proveniência.
Mudança relevante de snapshot/política/inventário exige revalidação antes de publicar.
Conteúdo excluído por RF-17/RF-35 não fica duplicado como ficha consultável na
execução, cache ou exportação; preservar auditoria e snapshots de execução existentes.

Não criar entidades de atestado, laudo, assinatura médica, aprovação jurídica ou
liberação clínica para o MVP; casos sintéticos e regras são documentados no projeto.
Atualização confirmada em MOD-03 cria snapshot novo e invalida triagem anterior;
execuções antigas mantêm referência à versão usada, sem reescrever histórico.

Esquemas reais, campos/unidades, retenção operacional e orçamento são definidos
nos gates/modelagem. [Arquitetura](../rag-semantico.md) e
[macrorequisitos](../../requisitos/macrorequisitos-ia-rag.md).
