# Invariantes e estados — modelo v1

[Modelo DBML](modelo-logico.dbml) / [JSON](modelo-logico.json) / [dicionário](dicionario.md).
Artefatos lógicos aceitos por delegação, com capacidades entregues e futuras.
O [manifesto](../../prompts/README.md) e as [migrations](../../../database/README.md)
distinguem a implementação física disponível do restante do modelo.
Módulos e ownership preservados. Cada entrega cria apenas suas próprias tabelas.

## Garantias a materializar nas migrations

- academia.id=1 e único registro; não há tenant_id.
- E-mail normalizado único, perfis cliente/funcionário com PK=usuario_id.
- Roles no enum de quatro papéis; credenciais e sessão conforme ADR-002.
- Índice parcial único designacao(cliente_id) WHERE fim IS NULL.
- Datas fim>=início; designação aponta funcionário com papel INSTRUTOR ativo,
  garantido pelo serviço/transação (não inventar FK de papel).
- Onboarding: unique(cliente_id,numero); uma edição concorrente usa revision e
  trava cliente; concluído é imutável, nova confirmação cria nova versão.
- Número de ficha é monotônico por cliente, inclusive após expurgo; lock no cliente
  para alocar/publicar. Unique parcial versao_ficha(cliente_id) WHERE vigente=true.
- Publicação, troca de vigente, retenção de 15, evento/outbox são transacionais.
  Rascunhos não contam. Expurgo exclui dia/item e marca conteúdo expirado; metadados,
  parecer e correlação sobrevivem; não excluir vigente por limpeza.
- Rejeitar versão posterior exclui conteúdo da rejeitada retida anterior, sem apagar
  aceita pela regra específica; parecer atrasado é ordenado por número da versão,
  não só pela hora do evento. Limite global de 15 continua independente.
- Validação técnica de publicação manual é imutável por versão/revisão;
  registra responsável e conferência explícita de restrições, separada do parecer.
- Parecer conclusivo é único por versão, imutável e exige motivo na rejeição.
  PENDENTE é a ausência de parecer conclusivo no fluxo implementado.
- Nova versão não herda parecer; origem MANUAL exige instrutor autor/designação;
  IA identifica execução, não inventa autor humano. Parecer nunca bloqueia consulta.
- Item mantém snapshot de nome/descrição usado; edição do catálogo não reescreve
  histórico. Quando existirem execuções de treino, snapshots já registrados não
  são apagados; não criar módulo de execução nesta fundação.
- Exercício/variação: nome_normalizado obrigatório e único, inclusive inativos;
  trim + espaços internos colapsados + lowercase, mantido pelo serviço e constraint.
- Exercício ativo: grupo de alternativa não vazio, todos seus recursos disponíveis,
  OU dispensa explícita sem recurso obrigatório. Relação grupo/recurso é única.
- Documento único por ambiente/catálogo; versão única por documento/número e
  ambiente/hash. Escopo TESTE não integra referências de literatura, mesmo aprovado.
  Conteúdo e metadados bibliográficos são imutáveis; aprovação/revogação têm autor,
  data e revisão, revogação também exige motivo e preserva aprovação anterior.
- Versão de documento aprovada e ingestão completa antes do uso ativo. Chunks
  compartilham modelo/dimensão/coleção; Qdrant não é autoridade de aprovação.
- Ingestão (0013): unique(versão,config_hash), plano/configuração/proveniência
  imutáveis e curador identificado. Fragmentos únicos por ingestão/ordem e vetor_id;
  página física PDF ou linhas TXT, offsets e hash, até 300 tokens de conteúdo e
  512 de entrada. Checkpoint só após confirmação do vetor. Trigger exige contagem
  total indexada antes de CONCLUIDA; gate de uso revalida aprovação/revisão no PG.
  Falha parcial fica inativa; retomada reconcilia recibos Qdrant e checkpoints sem
  duplicar embeddings íntegros. Não apagar metadados para esconder falhas.
- Execução única por cliente/chave; mesma chave com entrada diferente retorna 409.
  Chamadas LLM são únicas por etapa; estado interrompido não dispara replay.
- Revisão 0016: mensagem aponta diretamente ao cliente; não há tabela conversa.
  Unique(cliente_id,solicitacao_id), índice(cliente_id,criada_em) e FK composta
  mensagem(cliente_id,versao_contexto_id) → versao_ficha(cliente_id,id) preservam
  idempotência, histórico e titularidade. A FK simples de contexto é redundante
  e foi removida; o contexto pode ser nulo sem dispensar a FK do cliente.
- Pergunta tem uma única fonte em mensagem.pedido.mensagem, string obrigatória de
  1 a 1.000 caracteres após btrim. Pedido completo e hashes continuam congelados;
  consulta histórica não os reconstrói com onboarding/ficha/histórico atuais.
- Resumo de triagem canônico em execucao_ia.resultado.triagem; a tabela triagem
  conserva metadados de política/snapshot/decisão, sem JSON resumo duplicado.
  Retenção privada de 90 dias remove o conteúdo, preservando recibos e auditoria.
- Consumo canônico nas colunas de etapa_ia, sem JSON dados ou cópia em resultado.
  DTOs são hidratados; total de tokens é derivado. Entrada/saída são ambos nulos
  ou ambos conhecidos não negativos. Consumo desconhecido não significa zero;
  não perder reserva, contadores ou registro de chamada durante limpeza/replay.
