# Fichas manuais e rascunhos

O instrutor designado abre **Meus clientes → Fichas de treino** e monta
dias e exercícios. O rascunho recebe origem MANUAL, autor, número crescente,
onboarding de referência e, opcionalmente, uma avaliação desse mesmo
onboarding e cliente. A gravação funciona com os serviços de IA indisponíveis.

## API

| Rota | Operação |
|---|---|
| GET /api/v1/treinos/clientes/{client_id}/contexto | Retorna referências do onboarding, avaliações, catálogo elegível e equipamentos para o editor. |
| GET /api/v1/treinos/clientes/{client_id}/versoes | Lista metadados com `pagina` e `limite`. |
| GET /api/v1/treinos/clientes/{client_id}/versoes/{version_id} | Consulta uma versão dentro do cliente autorizado. |
| POST /api/v1/treinos/clientes/{client_id}/rascunhos | Cria rascunho com `solicitacao_id`, `versao_base_id`, `onboarding_id`, `avaliacao_id` e `dias`. |
| PUT /api/v1/treinos/clientes/{client_id}/rascunhos/{version_id} | Atualiza rascunho do próprio autor com `revisao` e o conteúdo completo. |

Cada dia possui título e itens ordenados pela posição no JSON. Cada item
informa exercício, alternativa escolhida de equipamentos, séries,
repetições, carga opcional, intervalo, cadência opcional e observações.
A API exige origem e CSRF em mutações. A designação é revalidada dentro
da transação, com bloqueio compatível com a troca de responsável.
Um sucessor pode copiar um rascunho anterior para uma nova versão com
a própria autoria.

A mesma chave de criação e o mesmo conteúdo recuperam a versão original
na revisão inicial. Entrada divergente ou revisão desatualizada retorna
409. Um onboarding superado ou recurso que deixou de ser elegível
também exige conferência. A tela mantém a edição diante de falha de rede
e oferece recarga das opções.

## Validações técnicas

Os limites do formulário são até sete dias, trinta itens por dia, título
de sessenta caracteres, séries entre 1 e 100 e intervalo entre 0 e 3600
segundos. A carga é decimal não negativa de até duas casas decimais e
999999,99 kg. Repetições e cadência têm até quarenta caracteres.
Esses limites tratam armazenamento e entrada do protótipo. O instrutor
preenche os valores da prescrição. Um rascunho pode ter dias sem itens
enquanto é montado.

O backend revalida o exercício e a alternativa por contrato do catálogo,
guardando no item o nome, a descrição, o grupo muscular, a revisão do
catálogo e os IDs dos equipamentos utilizados. Edições posteriores no
catálogo preservam esses snapshots. A gravação usa a ordem dos exercícios
para adquirir os bloqueios de recursos.

## Versões, publicação e exclusão de conteúdo

A migration 0010 separa versão, dias, itens e parecer. Acrescenta revisão
otimista e chaves estrangeiras que vinculam onboarding, avaliação e
versão-base ao mesmo cliente. Alterações de rascunho geram auditoria.
A referência de avaliação é fornecida pelo contrato do MOD-03.

O conteúdo de uma versão publicada é protegido por gatilhos. A edição
parte de uma cópia para novo rascunho. O registro de versão conserva
autoria, numeração e proveniência. `retention_candidates` seleciona
conteúdo que excede as quinze versões publicadas completas, incluindo
a vigente na retenção e desconsiderando rascunhos.

TRN-03 implementa [publicação, retenção e pareceres](publicacao-e-parecer.md)
utilizando esses invariantes. O expurgo marca conteúdo
expirado com motivo e data, remove itens antes dos dias e preserva os
metadados. Consultas de conteúdo expirado retornam a identificação e
uma lista vazia de dias. A estrutura preserva referências futuras de
execuções de treino por versão.
