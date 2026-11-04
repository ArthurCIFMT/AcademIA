# Análise do MER original — sem alteração do diagrama

Este relatório incorpora a correção posterior: publicação do treino independe do
parecer do instrutor, reconhecimento facial é real e a catraca é fictícia. Somente
o relatório mudou; o diagrama e seu XML embutido permanecem iguais.
Veja [fluxos atualizados](fluxos-atualizados.md).

## Método e preservação

Fonte: [PNG original do responsável](modelo-de-dados/original/MER_Academia_Completo_v4.drawio.png).
A revisão leu a imagem e o XML draw.io embutido no chunk tEXt/mxfile em memória.
Foram identificadas 307 células de desenho e 18 entidades, em imagem 6492 × 3187.

SHA-256 de referência:
`5B57634D6936BC76C82E3F85BFA45A91626EC734AF77B45E0A083E2990C1DF93`.

Nenhum PNG, XML, .drawio, DBML, schema ou migration foi criado ou alterado por esta
análise. Este relatório é uma recomendação de evolução, não um modelo aprovado.
Seu conteúdo serve de entrada à revisão futura de FND-03.

## O que a base já representa bem

As entidades atuais são USUÁRIO, CLIENTE, FUNCIONÁRIO, ACADEMIA, REGISTRO_ACESSO,
BIOMETRIA, ONBOARDING, Queixa, INTERACAO_IA, VERSAO_FICHA, ITEM_FICHA, EXERCÍCIO,
ASSINATURA, PLANO, COBRANÇA, PAGAMENTO, AULA DE GINÁSTICA e EQUIPAMENTO.

O MER já separa pessoa autenticável e perfis, catálogo e itens de ficha, versões,
assinatura/plano/cobrança/pagamento e cadastro biométrico. Essa base pode ser
evoluída; não exige redesenhar o domínio do zero.

## Prioridade 1 — antes de implementar o núcleo do MVP

| Evidência no MER atual | Mudança provavelmente necessária | Origem |
|---|---|---|
| USUÁRIO possui atributo único perfil | Representar múltiplos papéis por pessoa, por relação equivalente a PAPEL/USUARIO_PAPEL no modelo lógico | RF-05 e decisão de papéis acumuláveis |
| Usuário especializa cliente e funcionário, sem explicitar sobreposição | Esclarecer perfis opcionais e possibilidade de coexistirem na mesma identidade; garantir vínculo estável | RF-01/RF-04/RF-07 |
| Não há vínculo histórico cliente–instrutor | Acrescentar designação com início/fim, responsável principal, ator da atribuição e status | RF-34 |
| CLIENTE–ONBOARDING está 1 : 0..1 | Permitir reavaliação/versionamento e contexto identificável de cada geração; distinguir onboarding inicial de avaliações | RF-11–RF-15, RN-21, MRF03 |
| VERSAO_FICHA só tem id, número, criação, ativa, origem e motivo | Acrescentar autoria, publicação e parecer por versão como dimensões independentes, com responsável e datas | RF-17/RF-35, RN-31 |
| EXERCÍCIO contém ordem, séries, tempo_descanso, carga e observação | Transferir prescrições específicas para ITEM_FICHA; catálogo guarda características do movimento | RN-20, MRF05/MRF07 |
| ITEM_FICHA não representa dia/microciclo/cadência | Acrescentar esses dados ou uma estrutura de dia/organização equivalente | MRF07 |
| AJUSTA liga INTERACAO_IA diretamente a ITEM_FICHA, sem cardinalidade junto ao item | Relacionar execução a proposta/nova versão e, se útil, aos itens afetados; preservar itens aprovados históricos | RF-19, RN-16–RN-18 |
| Não há corpus/documentos/versões/ingestão/evidências | Acrescentar metadados e relações de proveniência; os vetores ficam no banco especializado | MRF01/MRF02 e derivados MRF11/MRF15 |
| INTERACAO_IA só possui mensagem, resposta, instante e tipo | Representar solicitação/execução, estado, decisão de triagem, política/modelo/prompts e falhas | RF-15/RF-18/RF-19, MRF04–MRF06 |

### Designação, publicação, parecer e ficha vigente

Uma possível relação de designação liga CLIENTE e FUNCIONÁRIO com papel de
instrutor, preservando quem era responsável em cada período. A regra de um
principal ativo precisa ter garantia de integridade.

