# Dicionário do modelo lógico v1

Fonte: [JSON](modelo-logico.json), [DBML](modelo-logico.dbml),
[invariantes e estados](invariantes-e-estados.md). Cada módulo possui seus dados;
FK entre módulos não permite acessar repositório alheio. Migrations de domínio
são criadas somente pelos respectivos prompts, não todas no scaffold.

## academia — MOD-00

Singleton id=1

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | integer | pk | — |
| nome | varchar(120) | required | — |
| endereco | text | opcional | — |
| descricao | text | opcional | — |

## usuario — MOD-01

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| email | varchar(254) | required unique | — |
| senha_hash | text | required | — |
| estado | varchar(20) | required | — |
| criado_em | timestamptz | required | — |
| revision | integer | required | — |

## usuario_papel — MOD-01

Unicidade usuario_id+papel; enum fechado de quatro papéis

Unicidades: usuario_id+papel.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| usuario_id | uuid | required | usuario.id |
| papel | varchar(30) | required | — |

## cliente — MOD-01

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| usuario_id | uuid | pk | usuario.id |
| nome | varchar(120) | required | — |
| data_nascimento | date | required | — |
| telefone | varchar(25) | opcional | — |
| ativo | boolean | required | — |

## funcionario — MOD-01

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| usuario_id | uuid | pk | usuario.id |
| nome | varchar(120) | required | — |
| cargo | varchar(80) | required | — |
| data_admissao | date | required | — |
| ativo | boolean | required | — |

## sessao — MOD-01

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| usuario_id | uuid | required | usuario.id |
| token_hash | char(64) | required unique | — |
| csrf_hash | char(64) | required | — |
| criado_em | timestamptz | required | — |
| ultimo_uso_em | timestamptz | required | — |
| expira_em | timestamptz | required | — |
| revogada_em | timestamptz | opcional | — |

## token_acesso — MOD-01

Finalidades de credencial separadas do convite/sessão restrita de onboarding

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| usuario_id | uuid | required | usuario.id |
| hash | char(64) | required unique | — |
| finalidade | varchar(30) | required | — |
| expira_em | timestamptz | required | — |
| consumido_em | timestamptz | opcional | — |

## designacao — MOD-02

Um vínculo principal sem fim por cliente

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| instrutor_id | uuid | required | funcionario.usuario_id |
| inicio | timestamptz | required | — |
| fim | timestamptz | opcional | — |
| atribuido_por | uuid | required | usuario.id |

## onboarding_versao — MOD-03

Dados validados pelo schema v1; versões concluídas imutáveis; contexto não é índice público

Unicidades: cliente_id+numero.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| numero | integer | required | — |
| estado | varchar(20) | required | — |
| schema_version | integer | required | — |
| idade_snapshot | integer | required | — |
| dados | jsonb | required | — |
| criado_por | uuid | required | usuario.id |
| concluido_em | timestamptz | opcional | — |
| revision | integer | required | — |

## convite_onboarding — MOD-03

Token é trocado por sessão restrita de edição com expiração, não login geral

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| onboarding_id | uuid | required | onboarding_versao.id |
| token_hash | char(64) | required unique | — |
| expira_em | timestamptz | required | — |
| revogado_em | timestamptz | opcional | — |
| consumido_em | timestamptz | opcional | — |
| sessao_restrita_hash | char(64) | opcional | — |
| sessao_expira_em | timestamptz | opcional | — |

## avaliacao — MOD-03

Avaliação opcional do instrutor; não é laudo ou aprovação prévia

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| instrutor_id | uuid | required | funcionario.usuario_id |
| onboarding_id | uuid | required | onboarding_versao.id |
| registrado_em | timestamptz | required | — |
| dados | jsonb | required | — |

## equipamento — MOD-10

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| nome | varchar(120) | required | — |
| descricao | text | opcional | — |
| categoria | varchar(80) | opcional | — |
| imagem_ref | text | opcional | — |
| ativo | boolean | required | — |
| operacional | boolean | required | — |
| revision | integer | required | — |

## exercicio — MOD-04

Cada variação pode ter ID próprio; catálogo não é prescrição

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| nome | varchar(120) | required | — |
| nome_normalizado | varchar(120) | required unique | — |
| descricao | text | required | — |
| grupo_muscular | varchar(80) | required | — |
| dispensa_equipamento | boolean | required | — |
| ativo | boolean | required | — |
| revision | integer | required | — |

## exercicio_recurso_grupo — MOD-04

Grupos são alternativas OR; todos os recursos de um grupo são obrigatórios

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| exercicio_id | uuid | required | exercicio.id |

## exercicio_recurso — MOD-04

Unicidade grupo+equipamento; grupo vazio não libera prescrição

Unicidades: grupo_id+equipamento_id.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| grupo_id | uuid | required | exercicio_recurso_grupo.id |
| equipamento_id | uuid | required | equipamento.id |

## versao_ficha — MOD-04

Origem IA pode não ter autor humano; modificação manual exige instrutor designado; metadados sobrevivem ao expurgo

