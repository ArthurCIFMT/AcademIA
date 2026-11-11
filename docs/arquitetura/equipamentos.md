# Equipamentos da academia

O inventário pertence ao MOD-10. Em **Administração → Gerenciar equipamentos**,
o administrador cadastra nome, situação ativa e disponibilidade operacional.
Categoria, descrição e foto são opcionais. Editar ou inativar preserva o UUID
do equipamento para os vínculos históricos. A página **Equipamentos disponíveis**
mostra a oferta atual para visitantes e clientes.

## Rotas e dados

| Rota | Operação |
|---|---|
| GET /api/v1/equipamentos | Lista equipamentos ativos e operacionais com nome, categoria, descrição e URL da foto, quando cadastrada. |
| GET /api/v1/equipamentos/{equipment_id}/imagem | Entrega a foto em PNG enquanto o equipamento está na oferta. |
| GET /api/v1/admin/equipamentos | Lista o inventário completo para administrador. |
| GET /api/v1/admin/equipamentos/{equipment_id} | Consulta o registro administrativo e sua revisão. |
| GET /api/v1/admin/equipamentos/{equipment_id}/imagem | Entrega a foto ao administrador, inclusive de equipamento inativo. |
| POST /api/v1/admin/equipamentos | Cadastra com `nome`, `ativo`, `operacional` e `solicitacao_id` (UUID). |
| PUT /api/v1/admin/equipamentos/{equipment_id} | Atualiza dados e exige a revisão consultada em `revisao`. |

As listagens aceitam `pagina` e `limite`. O limite padrão é 20 e o máximo é 100.
As mutações exigem sessão administrativa, origem configurada e CSRF. Uma revisão
superada retorna 409. Repetir o cadastro com a mesma chave e dados devolve o
registro original enquanto ele está na revisão inicial. Uma chave já utilizada
com dados diferentes retorna 409.

## Fotos

A API recebe `imagem_base64` no JSON, sem prefixo de Data URL. A atualização
preserva a foto quando o campo é omitido e remove a associação quando recebe
`null`. O backend usa Pillow para decodificar JPEG/PNG estático de até 4 MiB e
2048 px por lado. Redimensiona para até 1200 px por lado e grava PNG sem os
metadados enviados. [Documentação do Pillow](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html)

O adaptador local usa `ACADEMIA_EQUIPMENT_IMAGES_DIR`, com padrão
`uploads/equipamentos` relativo ao processo da API. O diretório contém os
arquivos de runtime e a tabela guarda a referência calculada do conteúdo.
A mesma foto normalizada reutiliza o arquivo existente. A API entrega
somente a foto associada ao equipamento consultado. Arquivos de imagens
substituídas permanecem no diretório local mesmo depois de perderem a
associação pública.

## Contrato para exercícios e IA

`available_resources(session)` lista a oferta atual. `read_resources(session, ids)`
retorna por UUID os estados de recursos existentes, inclusive os inativos.
`require_available(session, ids)` recusa UUIDs ausentes, inativos ou
indisponíveis. MOD-04 deve revalidar os IDs da alternativa escolhida na
mesma transação que publica a ficha. O bloqueio compartilhado dos
registros ordena essa validação com edições administrativas concorrentes.
MOD-04 resolve combinações de recursos e a dispensa explícita do exercício.
A disponibilidade descreve o estado do inventário. Ela independe da
ocupação momentânea do equipamento.