A revisão profissional pode ser uma entidade vinculada à VERSAO_FICHA. Não é
obrigatório criar uma entidade PROPOSTA separada: conteúdo versionado com estados
separados de geração, publicação e parecer pode atender ao fluxo. Aceite não
condiciona visibilidade/chat; nova versão não herda parecer anterior.
É necessário distinguir autor, gerador automático e profissional revisor.

Uma entidade-raiz FICHA pode facilitar a identidade/versionamento, mas não é
obrigatória se a relação cliente–versões e a versão atual forem inequívocas.
A ativação de uma versão deve impedir duas atuais. A retenção segue RF-35:
rejeitar a vigente mantém sua consulta; outra ficha posterior rejeitada exclui
conteúdo/itens da rejeitada anterior, preservando metadados de auditoria e snapshots
de treinos executados. Modelar essa exclusão sem quebrar chaves históricas.
RF-17 também limita a 15 versões publicadas completas por cliente, incluindo a
vigente. Conteúdo excedente das mais antigas é removido independentemente do
parecer; metadados permanecem para auditoria e numeração não é reutilizada.
A imagem original permanece intacta; essas decisões orientam o futuro modelo lógico.

Cada proposta deve identificar avaliação/onboarding e versão-base usados.
Na publicação, comparar a atualidade do contexto; no parecer posterior, registrar
instrutor designado e versão avaliada.
Política de revalidação precisa ser definida antes de implementar essa regra.

### Relação INSTRUCAO

No arquivo atual, INSTRUCAO conecta quatro entidades:
EQUIPAMENTO (0..N), FUNCIONÁRIO (0..1), EXERCÍCIO (1) e CLIENTE (1).

A conexão pode representar uma intenção de prescrição/instrução, mas mistura:
quem é responsável pelo cliente, o que foi prescrito e qual equipamento é utilizado.
Ela não traz a temporalidade da designação nem decisão de aprovação de uma versão.

Recomenda-se separar os conceitos. Designação e prescrição são necessárias no
escopo atual; a relação exercício/variação–equipamento foi confirmada pelo
responsável e deve integrar o MVP. Modelar recursos obrigatórios, combinações e
alternativas e dispensa explícita de equipamento (RF-15/RF-32/RN-37).

### Queixas e chaves

Há tanto ONBOARDING.queixas quanto a entidade Queixa. É preciso escolher uma fonte
canônica e sua temporalidade, evitando guardar duas versões divergentes da queixa.

Os três atributos de Queixa — id_queixa, dt_criacao e mensagem — estão sublinhados.
Na notação usual isso pode sugerir chave composta. Confirmar a intenção e,
provavelmente, manter apenas o identificador como chave, usando data/conteúdo como dados.

ITEM_FICHA tem id_item e id_versao_ficha sublinhados e representação de entidade
fraca. Isso pode ser uma escolha válida de chave composta; esclarecer no dicionário,
em vez de declarar automaticamente um erro.

REGISTRO_ACESSO também sublinha id_registro e id_evento_externo. Distinguir chave
primária da unicidade para idempotência, incluindo a origem se IDs externos não
forem globalmente únicos.

## Prioridade 2 — comunicação, chat e dados transversais

| Área | Recomendação | Observação |
|---|---|---|
| Avisos | Representar notificação/destinatário/estado de envio/consulta | Necessário ao aviso da IA ao instrutor, RF-35 |
| Auditoria | Registrar ator, ação, recurso, motivo, instante e correlação | Não duplicar anamnese/foto no evento |
| Chat | Separar conversa e mensagens, ou estrutura equivalente | A dupla mensagem/resposta não expressa bem conversas e falhas parciais |
| Contexto | Vincular geração/adaptação a snapshot autorizado | Chat geral não precisa exigir uma geração completa em toda mensagem |
| Convites | Permitir expiração/reenvio/consumo e distinguir convite de login de onboarding | Pode reutilizar estrutura comum com finalidades isoladas |
| Identidade externa | Prever identificador estável do provedor se OIDC for escolhido | senha_hash e recuperação na aplicação dependem de GATE-02 |
| Tempos e arquivos | Definir UTC/ISO 8601 e referências de armazenamento | Layout físico só depois da arquitetura aceita |

