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
- Execução única por cliente/chave; mesma chave com entrada diferente retorna 409.
  Chamadas LLM são únicas por etapa; estado interrompido não dispara replay.
- Revogação/snapshot/inventário/configuração superados são revalidados na publicação.
- Foto ativa por cliente matriculado; substituição mantém metadados, descarta
  referência antiga via provedor; reconhecimento não libera acesso sozinho.
- Evento unique(origem,event_id), comando/retorno correlacionados e idempotentes.
  Unique parcial presenca(cliente_id) WHERE saida_evento_id IS NULL.
  Apenas passagem confirmada muda frequência; replay não muda lotação.
- Matrícula manual sem FK obrigatória para pagamento. Plano ativo ao contratar.
  Datas civis início<=hoje<=fim no fuso da academia; ausente/futura/vencida inválida.
  Limites contratados congelados; regra detalhada de janela fecha em MEM-01/GATE-08.
- Cobrança permite múltiplas tentativas; referência externa única por provedor quando
  existir. Compra de plano exige pagamento.plano_id com plano ativo na contratação;
  valor contratado permanece no pagamento, sem depender de preço futuro. O campo é
  opcional só para lançamentos que não representam compra de plano.
  Confirmação não matricula nem cadastra face. Dinheiro decimal e não-negativo.
- Aulas: fim>início; estado CANCELADA preserva histórico. Reservas fora do primeiro escopo.
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
| Matrícula | ATIVA → VENCIDA/ENCERRADA; renovação preserva histórico |
| Acesso | RECEBIDO → IDENTIFICADO/DESCONHECIDO → ALLOW/DENY; passagem é evento separado |
| Comando | CRIADO → ACEITO/FALHOU/EXPIRADO; aceito não implica passagem |
| Aviso | PENDENTE → ENVIADO/FALHOU; reenvio controlado, sem duplicar pendência |

## Origem no MER preservado

USUARIO → usuario/usuario_papel/perfis/sessoes; CLIENTE/FUNCIONARIO preservados.
ONBOARDING/Queixa → versões com dados estruturados e origem; evitar queixa duplicada.
VERSAO_FICHA/ITEM_FICHA → dias/itens/parecer; INSTRUCAO → designação + recursos.
INTERACAO_IA → conversa/mensagem/execução/triagem/etapas/evidências.
EQUIPAMENTO/EXERCICIO → catálogo e combinações; BIOMETRIA/REGISTRO_ACESSO →
referência, eventos, decisões e presença. ASSINATURA → matrícula.
PLANO/COBRANCA/PAGAMENTO e AULA → capacidades posteriores correspondentes.
Corpus, metadados e eventos duráveis completam as lacunas documentadas.
PNG original é origem histórica, não foi regravado.
