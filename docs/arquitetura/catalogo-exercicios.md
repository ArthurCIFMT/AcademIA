# Catálogo de exercícios

Administradores e instrutores mantêm o catálogo no menu **Catálogo de exercícios**.
Cada exercício ou variação tem nome, descrição do movimento, grupo muscular,
situação ativa e um UUID estável. A unicidade usa o nome em minúsculas, sem
espaços nas pontas e com espaços internos colapsados. O nome permanece reservado
durante a inativação. Reativar atualiza o próprio registro.

## API do catálogo

| Rota | Operação |
|---|---|
| GET /api/v1/exercicios | Lista o catálogo com `pagina` e `limite`, situação, combinações e elegibilidade atual. |
| GET /api/v1/exercicios/{exercise_id} | Consulta o registro e a revisão. Inclui exercícios inativos. |
| GET /api/v1/exercicios/recursos | Lista equipamentos atualmente disponíveis no inventário para o editor. |
| GET /api/v1/exercicios/elegiveis | Lista candidatos ativos e suas alternativas completas disponíveis. |
| POST /api/v1/exercicios | Cadastra os campos do catálogo e retorna 201. |
| PUT /api/v1/exercicios/{exercise_id} | Atualiza os campos e exige a `revisao` consultada. |

A API exige sessão de administrador ou instrutor nas rotas do catálogo.
As mutações verificam origem e CSRF e registram auditoria com autoria, data e
ID do exercício. Nome duplicado ou revisão superada retorna 409. Os parâmetros
de séries, carga, descanso e ordem ficam no item da ficha.

## Disponibilidade e histórico

O JSON recebe `combinacoes` como uma lista de alternativas. Cada alternativa
contém os UUIDs dos equipamentos exigidos juntos. Uma alternativa completa
basta para a seleção. Se `dispensa_equipamento` estiver marcada, envie
`combinacoes: []`. A ausência de combinações com dispensa desmarcada deixa o
cadastro fora da seleção. Equipamentos vinculados que ficaram indisponíveis
continuam visíveis ao editar.

O MOD-04 consulta o contrato do [inventário](equipamentos.md#contrato-para-exercícios-e-ia)
para verificar os recursos. `eligible_exercises(session)` entrega candidatos
ao editor de ficha ou ao orquestrador. `require_prescribable(session, exercise_id,
equipment_ids)` exige um exercício ativo e uma alternativa completa ou
dispensa explícita. O chamador usa essa função dentro da transação de gravação
da ficha. Ela bloqueia o exercício e os equipamentos escolhidos para ordenar
a revalidação com alterações concorrentes.

A migration 0009 mantém o UUID na inativação e protege a unicidade dos nomes
e dos vínculos de cada grupo. O seed identificado como sintético fica restrito
ao banco `academia_test`.
