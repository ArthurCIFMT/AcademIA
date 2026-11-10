# Persistência do onboarding

ONB-02 usa o ponto de composição `backend/app/main.py` para montar a API.
`backend/app/modules/people/onboarding_directory.py` fornece o bloqueio do
cadastro e a data de nascimento pelo contrato de pessoas. O MOD-03 guarda
rascunhos, versões concluídas e avaliações no seu próprio schema de domínio.
A migration registra as tabelas no ambiente Alembic.

## API da própria conta

| Rota | Operação |
|---|---|
| GET /api/v1/onboarding/meu | Retorna o rascunho atual e a última versão concluída, cada qual como objeto ou `null`. |
| PATCH /api/v1/onboarding/meu/rascunho | Recebe `versao_base`, `revisao` e `dados` parciais. Cria ou atualiza o rascunho. |
| POST /api/v1/onboarding/meu/conclusao | Recebe `versao_base` e `revisao`. Valida o rascunho completo e o conclui. |
| POST /api/v1/onboarding/meu/atualizacoes | Recebe `versao_base`, `confirmado: true`, `dados` completos e a `revisao` do rascunho, se houver. Retorna 201 com a nova versão concluída. |
| GET /api/v1/onboarding/meu/versoes/{snapshot_id} | Consulta versão concluída da própria conta, inclusive histórica. |

O backend resolve o cliente pela sessão, verifica o papel efetivo e exige
origem e CSRF em mutações. Consultas e respostas com dados usam
`Cache-Control: no-store`. O cliente recebe 404 ao consultar um UUID de versão
que não está no seu escopo. As mensagens de erro da API evitam repetir
conteúdo do formulário.

## Versões e concorrência

`versao_base` é o UUID da última versão concluída. Antes da primeira
conclusão, use `null`. `revisao` corresponde ao rascunho consultado, ou
`null` ao abrir um novo. A abertura após uma conclusão copia o snapshot
anterior como base do rascunho. Cada PATCH modifica somente campos enviados.
Uma lista enviada substitui a lista inteira. O rascunho mantém a diferença
entre campo ausente, campo `null` e resposta explícita `NAO_SEI`.

Conclusão e confirmação validam o
[JSON Schema v1](../requisitos/schemas/onboarding-v1.schema.json), inclusive
as regras condicionais entre respostas e listas. Resposta `NAO_SEI` pode
concluir o formulário. A elegibilidade para IA é tratada pela triagem em
etapa própria. A transação usa o bloqueio do cadastro e compara versão e
revisão. Uma base superada retorna 409. A conclusão grava data e responsável
e congela a idade calculada pela data civil de São Paulo. O banco armazena
o instante em UTC.

A migration 0006 permite um rascunho por cliente. Os gatilhos protegem
versões concluídas e avaliações de alteração ou exclusão. O serviço
`get_snapshot` recupera um snapshot concluído pelo par cliente e versão,
após a autorização do chamador. Para triagens novas ou para reuso, o
consumidor verifica `is_current_snapshot`. A confirmação de uma nova versão
torna o resultado vinculado à versão anterior obsoleto. Abrir ou editar um
rascunho preserva a referência vigente até a conclusão.

## Avaliações

O serviço interno `append_evaluation` guarda uma entrada imutável por
avaliação com autor, data e snapshot do próprio cliente. A chave estrangeira
composta impede associar a avaliação ao snapshot de outra pessoa. A
autorização por designação e as rotas profissionais serão ligadas em
ONB-04. A interface do cliente entra em ONB-03.

O teste de migration do PES-03 continua verificando a revisão 0005. A checagem
global do Alembic acompanha a revisão mais recente no teste de ONB-02.

## Convite inicial e sessão restrita

ONB-01 acrescenta a migration 0007 e as rotas abaixo. O atendente ou
administrador autenticado usa o e-mail já vinculado ao cliente. A API exige
origem e CSRF da sessão normal para emitir ou reenviar. Só a versão inicial
editável aceita convite novo. Uma conclusão anterior retorna 409.

| Rota | Operação |
|---|---|
| POST /api/v1/onboarding/clientes/{client_id}/convite | Recebe `solicitacao_id` (UUID) e retorna 201 com o ID do convite, estado de entrega e expiração. |
| GET /api/v1/onboarding/clientes/{client_id}/convite | Consulta o último estado de entrega e a expiração. Retorna 404 se não houver convite. |
| POST /api/v1/onboarding/convite/troca | Recebe `token` em JSON, consome o link e devolve a expiração e o cookie restrito. |
| GET /api/v1/onboarding/convite/rascunho | Consulta o rascunho vinculado ao cookie. |
| PATCH /api/v1/onboarding/convite/rascunho | Recebe `revisao` e `dados` parciais. |
| POST /api/v1/onboarding/convite/conclusao | Recebe `revisao`, valida a conclusão e encerra a sessão com 204. |

A mesma chave de solicitação para o mesmo cliente recupera o resultado da
emissão sem novo envio. Uma chave nova representa reenvio explícito, revoga
o link e a sessão anteriores e preserva os dados do rascunho. O limite é de
três emissões por cliente em 48 horas. Falha SMTP fica registrada como
`FALHOU`. Se a execução parar antes de confirmar o envio, a consulta pode
mostrar `SEM_CONFIRMACAO` ou `ENVIANDO`. Nesses casos, o operador pode
solicitar reenvio com chave nova. A entrega do e-mail não conclui o onboarding.

O e-mail aponta para `/onboarding/convite#token=…` na origem configurada.
O fragmento não compõe a URL da requisição HTTP. A tela de ONB-03 lerá e
removerá o fragmento antes da troca. Se a troca falhar, a tela apresentará
o erro sem reabrir um rascunho associado a um cookie anterior.

O link é de uso único e expira após 48 horas. A troca gera outro segredo,
válido até o prazo original, em cookie HttpOnly, SameSite=Lax e Secure em
HTTPS, limitado a `/api/v1/onboarding/convite`. O backend exige a origem
configurada na troca e nas mutações restritas. Cada consulta revalida
cliente, rascunho, prazo e revogação. A sessão permite reabrir o formulário
no mesmo navegador, mesmo após recarregar a página. Link consumido,
expirado ou revogado recebe 401. Uma vez concluída a versão inicial,
a sessão perde o acesso ao rascunho. Login, consulta normal e APIs de
administração exigem a sessão geral. Os segredos são armazenados por hash.

O bloqueio do cadastro serializa troca, reenvio, edição e conclusão.
A migration limita a um convite não revogado por rascunho e exige
metadados de sessão coerentes com o consumo e o prazo do convite.
