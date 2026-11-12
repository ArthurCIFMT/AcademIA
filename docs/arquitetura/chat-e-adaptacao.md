# Chat e adaptação versionada — AI-05

## Entrega e fronteiras

MOD-06 persiste perguntas privadas e coordena etapas fixas; MOD-05 recupera
evidências aprovadas; MOD-03 fornece snapshots confirmados; MOD-04 consulta e
publica versões por seus serviços públicos. Nenhum acesso direto às tabelas
internas desses módulos foi introduzido. A composição em app/main.py e as portas
existentes de contexto, estado, geração e publicação foram estendidas para conectar
o chat. Não há dependências novas, Docker, planner ou ferramentas escolhidas pelo LLM.

A interface em /area/cliente/assistente aceita dúvida geral sem onboarding,
ficha ou parecer. Uma pergunta usa até três perguntas anteriores do mesmo cliente
e da mesma versão de contexto, limitadas a 3.000 caracteres no total, mais os
trechos recuperados. Respostas anteriores, fichas completas, anamnese e livros
não são carregados no contexto de dúvidas. Sem evidência, abster-se.
A resposta em português é informação e nunca altera uma ficha.

## Contratos REST

Todas as rotas exigem sessão de cliente ativo, permissão própria e no-store.
O cliente é resolvido pela sessão; não há cliente_id ou conversa_id na entrada.
POST exige também CSRF/Origin. Autorização ocorre antes de histórico/RAG/provedor.

| Método e rota | Comportamento |
|---|---|
| POST /api/v1/ia/chat | Criar/repetir explicitamente um turno idempotente |
| GET /api/v1/ia/chat?page=1 | Histórico do contexto vigente, páginas de até 20 turnos |
| GET /api/v1/ia/chat/contexto/adaptacao | IDs da ficha e snapshot atuais, número do snapshot e títulos dos dias; sem dados médicos |
| GET /api/v1/ia/chat/{solicitacao_id} | Retomar recibo próprio sem executar geração |
| GET /api/v1/ia/chat/{solicitacao_id}/diferencas | Consultar antes/depois retidos de uma adaptação publicada |

[Schema de pedido e turno](../requisitos/schemas/chat-ia-v1.schema.json).
Pedido DUVIDA: solicitacao_id UUID, mensagem de 1 a 1.000 caracteres e finalidade
opcional DUVIDA. Campos extras, controles inválidos e seletores de contexto são
rejeitados (422). Pedido ADAPTACAO exige finalidade, versao_base_id, onboarding_id
e dia_alvo inteiro de 1 a 6. Não aceita histórico/estado/fontes enviados pelo cliente.
O backend converte o snapshot confirmado para onboarding_confirmado_id do
[contrato interno](../requisitos/schemas/execucao-ia-v1.schema.json).

Turno: solicitacao_id, pergunta, criada_em UTC, finalidade, estado, motivo,
resposta textual estruturada ou null, fontes bibliográficas e versao_publicada_id
ou null. Não retorna resumo de saúde nem proposta de ficha na resposta do chat.
As diferenças reutilizam os DTOs públicos de consulta de ficha e informam
conteudo_expirado; não constituem uma segunda cópia da prescrição.

401 sem sessão; 403 sem permissão/CSRF; 404 para turno ausente/alheio; 409 para
pedido divergente, snapshot/base superados ou diferenças indisponíveis; 422 para
entrada inválida; 429 com Retry-After: 60; 503 para preparação indisponível.
Falhas ocorridas dentro do orquestrador permanecem estados de execução no recibo.
Uma reserva sem execução é AGUARDANDO e, após 100 segundos, INTERROMPIDA;
falha de preparação deixa FALHA/PREPARACAO_RECUSADA, sem detalhes sensíveis.

## Adaptação explícita

1. Cliente atualiza/confirma os dados no formulário autenticado existente de
   onboarding; a interface de chat apenas oferece o link, sem escrever em MOD-03.
2. Ao selecionar adaptação, consultar metadados atuais, escolher um dia e confirmar
   que o onboarding reflete a situação relatada. Snapshot e base são reenviados.
3. Backend valida titularidade, snapshot confirmado, base vigente/retida e dia.
   Resolve resumo minimizado, política e recursos por contratos existentes.
4. Executar nova triagem (até uma análise LLM) e geração (até uma chamada).
   Novo relato relevante detectado exige atualização confirmada; grave bloqueia,
   insuficiência não vira saúde presumida. Sem suporte de saúde pertinente ou
   com conflito, abster-se. Não há retry/reparo automático ou fallback pago.
5. Validar JSON, referências, catálogo e recursos. O dia-alvo pode mudar; quantidade
   de dias e todos os demais dias devem ser idênticos à base. Sem mudança efetiva,
   abster-se. Alteração de outra parte é recusada.