O RAG precisa distinguir documento lógico, sua versão, processamento e fragmentos.
O PostgreSQL pode armazenar a referência estável de um chunk enquanto o banco
vetorial armazena vetor/texto/metadados. A distribuição exata deve evitar duplicação
incoerente e preservar evidências usadas por propostas antigas.

Não é necessário criar tabelas complexas para toda medicação, patologia ou medida
no projeto acadêmico. É necessário que o contexto seja compreensível e que as
restrições usadas pelo validador sejam estruturadas, versionadas e testáveis.
As fontes e critérios de gravidade continuam pendentes de decisão aprovada.

## Prioridade 3 — acesso, matrícula e módulos complementares

| Evidência atual | Evolução recomendada | Momento |
|---|---|---|
| REGISTRO_ACESSO está obrigatoriamente ligado a cliente | Separar evento recebido, identidade/decisão e passagem; desconhecido também pode ser registrado | Antes de ACS-02/ACS-03 |
| Registro só possui tipo, data/hora e status | Acrescentar origem, confiança, motivo, correlação, identificador e, quando aplicável, autor de liberação manual | Controle de acesso |
| BIOMETRIA admite até uma referência por cliente | Referência da API real, estado técnico, matrícula prévia e autor; validar captura nova no reconhecimento | ACS-01/ACS-02 |
| ASSINATURA já liga cliente, plano e validade | Pode ser matrícula; incluir atendente, modalidade, limites e histórico, sem exigir relação com pagamento | MEM-01 |
| Não há comando/retorno da catraca simulada | Representar correlação, validade e idempotência; comando aceito é distinto de passagem simulada | ACS-07/ACS-03 |
| AULA DE GINÁSTICA usa dia_semana e horas | Acrescentar data de ocorrência ou separar aula/ocorrência, conforme RF-30 | AUL-01 |
| EQUIPAMENTO já possui situação e imagem | MVP: disponibilidade operacional e vínculo com exercício/variação são obrigatórios para prescrição | EQP-01; TRN-01; RN-37 |
| COBRANÇA–PAGAMENTO está 1 : 0..1 | Prever múltiplas tentativas/transações e confirmação idempotente por provedor | Financeiro tardio |
| ACADEMIA existe como entidade | Definir se é configuração de estabelecimento único ou escopo multitenant | GATE-03, antes do modelo lógico |

Uma decisão de autorização não prova que a pessoa atravessou a catraca.
Lotação deve derivar de passagens confirmadas, com política para duplicatas,
eventos fora de ordem, entrada repetida e saída sem entrada.

Substituir foto não exige armazenar foto anterior: o histórico pode guardar
somente metadados de ação, respeitando a regra de descarte fornecida.

## Cardinalidades e invariantes para a futura revisão

1. Uma identidade pode ter vários papéis, sem duplicar a pessoa.
2. Um cliente pode ter múltiplas designações históricas e apenas o principal
   vigente definido pela política.
3. Um cliente pode ter múltiplas avaliações/snapshots.
4. Uma versão usa itens de exercícios e pode ter várias decisões/revisões históricas.
5. Uma versão publicada possui itens; rascunho vazio exige discutir a atual
   cardinalidade mínima 1..N entre VERSAO_FICHA e ITEM_FICHA.
6. Uma execução da IA aponta aos dados, políticas e fontes que utilizou.
7. Uma cobrança pode exigir múltiplas tentativas, ainda que apenas uma seja efetivada.
8. Um evento externo pode não resolver um cliente; frequência confirmada deve
   conseguir identificar o cliente correspondente.
9. Timestamp, unicidade e índices serão especificados no modelo lógico/físico,
   sem confundir diagrama conceitual com migration pronta.

## O que permanece opcional ou condicionado

- Tabela-raiz FICHA versus identidade da ficha por cliente/versões.
- Sessões efetivamente executadas, cargas realizadas e progresso por exercício.
- Reservas, lista de espera e capacidade de aulas, além do RF-30 básico.
- Vários estabelecimentos com isolamento multitenant.
- Normalização clínica detalhada e financeiro avançado.

## Encaminhamento

Priorizar identidade/papéis, designação, avaliações, prescrição, revisões e RAG.
Depois revisar acesso/matrícula e complementares, deixando pagamento detalhado para
a fase tardia. A implementação futura altera o modelo revisado e cria migrations;
a imagem original deve continuar preservada como fonte de origem.
