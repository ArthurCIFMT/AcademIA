# Dados do orquestrador, RAG e IA

Modelo do escopo completo: documento/versão implementados na migration 0012
([RAG-01](../corpus.md)); ingestão e fragmentos entregues na migration 0013
([RAG-04](../indexacao-documental.md)); orquestrador/triagem/etapas/evidências entregues na migration 0014
([AI-03](../geracao-persistente.md)); mensagens privadas entregues na
migration 0015 ([AI-05](../chat-e-adaptacao.md)) e normalizadas na revisão 0016.
RAG-03 mantém [artefatos privados de extração](../extracao-documental.md), por
versão/hash/configuração, fora do índice e do Git. Não são ingestões vetoriais ativas.
MER original permanece preservado. Substitui a extensão agentiva.

| Conceito | Proprietário / persistência | Relações e invariantes |
|---|---|---|
| Documento e versão | MOD-05 / PostgreSQL | fonte, hash, idioma, licença, estado, aprovação/revogação |
| Ingestão e fragmento | MOD-05 / metadados relacionais + banco vetorial especializado | versão documental, página/seção, configuração/embedding; ingestão idempotente |
| Mensagem por cliente | MOD-06 / PostgreSQL | titular direto, ordem, estados, correlação; pergunta em pedido.mensagem congelado; histórico paginado e janela limitada no LLM, sem tabela-marcador conversa |
| Execução | MOD-06 / PostgreSQL | finalidade dúvida/triagem/ficha/adaptação, pedido idempotente, estado, modelo/prompts/política/corpus e orçamento |
| Resumo e decisão de triagem | MOD-06 / PostgreSQL | resumo canônico em execucao_ia.resultado.triagem; tabela triagem mantém snapshot/política/decisão/motivos, sem resumo duplicado; dados ausentes e alertas preservados |
| Etapa e evidência usada | MOD-06 / PostgreSQL | busca/análise/geração/validação; fonte/trecho e versões reais; consumo canônico nas colunas de etapa_ia, DTO hidratado e tokens totais derivados, sem raciocínio interno |
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

Modelo lógico, campos, retenção e orçamento foram definidos na preparação:
[modelo DBML](modelo-logico.dbml), [dicionário](dicionario.md),
[invariantes](invariantes-e-estados.md) e
[campos/triagem](../../requisitos/onboarding-e-triagem.md).
As capacidades futuras permanecem delimitadas pelo manifesto. [Arquitetura](../rag-semantico.md) e
[macrorequisitos](../../requisitos/macrorequisitos-ia-rag.md).

## Marco AI-01

A [triagem](../triagem-academica.md) entrega projeção, decisões tipadas e porta
assistida, com auditoria mínima. Não cria tabelas paralelas de execução/triagem.
O registro interno inclui códigos, resumo, snapshot, política e referências;
execucao_ia/triagem/etapa_ia/evidencia_execucao são implementadas em
AI-03, usando as portas definidas em AI-02. A API de preparação não armazena anamnese no log ou no índice RAG.

## Histórico consultável e janela de IA

CA-18.9/CA-18.10 distinguem consulta de histórico e contexto enviado ao modelo.
Mensagem já possui versao_contexto_id; não é necessária nova entidade para
recuperar mensagens anteriores à ficha vigente. O DTO informa essa referência
e contexto_anterior; 20 turnos/página e 90 dias permanecem. Não reenviar a conversa
inteira nem reintroduzir resposta apoiada em ficha expurgada/fonte revogada.

## Normalização da persistência — revisão 0016

A [ADR-013](../decisoes/ADR-013-normalizacao-persistencia-ia-chat.md) remove
conversa, coluna pergunta, triagem.resumo e etapa_ia.dados. Mensagem usa cliente_id
com FK direta ao cliente e FK composta titular/contexto da ficha. O JSON do pedido
é a fonte da pergunta, preservado para hash e replay. Não duplicar o consumo no
resultado da execução: hidratá-lo das colunas, com tokens de entrada/saída ambos
nulos ou conhecidos não negativos e soma total derivada. O resumo completo da
triagem permanece somente em execucao_ia.resultado.triagem, sem alterar seu DTO.
Essas mudanças preservam contratos, orçamento e limpeza de dados privados em
90 dias; não unificam tabelas de domínio com responsabilidades distintas.
As [evidências de migração e regressão](../../testes/otimizacao-modelagem-20261119.md)
registram a preservação dos dados legados e os limites da verificação.
