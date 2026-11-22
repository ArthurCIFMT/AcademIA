# Consulta e exportação da ficha pelo cliente

TRN-04 acrescenta leitura e exportação ao MOD-04 em
`backend/app/modules/training/` e `frontend/src/features/my-training/`.
A integração de entrada altera apenas a rota e o link na área do cliente em
`frontend/src/app/AppRoutes.tsx`, caminho equivalente necessário para a tela.
As tabelas e regras de publicação/retenção existentes são reutilizadas;
nenhuma migration ou dependência nova foi necessária.

## Fluxo da interface

**Área do cliente → Meus treinos** abre a ficha vigente no primeiro dia. A
navegação permite escolher outro dia da mesma versão em memória, sem chamada
à API. A seleção move o foco para o título do dia. A prescrição mostra
exercício, descrição, séries, repetições, descanso, carga, cadência, recursos
e observações na ordem salva. Origem e dados de autoria ficam junto ao
parecer. Datas usam pt-BR e America/Sao_Paulo. A carga usa vírgula
decimal e distingue zero de ausência.

O parecer PENDENTE, ACEITO ou REJEITADO aparece separado, com motivo,
responsável e data quando disponíveis. Todos permitem consulta e exportação.
A ausência de responsável atual também não bloqueia a consulta própria.
O chat continua sendo uma entrega dos cartões AI.

O painel **Histórico de versões** oferece até quinze versões publicadas
completas, incluindo a vigente. Consultar uma versão histórica mantém
visível a identificação da vigente e a ação de retorno. Rascunhos e
conteúdo expirado ficam fora da lista. A interface revalida ao atualizar
ou retornar à janela. Se uma versão selecionada expirar, inclusive entre
a listagem e a leitura, a ficha sai da tela e a exportação deixa de estar
disponível. Erros de consulta limpam a versão mostrada. Estado vazio orienta
quem ainda não possui ficha publicada. Troca de sessão desmonta o contexto
e cancela requisições e downloads pendentes.

Em ficha de IA, **Ver fontes da ficha** consulta sob demanda o contrato
de [contexto da versão](solicitacao-e-acompanhamento-ia.md#acompanhamento-e-revisão).
Uma fonte alterada é identificada separadamente do parecer. Uma falha
técnica na consulta das fontes mantém a prescrição disponível. Se o
contexto indicar expurgo ou recusa de acesso, a interface retira a ficha
e cancela o download ainda em andamento.

## Equipamentos

A consulta resolve os IDs dos equipamentos utilizados em cada item pelo contrato
`read_resources` do MOD-10, na mesma transação de leitura. Retorna nome e
disponibilidade cadastral/operacional atuais, com instante da consulta.
Recurso ausente/inativo/não operacional é sinalizado. A prescrição e seus
snapshots permanecem inalterados e nenhum exercício é trocado automaticamente.

Dispensa explícita de equipamento é apresentada como tal. Não inferir dispensa
a partir de vínculo faltante. A autorização e os recursos seguem as mesmas
regras na consulta e na exportação.

## REST e JSON v1

Prefixo: `/api/v1/treinos/clientes/{client_id}`.

| Método e sufixo | Resultado |
|---|---|
| GET /publicadas | `schema_version=1`, `versao_vigente_id` e até 15 resumos, com parecer por versão. |
| GET /publicadas/{version_id}/ficha | Conteúdo consolidado: `ficha`, `parecer`, `validacao`, `equipamentos`, `consultado_em` e `schema_version=1`. |
| GET /publicadas/{version_id}/exportacao | Mesmo contrato em attachment JSON com nome gerado por número e UUID da versão. |

O cliente consulta somente seu contexto; o instrutor precisa de designação
vigente. Perfil administrativo não concede acesso a prescrições privadas.
A autorização ocorre no backend antes de carregar conteúdo e é repetida
em cada exportação. Sessão ausente retorna 401, acesso indevido retorna 403,
versão desconhecida/de outro cliente/rascunho/expirada retorna 404 dentro
do contexto autorizado. Não retornar conteúdo por URL direta após retenção.

As respostas usam `Cache-Control: no-store`. O download usa a sessão atual e
uma nova requisição à API, sem reconstruir o arquivo a partir da tela.
A API entrega JSON, `Content-Disposition: attachment` e `nosniff`.
O frontend libera a URL temporária do arquivo depois de iniciar o download.
Recusa por autorização/expiração também limpa a ficha anteriormente exibida.

As rotas de metadados de TRN-03 continuam preservando auditoria de versões
expiradas com dias vazios. As novas rotas de ficha/exportação exigem conteúdo
retido. Não alterar a retenção nem remover pareceres/validações históricos.

## Evidências

[Testes e roteiro de navegador](../testes/comandos.md#consulta-móvel-e-exportação-do-treino).
A validação usa PostgreSQL real de teste, clientes sintéticos, frontend React,
FastAPI e Edge em 390 px. O esquema temporário é removido ao final.
