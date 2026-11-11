# Consulta e exportação da ficha pelo cliente

TRN-04 acrescenta leitura e exportação ao MOD-04 em
`backend/app/modules/training/` e `frontend/src/features/my-training/`.
A integração de entrada altera apenas a rota e o link na área do cliente em
`frontend/src/app/AppRoutes.tsx`, caminho equivalente necessário para a tela.
As tabelas e regras de publicação/retenção existentes são reutilizadas;
nenhuma migration ou dependência nova foi necessária.

## Fluxo da interface

**Área do cliente → Meus treinos** abre a ficha vigente. A prescrição aparece
em cartões por dia, na ordem salva, com exercício/descrição, séries, repetições,
carga, intervalo, cadência e observações. Origem e identificação do autor são
exibidas. Datas usam pt-BR e America/Sao_Paulo; carga usa vírgula decimal.

O parecer PENDENTE, ACEITO ou REJEITADO aparece separado, com motivo,
responsável e data quando disponíveis. Todos permitem consulta e exportação.
A ausência de responsável atual também não bloqueia a consulta própria.
O chat continua sendo uma entrega dos cartões AI.

O seletor oferece apenas versões publicadas completas retidas, até quinze
incluindo a vigente. Rascunhos e conteúdo expirado ficam fora da lista.
Ao atualizar ou retornar à janela, a tela busca os dados novamente.
Versão removida deixa de ser exibida e oferece retorno à vigente.
Erros de consulta limpam a versão mostrada; estado vazio orienta quem
ainda não possui ficha publicada. Troca de sessão desmonta o contexto e
cancela requisições/downloads pendentes.

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