Unicidades: cliente_id+numero.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| numero | integer | required | — |
| origem | varchar(20) | required | — |
| autor_id | uuid | opcional | usuario.id |
| onboarding_id | uuid | required | onboarding_versao.id |
| avaliacao_id | uuid | opcional | avaliacao.id |
| versao_base_id | uuid | opcional | versao_ficha.id |
| estado_publicacao | varchar(25) | required | — |
| vigente | boolean | required | — |
| publicada_em | timestamptz | opcional | — |
| conteudo_excluido_em | timestamptz | opcional | — |
| motivo_exclusao | varchar(40) | opcional | — |

## dia_ficha — MOD-04

Unicidades: versao_id+ordem.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| versao_id | uuid | required | versao_ficha.id |
| ordem | integer | required | — |
| titulo | varchar(60) | required | — |

## item_ficha — MOD-04

Nome/descrição do exercício usados são snapshot do item, preservados contra edição do catálogo

Unicidades: dia_id+ordem.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| dia_id | uuid | required | dia_ficha.id |
| exercicio_id | uuid | required | exercicio.id |
| ordem | integer | required | — |
| series | integer | required | — |
| repeticoes | varchar(40) | required | — |
| carga_kg | numeric(8,2) | opcional | — |
| intervalo_segundos | integer | required | — |
| cadencia | varchar(40) | opcional | — |
| observacoes | text | opcional | — |
| exercicio_snapshot | jsonb | required | — |

## parecer — MOD-04

Parecer independente de publicação; histórico atribuível, sem herdar aceite

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| versao_id | uuid | required | versao_ficha.id |
| instrutor_id | uuid | required | funcionario.usuario_id |
| estado | varchar(20) | required | — |
| motivo | text | opcional | — |
| criado_em | timestamptz | required | — |

## documento — MOD-05

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| catalogo_id | varchar(40) | required unique | — |
| titulo | text | required | — |
| origem_url | text | required | — |
| licenca | text | required | — |

## documento_versao — MOD-05

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| documento_id | uuid | required | documento.id |
| sha256 | char(64) | required | — |
| idioma | varchar(12) | required | — |
| arquivo_ref | text | required | — |
| estado | varchar(25) | required | — |
| aprovado_por | uuid | opcional | usuario.id |
| aprovado_em | timestamptz | opcional | — |
| revision | integer | required | — |

## ingestao — MOD-05

Unicidade doc_versao+config_hash; reindexação é nova configuração/coleção

Unicidades: documento_versao_id+config_hash.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| documento_versao_id | uuid | required | documento_versao.id |
| config_hash | char(64) | required | — |
| estado | varchar(25) | required | — |
| iniciada_em | timestamptz | required | — |
| concluida_em | timestamptz | opcional | — |

## fragmento — MOD-05

Texto/vetor e metadados pesquisáveis no Qdrant; PG controla aprovação/proveniência

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| ingestao_id | uuid | required | ingestao.id |
| pagina_inicio | integer | required | — |
| pagina_fim | integer | required | — |
| secao | text | opcional | — |
| texto_hash | char(64) | required | — |
| vetor_id | uuid | required unique | — |
| colecao | varchar(100) | required | — |

## conversa — MOD-06

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| criada_em | timestamptz | required | — |

## mensagem — MOD-06

Idempotência por conversa+request_id+papel; histórico não é contexto ilimitado

Unicidades: conversa_id+request_id+papel.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| conversa_id | uuid | required | conversa.id |
| request_id | uuid | required | — |
| papel | varchar(20) | required | — |
| texto | text | required | — |
| estado | varchar(25) | required | — |
| criada_em | timestamptz | required | — |

## execucao_ia — MOD-06

Única por cliente+chave; sem duplicar conteúdo de ficha excluída

Unicidades: cliente_id+idempotency_key.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| idempotency_key | varchar(100) | required | — |
| entrada_hash | char(64) | required | — |
| finalidade | varchar(25) | required | — |
| estado | varchar(25) | required | — |
| onboarding_id | uuid | opcional | onboarding_versao.id |
| versao_base_id | uuid | opcional | versao_ficha.id |
| versao_publicada_id | uuid | opcional | versao_ficha.id |
| config_version | integer | required | — |
| modelo | varchar(100) | required | — |
| prompt_version | varchar(60) | required | — |
| iniciada_em | timestamptz | required | — |
| terminada_em | timestamptz | opcional | — |

## triagem — MOD-06

Três estados de domínio, falhas técnicas pertencem à execução

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| execucao_id | uuid | required unique | execucao_ia.id |
| onboarding_id | uuid | required | onboarding_versao.id |
| resumo | jsonb | required | — |
| regra_version | integer | required | — |
| estado | varchar(35) | required | — |
| motivos | jsonb | required | — |

## etapa_ia — MOD-06

Dados de consumo sem chain-of-thought

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| execucao_id | uuid | required | execucao_ia.id |
| tipo | varchar(25) | required | — |
| estado | varchar(25) | required | — |
| chamadas | integer | required | — |
| tokens_entrada | integer | opcional | — |
| tokens_saida | integer | opcional | — |
| duracao_ms | integer | opcional | — |

## evidencia_execucao — MOD-06

