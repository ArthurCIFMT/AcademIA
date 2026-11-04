# Extensão de dados para Agentic RAG

Proposta lógica autorizada para orientar FND-03 e as migrations de RAG-01/04 e
AI-01/03/05. Não há modelo físico, ORM ou migration implementados nesta entrega.
Os nomes abaixo são conceituais e devem ser conciliados com o modelo lógico aceito;
se a entidade já existir, evoluí-la sem duplicação nem edição de migration aplicada.
O [MER original](original/MER_Academia_Completo_v4.drawio.png) permanece intacto.

## Separação dos armazenamentos

| Armazenamento | Conteúdo/proprietário | Não armazenar ali |
|---|---|---|
| PostgreSQL / MOD-05 | Documentos, versões, trechos/proveniência, aprovação e execução de ingestão | Estado privado de cliente como corpus compartilhado |
| Banco vetorial / MOD-05 | Vetores de literatura e IDs/metadados necessários à recuperação | Onboarding, fotos faciais, histórico privado de chat ou cópias de fichas como literatura |
| PostgreSQL / MOD-06 | Solicitações/execuções, plano operacional, chamadas, decisões e vínculos de evidência | Uma segunda ficha vigente, parecer profissional próprio ou raciocínio interno |
| PostgreSQL / MOD-03/04/10 | Onboarding, exercícios/fichas e equipamentos nos módulos existentes | Tabelas duplicadas para acesso livre pelo agente |
| Arquivo/objeto documental / MOD-05 | Original e extração controlada referenciados por hash/versão | Acesso a caminho arbitrário indicado por LLM |

PostgreSQL mantém integridade e estado operacional; a busca vetorial continua
especializada. Registros JSON estruturados podem representar planos/argumentos
versionados, mas chaves, referências, estado e contadores críticos devem possuir
garantias explícitas de integridade, não depender de texto livre em JSON.

## Entidades de conhecimento — MOD-05

| Entidade conceitual | Relações/campos necessários | Entrega |
|---|---|---|
| DOCUMENTO / VERSAO_DOCUMENTO | Origem, hash, idioma, versão, estado, autor/data de aprovação/revogação, revisão de aprovação | RAG-01 |
| TRECHO_DOCUMENTO | Versão documental, ID estável, página/seção/ordem, hash da extração, vizinhança/contexto e referência de índice | RAG-03/04 |
| EXECUCAO_INGESTAO | Documento, configuração/modelo/dimensão dos embeddings, status, tentativas e erros minimizados | RAG-01/04 |

Um trecho tem exatamente uma versão documental; uma versão possui vários trechos.
ID vetorial não é chave estrangeira transacional entre bancos: metadados relacionais
e filtros de aprovação são a autoridade. Publicação de índice e revogação devem
tratar falhas parciais; vector store atrasado não autoriza ler versão revogada.

## Entidades operacionais — MOD-06

| Entidade conceitual | Campos/relações mínimos | Entrega |
|---|---|---|
| EXECUCAO_IA | Cliente/solicitante autorizados, tipo do pedido, chave de idempotência e hash de entrada, snapshot/contexto, versão-base opcional, execução-pai opcional, estado de execução, triagem e pesquisa separados; versões de modelo/prompts/políticas/corpus; limites e consumo; versão publicada como referência opcional; criação/atualização UTC | AI-03, integrando o resultado da triagem de AI-01 |
| ETAPA_PESQUISA | Execução, sequência e revisão do plano, ação/ferramenta/versão, questão investigada, argumentos/resultado minimizados ou referências, estado, motivo resumido, tentativas, tempo e consumo | AI-03, conforme contratos de AI-02 |
| EVIDENCIA_RECUPERADA | Execução/etapa, documento/versão/trecho, página/seção, hash do conteúdo retornado, score de recuperação, idioma e referência do resultado; agrupamento de duplicatas | AI-03 usando proveniência de MOD-05 |
| AVALIACAO_EVIDENCIA | Execução/revisão do plano, questões e evidências avaliadas, decisão, lacunas/conflitos/códigos e política usada, data/hora | AI-03 |
| CONVERSA / MENSAGEM | Cliente/contexto autorizado e vínculos com execução, versão consultada e eventual adaptação; campos já previstos para chat | AI-05, sem nova cópia do estado de treino |

