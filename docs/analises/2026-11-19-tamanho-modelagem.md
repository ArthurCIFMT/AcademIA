# Avaliação do tamanho da modelagem após o MVP

Data: 2026-11-19. Escopo: avaliar o MER original, o modelo lógico completo e
o banco do MVP. Nenhum schema, migration, DBML, JSON lógico ou imagem do MER
foi alterado nesta avaliação. Otimizações abaixo são propostas, não implementações.

## Conclusão

O MVP tem complexidade moderada e justificável para os requisitos aprovados.
Não há evidência de que seja necessário reduzir radicalmente o banco ou fundir
entidades de domínio. Há redundâncias pontuais de armazenamento/constraints
que podem ser simplificadas em uma entrega própria; elas merecem mais atenção
do que simplesmente tentar reduzir a quantidade de tabelas.

Para um sistema apenas de cadastro e treino manual, a estrutura seria grande.
O escopo solicitado inclui identidade segura, papéis acumuláveis, designação,
onboarding e treinos versionados, fontes RAG, execução da IA, isolamento e auditoria.
São esses requisitos que explicam boa parte da diferença em relação ao MER inicial.

## Contagens verificadas

| Artefato | Quantidade | Interpretação |
|---|---:|---|
| MER PNG original | 18 entidades com nome | Extraídas do XML draw.io incorporado no próprio PNG, sem modificar a imagem. |
| Modelo lógico completo | 43 tabelas, 335 colunas | Inclui capacidades futuras e configuração da academia. |
| ORM/migrations do MVP | 32 tabelas, 262 colunas, 53 constraints de FK | Modelo físico implementado, distinto do escopo futuro. |
| PostgreSQL de desenvolvimento | 32 tabelas, 78 índices totais | Consulta de catálogo/estatísticas em transação somente leitura. |
| Tamanho dessas tabelas e índices | 2.039.808 bytes, aproximadamente 1,95 MiB | Amostra local pequena; não inclui WAL, tamanho total do cluster, PDFs, pesos ou Qdrant. Não é teste de capacidade. |

Os 18 índices declarados explicitamente no ORM não são os 78 índices totais:
o total inclui índices de chaves primárias/unicidades. Não interpretar os outros
como supérfluos sem analisar as constraints que atendem.

Fontes: [MER original](../arquitetura/modelo-de-dados/original/MER_Academia_Completo_v4.drawio.png),
[modelo lógico](../arquitetura/modelo-de-dados/modelo-logico.json),
[DBML](../arquitetura/modelo-de-dados/modelo-logico.dbml),
[migrations](../../database/migrations/versions/) e modelos SQLAlchemy em backend/.
As contagens físicas foram comparadas com o catálogo do banco, sem ler conteúdo
de saúde ou mensagens de clientes. Estimativas de linhas não foram tratadas
como contagens exatas nem usadas para justificar capacidade de produção.

## De onde vêm as 32 tabelas do MVP

| Grupo | Tabelas | Justificativa |
|---|---:|---|
| Identidade, perfis e designação | 7 | usuario, usuario_papel, cliente, funcionario, sessao, token_acesso e designacao. Permitem sobreposição de papéis, conta/cadastro independentes e responsável histórico. |
| Onboarding/avaliação | 3 | onboarding_versao, convite_onboarding e avaliacao. Histórico e sessão restrita não devem ser confundidos com cadastro ou login normal. |
| Exercícios e fichas | 8 | exercicio, exercicio_recurso_grupo, exercicio_recurso, versao_ficha, dia_ficha, item_ficha, parecer e validacao_ficha. Catálogo, requisitos de equipamento, prescrição, publicação e parecer têm regras diferentes. |
| Equipamentos | 1 | equipamento, incluindo disponibilidade. |
| Literatura/RAG | 4 | documento, documento_versao, ingestao e fragmento. Origem bibliográfica, aprovação, processamento e vetor são conceitos distintos. |
| IA e chat | 6 | execucao_ia, triagem, etapa_ia, evidencia_execucao, conversa e mensagem. Contexto, consumo, evidência e conversa privada são rastreáveis. |
| Auditoria e comunicação | 3 | auditoria, outbox e notificacao. Autoria, idempotência de eventos e estado de entrega persistem mesmo se uma integração falhar. |
| Total | 32 | Sem tabelas financeiras ou biométricas antecipadas. |

Onze tabelas existem apenas no modelo futuro: academia, plano, matricula,
cobranca, pagamento, biometria, evento_acesso, decisao_acesso, catraca_comando,
presenca e aula_ocorrencia. Academia é configuração singleton planejada;
as outras dez pertencem às extensões de acesso/matrícula, financeiro e agenda.
Não confundir essas onze previsões com tabelas desnecessárias já implantadas.

## Simplificações concretas a considerar