- Revogação/snapshot/inventário/configuração superados são revalidados na publicação.
- Uma referência facial ativa e uma candidata pendente por cliente matriculado.
  A conclusão descarta o exemplo anterior via provedor e conserva auditoria.
  A candidata pendente fica indisponível para identificação.
- Evento unique(origem,event_id), comando/retorno correlacionados e idempotentes.
  Unique parcial presenca(cliente_id) WHERE saida_evento_id IS NULL.
  Apenas passagem confirmada muda frequência. Replays são idempotentes, e a
  reconciliação ordena ocorrências por instante, direção (entrada primeiro) e UUID.
- Matrícula manual sem FK obrigatória para pagamento. Plano ativo ao contratar.
  Datas civis início<=hoje<=fim no fuso da academia; ausente/futura/vencida inválida.
  Limites contratados congelados. O [GATE-08](../preparacao-gate-08.md) registra
  o limite por dia civil no fuso da academia e a renovação sem sobreposição.
- Cobrança permite múltiplos lançamentos vinculados. A
  [compra simulada](../compra-simulada.md) exige plano ativo com preço; plano,
  nome, preço e instante contratados permanecem no recibo. O UUID identifica
  uma operação idempotente. Pendente ou recusado não tem data de confirmação.
  Confirmação não matricula nem cadastra face. Dinheiro decimal e não-negativo.
  No [registro manual](../pagamentos-manuais.md), o valor é positivo, a referência
  é única entre lançamentos confirmados e a correção preserva o registro anterior.
  O vínculo de substituição exige o mesmo cliente.
  [Cobranças](../cobrancas.md) usam matrícula e pagamentos do mesmo cliente.
  Cada edição preserva uma revisão com autoria. O saldo considera pagamentos
  confirmados com data registrada. A inadimplência acadêmica é informativa.
- Aulas: `fim > inicio`, estado AGENDADA ou CANCELADA e revisão positiva.
  Cancelar preserva o registro administrativo e retira a ocorrência da agenda pública.
  [Contrato da agenda](../agenda.md).
- Outbox e notificação idempotentes; autor da ação não apaga auditoria livremente.
  TTL técnico de 90 dias não apaga metadados necessários à ficha/auditoria.

## Máquinas de estado

| Recurso | Transições principais |
|---|---|
| Conta | CONVIDADO → ATIVO → INATIVO/BLOQUEADO; reativação administrativa auditada |
| Perfil | ativo/inativo, independente da conta e do outro perfil |
| Onboarding | RASCUNHO → CONCLUIDO; alteração cria novo RASCUNHO/versão, não reescreve o concluído |
| Triagem | DADOS_INSUFICIENTES / BLOQUEADO_POR_SEGURANCA / ELEGIVEL_PARA_GERACAO |
| Execução IA | PENDENTE → EM_EXECUCAO → CONCLUIDA / FALHOU / INTERROMPIDA / CANCELADA |
| Ficha | RASCUNHO → PUBLICADO → SUBSTITUIDO; conteúdo expurgado recebe CONTEUDO_EXPIRADO |
| Parecer | PENDENTE → ACEITO/REJEITADO; decisões históricas atribuíveis |
| Documento | PENDENTE → APROVADO → REVOGADO; ativação exige ingestão completa |
| Ingestão | PROCESSANDO → CONCLUIDA/FALHA/REVOGADA; FALHA retoma PROCESSANDO; PENDENTE_TRATAMENTO exige revisão; reparo de CONCLUIDA retorna PROCESSANDO |
| Matrícula | Estado persistido ATIVA ou ENCERRADA. Para ATIVA, situação FUTURA, VIGENTE ou VENCIDA deriva do dia civil. A renovação cria outro período. |
| Acesso | ACS-02 guarda uma identificação por origem e ID. Só IDENTIFICADO recebe cliente. Autorização ALLOW/DENY e passagem confirmada são etapas próprias |
| Comando | CRIADO → ACEITO/FALHOU/EXPIRADO; aceito não implica passagem |
| Aviso | PENDENTE → ENVIADO/FALHOU; reenvio controlado, sem duplicar pendência |

## Origem no MER preservado

USUARIO → usuario/usuario_papel/perfis/sessoes; CLIENTE/FUNCIONARIO preservados.
ONBOARDING/Queixa → versões com dados estruturados e origem; evitar queixa duplicada.
VERSAO_FICHA/ITEM_FICHA → dias/itens/parecer; INSTRUCAO → designação + recursos.
INTERACAO_IA → mensagem por cliente/execução/triagem/etapas/evidências.
O marcador conversa introduzido na 0015 foi removido na normalização 0016,
sem retirar a funcionalidade de conversa ou a separação entre histórico e contexto.
EQUIPAMENTO/EXERCICIO → catálogo e combinações; BIOMETRIA/REGISTRO_ACESSO →
referência, eventos, decisões e presença. ASSINATURA → matrícula.
PLANO/COBRANCA/PAGAMENTO e AULA → capacidades posteriores correspondentes.
Corpus, metadados e eventos duráveis completam as lacunas documentadas.
PNG original é origem histórica, não foi regravado.
