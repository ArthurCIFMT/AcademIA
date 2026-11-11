# Solicitação e acompanhamento de geração — AI-04

## Entrega e composição

A rota /area/cliente/treino-ia permite solicitar, consultar e cancelar geração.
A requisição permanece identificada na URL, sem salvar anamnese, ficha, credencial
ou contexto em localStorage. Recarregar, retomar a URL ou focar a janela apenas
consulta; nunca dispara outra geração automaticamente. Nova geração é uma ação
explícita com outro UUID. O backend resolve o titular pela sessão.

AI-03 continua responsável por gerar/publicar e TRN-03 por parecer, retenção e
aviso. Não há outra publicação ou entidade de aprovação neste cartão.
[Contrato de geração](geracao-persistente.md), [parecer](publicacao-e-parecer.md)
e [schemas portáveis](../requisitos/schemas/acompanhamento-ia-v1.schema.json).

Ajustes equivalentes necessários: AppRoutes.tsx registra rota/link e mantém a
sessão da edição; notifications/review_status.py é uma porta de consulta ao aviso
que pertence ao MOD-12, sem acesso cruzado às suas tabelas. O envio já existente
do MOD-04 recebe modo interno para geração própria, revalidando conta/contexto e
origem IA; esse modo não é parâmetro REST. Nenhuma dependência ou migration nova.

## Experiência do cliente

A tela distingue andamento, ficha publicada, bloqueio, dados insuficientes,
abstenção/conflito, falha técnica, saída inválida, limite, timeout e cancelamento.
Há link para conferir onboarding e para consultar fichas já existentes. Ausência
não é interpretada como saudável. Nenhum laudo ou aceite prévio foi acrescentado.

POST ocorre somente por clique explícito, com solicitacao_id e CSRF. A consulta
em andamento repete GET a cada dois segundos; ao encerrar ou desmontar, interrompe
essa consulta. Cancelar usa o DELETE existente; interromper a requisição do
navegador não equivale a cancelar a execução no servidor. Em erro de transporte,
orientar consulta do estado salvo; não abrir outro POST automaticamente.
Identificador inválido não é enviado. Troca de usuário desmonta estado anterior;
respostas antigas não podem preencher uma solicitação diferente.

A ficha retornada pelo MOD-04 é exibida por dias/itens, com explicação, carga,
cadência, séries/repetições/intervalo, parecer, responsável, motivo e data.
Parecer PENDENTE/REJEITADO não bloqueia consulta de conteúdo ainda retido. Expurgado
não reaparece via execução: a tela mostra metadados/aviso e link para histórico.
Sem instrutor, indicar pendência de designação e manter acesso à ficha.
O chat público continua em AI-05; esta entrega não o declara implementado.

Fontes mostram título/link seguro, idioma, página/linhas e seção. IDs e versão
documental ficam em detalhe expandível. Texto não é interpretado como HTML;
URLs aceitam somente http/https. Fontes e contexto são bibliográficos/metadados:
não devolver resumo completo, anamnese, mensagens ou resposta bruta do modelo.

## Acompanhamento e revisão

| GET /api/v1/ia/fichas/... | Permissão/resultado |
|---|---|
| execucoes/{id}/acompanhamento | Somente ator da execução, cliente ativo; recibo e contexto/ficha publicada quando houver |
| clientes/{client_id}/versoes/{version_id}/contexto | Cliente próprio ou instrutor atualmente designado; fontes, versão e estado atual do contexto da ficha IA |

Ambas usam no-store. Sem sessão: 401; contexto proibido: 403; execução alheia/
inexistente ou versão sem geração: 404 conforme o contrato. O administrador não
recebe permissão clínica por seu papel. Perfil/designação são revalidados no
backend. Não há seleção de cliente ou conteúdo por parâmetros do modelo.

O instrutor usa a tela de revisão existente, com fontes/contexto, link para
onboarding/avaliações e o mesmo formulário de aceitar/rejeitar/copiar para edição.
Parecer identifica a versão e é imutável. Trocar instrutor retira acesso do anterior;
o designado atual vê a pendência pela fila, independentemente de e-mail antigo.

Mudança posterior de onboarding, catálogo/recursos, política ou aprovação das fontes
aparece como pendência/alerta de contexto atual, sem reescrever a ficha ou zerar
parecer já concluído. Não criar outro aceite. A publicação já revalida antes do
commit em AI-03. Referência a fonte revogada é histórica e não autoriza novo uso.

## Um único fluxo de aviso

Após uma geração nova publicada, chamar o envio existente de TRN-03 fora da
transação de publicação, com o mesmo evento uuid5(versão, publicacao).
Ausência de instrutor não falha a geração. O ledger do MOD-12 reserva e limita
tentativas; replay não reenvia automaticamente e GET nunca envia/cria aviso.
Falha de SMTP mantém publicação/fila e é apresentada como FALHOU/INCERTO.

No endpoint de aviso já existente, tentativa_anterior=null solicita o primeiro
envio quando ainda não há ledger; 1/2 pede repetição explícita da tentativa falha
correspondente, até três tentativas. Repetir a mesma ação não envia outra mensagem.
O instrutor vê a tentativa realmente salva, inclusive ao abrir a página depois.
A consulta ao aviso acompanha o destinatário atualmente designado, sem expor e-mail,
corpo ou credenciais, e sem recriar aviso de um destinatário anterior.

## Verificação

[Comandos e resultados](../testes/comandos.md#acompanhamento-e-interface-ai-04).
Testes React verificam ações, retomada, bloqueios, cancelamento e limpeza de acesso.
Integrações PostgreSQL/Qdrant exercitam fontes reais da fixture, registro único,
falha/reenvio SMTP controlado, designação, parecer e endpoints autenticados.
O contrato Groq e o transporte do aviso são controlados nas integrações novas;
qualidade/latência reais do provedor ficam em AI-06, e o E2E do MVP em TST-01.