IDs de fontes reais, sem copiar dados privados na literatura

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| execucao_id | uuid | required | execucao_ia.id |
| fragmento_id | uuid | required | fragmento.id |
| finalidade | varchar(25) | required | — |

## plano — MOD-08

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| nome | varchar(100) | required | — |
| duracao_dias | integer | required | — |
| modalidade | varchar(80) | required | — |
| limite_acessos | integer | opcional | — |
| janela_limite | varchar(25) | opcional | — |
| preco_base | numeric(12,2) | opcional | — |
| ativo | boolean | required | — |

## matricula — MOD-08

Fim civil inclusive no fuso da academia; sem FK obrigatória para pagamento

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| plano_id | uuid | required | plano.id |
| atendente_id | uuid | required | funcionario.usuario_id |
| inicio | date | required | — |
| fim | date | required | — |
| estado | varchar(20) | required | — |
| modalidade_contratada | varchar(80) | required | — |
| limites_snapshot | jsonb | required | — |

## biometria — MOD-07

Referência ativa única; substituição descarta foto/exemplo antigo conforme contrato

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required unique | cliente.usuario_id |
| subject_externo | varchar(120) | required unique | — |
| image_id | varchar(120) | required | — |
| estado | varchar(25) | required | — |
| cadastrada_por | uuid | required | funcionario.usuario_id |
| criada_em | timestamptz | required | — |

## evento_acesso — MOD-07

Unicidade origem+event_id; desconhecido tem cliente nulo

Unicidades: origem+event_id_externo.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| origem | varchar(80) | required | — |
| event_id_externo | varchar(120) | required | — |
| cliente_id | uuid | opcional | cliente.usuario_id |
| tipo | varchar(25) | required | — |
| ocorrido_em | timestamptz | required | — |
| payload_hash | char(64) | required | — |

## decisao_acesso — MOD-07

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| evento_id | uuid | required | evento_acesso.id |
| matricula_id | uuid | opcional | matricula.id |
| resultado | varchar(15) | required | — |
| motivo | varchar(80) | required | — |
| criada_em | timestamptz | required | — |

## catraca_comando — MOD-07

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| decisao_id | uuid | required unique | decisao_acesso.id |
| request_id | uuid | required unique | — |
| direcao | varchar(15) | required | — |
| expira_em | timestamptz | required | — |
| estado | varchar(25) | required | — |

## presenca — MOD-07

Uma presença aberta por cliente, apenas passagem simulada confirmada muda lotação

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| entrada_evento_id | uuid | required unique | evento_acesso.id |
| saida_evento_id | uuid | unique | evento_acesso.id |

## cobranca — MOD-08

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cliente_id | uuid | required | cliente.usuario_id |
| matricula_id | uuid | opcional | matricula.id |
| competencia | date | required | — |
| valor | numeric(12,2) | required | — |
| vencimento | date | required | — |
| estado | varchar(25) | required | — |

## pagamento — MOD-08

Múltiplas tentativas; confirmação financeira não cria matrícula; compra de plano exige plano_id, lançamento manual legado pode omitir

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| cobranca_id | uuid | opcional | cobranca.id |
| cliente_id | uuid | required | cliente.usuario_id |
| plano_id | uuid | opcional | plano.id |
| origem | varchar(25) | required | — |
| referencia_externa | varchar(150) | opcional | — |
| valor | numeric(12,2) | required | — |
| estado | varchar(25) | required | — |
| confirmado_em | timestamptz | opcional | — |

## aula_ocorrencia — MOD-09

Reserva/capacidade não entra no primeiro escopo sem GATE-07

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| nome | varchar(120) | required | — |
| inicio | timestamptz | required | — |
| fim | timestamptz | required | — |
| descricao | text | opcional | — |
| estado | varchar(25) | required | — |

## notificacao — MOD-12

Unique destinatario+evento+canal; sem anamnese no payload

Unicidades: destinatario_id+evento_id+canal.

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| destinatario_id | uuid | required | usuario.id |
| evento_id | uuid | required | — |
| canal | varchar(25) | required | — |
| tipo | varchar(25) | required | — |
| estado | varchar(25) | required | — |
| tentativas | integer | required | — |
| criada_em | timestamptz | required | — |
| atualizada_em | timestamptz | required | — |
| lida_em | timestamptz | opcional | — |

## auditoria — MOD-12

Sem exclusão pelo autor; metadados mínimos, não cópia de ficha/foto

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| ator_id | uuid | opcional | usuario.id |
| acao | varchar(80) | required | — |
| recurso_tipo | varchar(60) | required | — |
| recurso_id | uuid | opcional | — |
| motivo | text | opcional | — |
| correlation_id | uuid | required | — |
| ocorrido_em | timestamptz | required | — |

## outbox — MOD-12

Publicação de domínio e evento na mesma transação; consumidor idempotente

| Campo | Tipo | Regras | Referência |
|---|---|---|---|
| id | uuid | pk | — |
| evento_tipo | varchar(80) | required | — |
| schema_version | integer | required | — |
| payload | jsonb | required | — |
| estado | varchar(25) | required | — |
| criado_em | timestamptz | required | — |
| entregue_em | timestamptz | opcional | — |