6. Publicação transacional por MOD-04 revalida snapshot, fontes e inventário,
   cria nova vigente com parecer PENDENTE e aviso ao instrutor. Consulta independe
   do aceite. Erro preserva a vigente anterior. Reutiliza retenção de 15 versões
   completas e regra específica de rejeitadas; não muda snapshots de execução.

## Suporte técnico para cenários de saúde

A configuração opcional ACADEMIA_RAG_HEALTH_CONFIG aponta para JSON local privado,
com no máximo 1 MiB, conforme
[schema de suporte](../requisitos/schemas/suporte-saude-ia-v1.schema.json).
schema_version=1; cenarios associa SHA-256 exato do resumo estruturado autorizado
a um escopo de condição/população/intervenção; anotacoes contém até 200 anotações
técnicas de suporte/conflito identificadas por hash do arquivo e do trecho.
O hash do resumo é produzido pelo serviço de triagem; não deve ser fabricado ou
calculado a partir de descrição livre. Alteração do resumo invalida a associação.

Somente o responsável técnico configura cenários/evidências; usuário da API ou
modelo não escolhe escopo nem escreve essas anotações. Sem configuração,
restrições declaradas permanecem sem suporte e geram abstenção conservadora.
Arquivo inválido/ausente quando configurado retorna erro controlado, sem fallback
para saudável. Configuração participa do fingerprint revalidado antes da publicação.
Busca deve ainda recuperar evidência pertinente aprovada; associação sozinha não
libera geração e não remove bloqueio determinístico. Não há aprovação médica,
diagnóstico ou inferência clínica nova. Hashes de cenários privados ficam fora do
corpus compartilhado e do Git. DUVIDA não usa esse mapeamento de saúde.

## Persistência, orçamento e retenção

Migration 0015 cria conversa (uma por cliente, PK igual ao cliente) e mensagem
(um turno/pergunta, pedido congelado pelo servidor, estado e referência de
contexto). O resultado do assistente fica em execucao_ia; não duplicar ficha ou
resposta em mensagem. Chave única conversa+solicitacao e FK composta garantem
que a versão de contexto pertence ao mesmo cliente. Explicação e comparação
de fichas são resolvidas pelo serviço de MOD-04.

Dúvida/adaptação compartilham seis novas execuções em 60 segundos por cliente.
Reserva transacional com advisory lock PostgreSQL ocorre antes de RAG/embeddings;
reservas de mensagens ainda sem execução também ocupam vaga. O claim de execução
exclui sua própria reserva e não cobra duas vezes. Concorrência/replay não ampliam
o orçamento. GERACAO inicial conserva o limite próprio vigente.
Cada etapa reserva despacho e consumo na persistência de AI-03, sem segurar
transação SQL durante a rede. Consulta GET, foco e recarga nunca geram POST.
Retry de transporte é explícito com o mesmo UUID; entrada diferente exige UUID novo.
Após 100 segundos, uma reserva abandonada sem execução não pode ser reaberta.
Execução terminal nunca repete chamada LLM ao reusar UUID.

Histórico serve apenas o contexto atual, incluindo o turno da adaptação que o
publicou, e os últimos 90 dias. Não reenviar perguntas de versões substituídas.
Consulta direta de dúvida antiga retira resposta/fontes se mudou o contexto;
revogação de evidência também retira resposta/fontes. Comparação lê apenas
conteúdo ainda retido de MOD-04 e informa expiração. Não restaura ficha apagada.
A manutenção existente de AI-03 também expurga perguntas/pedidos após 90 dias,
preservando recibos e contadores de auditoria. Esse prazo independe das 15 fichas.

## Interface e segurança

Mensagem/resposta é texto React, sem HTML/Markdown executável. URLs bibliográficas
aceitam somente http/https e usam noopener/noreferrer. Troca/revogação de sessão
remove conteúdo privado; retomada usa UUID na URL e somente GET.
Falha/429 não abre retry automático. A confirmação de adaptação é invalidada se
snapshot ou base mudar. A ficha publicada abre no recurso existente de consulta.

Mensagens e documentos são dados sem autoridade para SQL, ferramentas,
permissões ou publicação. JSON Schema, referências reais, titularidade, validações
em código e publicação por contrato limitam os efeitos. Não alegar imunidade
semântica a prompt injection com base em um modelo simulado.

## Verificação e limites

[Comandos e evidências](../testes/comandos.md#chat-e-adaptação-ai-05).
SC-01/02/03/04/06: isolamento com dois clientes, documento/pergunta maliciosos
em fronteira de dados, rejeição de referências/JSON inválidos, texto HTML inerte,
links inseguros bloqueados e cota atômica concorrente/replay.
Testes usam PostgreSQL/Qdrant reais e respostas/embeddings sintéticos controlados;
a regressão também exercita E5 e Mailpit reais. Não comprova qualidade/latência do
LLM gratuito. AI-06 e o E2E TST-01 permanecem abertos, assim como as pendências
técnicas anteriores do corpus/livro.