Relações: uma execução possui N etapas, N evidências e N avaliações; cada etapa,
evidência e avaliação pertence a uma só execução. Retomada técnica mantém a mesma
execução e seus contadores. Nova resposta a pedido de dados pode criar execução
filha com novo snapshot e autorização; não implica publicação automática.

Cada execução pode originar no máximo uma versão publicada por pedido idempotente.
Uma ficha manual pode não ter execução de IA. A ligação com a versão publicada
apenas aponta ao registro de MOD-04: não replica situação de parecer ou conteúdo.

## Invariantes para o modelo lógico e migrations

- Unicidade da chave de idempotência por contexto autorizado/tipo de operação;
  mesma chave com entrada diferente produz conflito, não reuso silencioso.
- Sequência/revisão do plano e identificação das chamadas são únicas dentro da
  execução; resultados tardios não mudam execução terminal.
- Evidência/etapa/avaliação referenciam a mesma execução; não vincular evidência
  privada de A à execução de B. Snapshot e identidade não podem ser substituídos
  por um argumento do modelo.
- Contadores não negativos e reserva atômica de orçamento antes de executar ação;
  concorrência, falha de processo e retry não autorizam N+1.
- Estados clínicos, operacionais, de pesquisa, publicação e parecer são dimensões
  diferentes; timeout não equivale a bloqueio clínico ou parecer rejeitado.
- Guardar revisão de contexto, política, corpus, catálogo/disponibilidade e
  versão-base usadas. As referências não transferem ownership entre módulos.
- Não persistir raciocínio interno; conteúdo sensível de planos/argumentos fica
  em área autorizada, com limites de tamanho. Logs gerais são minimizados.
- Aplicar integridade por constraints/transações onde possível e complementar
  com validação de serviço para invariantes semânticas e entre armazenamentos.

## Rede, transações e publicação

Chamadas LLM/embedding/vetorial ficam fora de transações SQL longas. Mudanças de
estado são curtas e controladas por revisão/concorrência. A publicação final usa
o contrato único de MOD-04, idempotência e controle de versão-base; a retenção de
15 e a regra de rejeitadas continuam transacionais no módulo proprietário.

A aprovação de fonte e a disponibilidade devem ser verificadas novamente na
publicação. Os contratos de MOD-05/10 devem oferecer revisão/validação consistente
com a transação final, usando serviços públicos e unidade de trabalho definida
na implementação. Não basta confiar no snapshot lido antes da chamada ao LLM.
Se o contrato ainda não existir, AI-03 registra a lacuna e bloqueia somente a
publicação afetada; não consulta tabelas alheias ou amplia permissões para prosseguir.

## Retenção, memória e auditoria

O limite de 15 se aplica a versões publicadas completas, não a todos os registros
de execução/evidência. Estes também precisam de política de retenção própria,
limite de tamanho e acesso, definida antes do aceite; não reter transcrições e
resultados completos indefinidamente por conveniência.

Remover uma prescrição não apaga a rastreabilidade necessária, mas a trilha não
pode reconstruí-la como ficha disponível nem recolocá-la no contexto ativo.
Referências de versões excluídas mantêm identidade/auditoria, sem cascata que apague
execuções históricas. Preservar snapshots de treinos executados quando existentes.

Revogação de documento preserva metadados históricos e impede seu uso ativo,
inclusive por cache. Chave de cache/memória inclui cliente/execução quando privada
e revisões de contexto/corpus/política pertinentes; nunca misturar com literatura
compartilhada. Memória vetorial privada não faz parte deste escopo.

## Compatibilidade e execução futura

FND-03 já lê requisitos e arquitetura e pode incorporar esta extensão sem alterar
seu prompt. RAG-01/04 cuidam de metadados e ingestão; AI-02 define contratos sem
exigir banco da execução já pronto; AI-03 cria/evolui a persistência do workflow.
Não criar dependência AI-02 → AI-03 → AI-02. AI-05 estende o chat conforme necessário.
As migrations devem ser novas/reproduzíveis e limitadas ao ownership da entrega.
