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
ONB-04. A interface do cliente entra em ONB-03 e o convite em ONB-01.

O teste de migration do PES-03 continua verificando a revisão 0005. A checagem
global do Alembic acompanha a revisão 0006 no teste de ONB-02.