| Proposta | Evidência e benefício provável | Custo/condição |
|---|---|---|
| Unificar a fonte persistida da triagem | execucao_ia.resultado.triagem e triagem.resumo armazenam o mesmo TriageResult. Reduzir duplicação de dados privados e risco de divergência é mais útil que apagar entidades arbitrariamente. | Definir a fonte canônica e hidratar o DTO na leitura; manter snapshot, política, motivos, auditoria, replay e expurgo em 90 dias. Não foi alterado agora. |
| Revisar etapa_ia.dados | O JSON de Consumption repete parte de chamadas/limites/tokens já em colunas. Pode-se montar o DTO a partir de uma representação canônica. | Conferir campos exclusivos do JSON, estados em voo e consumo desconhecido. Não remover evidência de chamadas ou orçamento para economizar campos. |
| Revisar mensagem.pergunta/pedido | A pergunta está tanto na coluna quanto no JSON do pedido, que também congela uma janela curta de histórico. Há duplicação deliberada para retomada/hash. | Só simplificar preservando a representação histórica necessária ao hash e ao replay; não reconstruir o pedido antigo com o contexto atual. |
| Remover uma FK redundante do contexto da mensagem | A FK simples de versao_contexto_id já é coberta pela FK composta (conversa_id, versao_contexto_id) → (cliente_id, id). A composta ainda protege o dono. | Ganho pequeno, requer migration nova e testes de null, referência inexistente e versão de outro cliente. Preservar a composta. |
| Avaliar a tabela conversa | Hoje contém somente id do cliente, em relação 1:1. Mensagem poderia referenciar cliente diretamente, poupando uma tabela e sua criação. | Economia pequena e mudança de FKs/serviço. Manter se forem previstos vários chats ou metadados por conversa. Não remover somente para deixar o diagrama menor. |
| Diagramar por escopo/módulo | Separar visão conceitual, MVP físico e escopo futuro torna a apresentação acadêmica mais compreensível. | Melhora legibilidade, sem ganho automático de espaço/desempenho; não esconder tabelas reais ou substituir a imagem original silenciosamente. |

As primeiras três propostas envolvem redundância real. Mesmo assim, o tamanho
local não indica urgência de armazenamento; a prioridade é clareza e manutenção.
Não foram executados EXPLAIN ANALYZE, ensaio de escala ou medição comparativa de
latência. Não prometer ganho percentual ou propor índices novos sem consulta-alvo.

## O que preservar

- USUARIO e papéis acumuláveis, com perfis específicos. Fundir cliente/funcionário
  em uma tabela com campos opcionais mistura estados e responsabilidades.
- Ficha, dia e item separados; prescrição pertence à ficha, não ao catálogo.
  O vínculo por ID de exercício e o snapshot histórico do item têm funções distintas.
- Grupos de recursos: permitem combinações obrigatórias e alternativas completas.
  Uma lista plana de equipamentos perde a diferença entre combinar recursos e
  oferecer alternativas, afetando a validação da IA.
- Publicação e parecer por versão. Validacao_ficha pode parecer um registro
  adicional, mas mantém revisão conferida/idempotência e o parecer é posterior;
  não juntar estados só para diminuir a contagem.
- Documento/versão/ingestão/fragmento e evidências de execução. Fragmento guarda
  offsets, hashes e referências, não uma segunda cópia integral do livro. O banco
  vetorial especializado é separado do PostgreSQL conforme os requisitos.
- Snapshots de onboarding em JSONB validados por schema. O projeto já evita criar
  tabela para cada medida, queixa, medicamento ou condição; normalizar tudo isso
  seria um aumento desnecessário para o trabalho acadêmico atual.
- Unicidades compostas que sustentam FKs de titularidade. Mesmo quando id já é
  PK global, a referência composta impede ligar dados de pessoas diferentes.
- Retenção de 15 fichas completas e 90 dias de conteúdo privado de chat/execução,
  sem apagar metadados de auditoria necessários. Número de tabelas não determina
  sozinho crescimento; documentos, mensagens, snapshots e vetores são relevantes.

JSONB é adequado a documentos de esquema controlado, mas não substitui FKs e
constraints relacionais. Referências técnicas: [JSON e projeto de documentos](https://www.postgresql.org/docs/17/datatype-json.html#JSON-DESIGN)
e [constraints](https://www.postgresql.org/docs/17/ddl-constraints.html).
Essas referências fundamentam as opções; as prioridades acima são avaliação
arquitetural deste projeto, não recomendação de remover dados sem medir.

## Encaminhamento

Manter o schema do MVP nesta correção. Se houver interesse em simplificar depois,
começar pela fonte única de triagem/consumo e avaliar a FK repetida; cada alteração
deve ter migration nova quando pertinente, dados preservados e testes de regressão.
Atualizar DBML/JSON/dicionário junto da decisão aplicada, nunca modificar migration
já executada. A correção do histórico solicitada nesta entrega reutiliza os
campos e índices existentes e não exige aumentar o modelo.
