# Planos e matrículas — MEM-01

MOD-08 mantém os planos da academia e os períodos contratados pelo cliente.
Na área administrativa, **Gerenciar planos** permite criar, editar e desativar
planos. Na área de atendimento, **Matrículas** permite buscar o cliente pelo
cadastro existente, consultar o histórico e registrar o próximo período.
Administrador e atendente usam seus respectivos papéis. Uma conta com ambos
os papéis pode operar nas duas áreas.

## Regras aplicadas

- Plano possui nome, modalidade, duração positiva em dias, estado ativo/inativo
  e limite diário opcional. Limite ausente representa entradas sem teto diário.
- Somente o atendente ativo pode matricular cliente com perfil habilitado e
  conta ativa ou convidada. A autenticação do aluno segue os estados da conta.
- O término é calculado como início mais duração menos um dia. Os dois extremos
  são inclusivos, no dia civil de São Paulo. A renovação cria outro registro e
  pode começar a partir do dia seguinte ao último término, inclusive de uma
  matrícula futura. As datas podem ser consultadas no histórico.
- Modalidade, janela e limite ficam congelados em cada matrícula. Editar ou
  inativar o plano preserva seus efeitos nos períodos já registrados.
- Matrícula e renovação independem de pagamento, comprovante e serviço financeiro.
  O formulário do atendente registra o período com a revisão do plano exibido.
- A transação serializa inscrições concorrentes pelo cliente por meio do serviço
  de pessoas e mantém a revisão do plano estável durante a contratação. A escrita
  e a auditoria do responsável são atômicas. Repetir o UUID de solicitação do
  mesmo atendente, cliente, plano e início devolve a matrícula registrada.
- O histórico expõe estado persistido (`ATIVA` ou `ENCERRADA`) e situação
  calculada (`FUTURA`, `VIGENTE`, `VENCIDA` ou `ENCERRADA`). O calendário
  deriva a situação sem atualizar cada registro na virada do dia.

## REST e JSON

Rotas sob `/api/v1`. Operações de escrita exigem sessão e CSRF. Listas usam
`itens`, `pagina`, `limite` e `total`. Datas são ISO 8601 `AAAA-MM-DD`.

| Método e rota | Permissão | Operação |
|---|---|---|
| `GET /admin/planos` | Administrador | Lista planos ativos e inativos |
| `POST /admin/planos` | Administrador | Cria plano (201) |
| `PUT /admin/planos/{plan_id}` | Administrador | Edita os dados e o estado do plano |
| `GET /atendimento/planos` | Atendente | Lista planos ativos |
| `GET /atendimento/clientes/{client_id}/matriculas` | Atendente | Lista histórico, começando pelo último período |
| `POST /atendimento/clientes/{client_id}/matriculas` | Atendente | Matricula ou renova (201) |

Planos recebem `nome`, `modalidade`, `duracao_dias`, `limite_acessos` e
`ativo`, com `solicitacao_id` UUID na criação e `revisao` na edição.
Matrículas recebem `solicitacao_id`, `plano_id`, `plano_revisao` e `inicio`.
O backend obtém o responsável da sessão e devolve a modalidade contratada e o
objeto `limites_snapshot` com `limite_acessos` e `janela_limite`. Quando
limitada, a janela é `DIA_CIVIL`. Sem teto, os dois campos são nulos. Plano
inativo, revisão superada e período conflitante retornam 409.

## Porta para acesso

`app.modules.memberships.service.valid_membership(db, client_id, at=instante)`
recebe um instante com fuso e devolve `ValidMembership` com ID, modalidade e
limites contratados, ou `None` quando não há matrícula ativa no dia consultado.
A autorização de entrada combina essa consulta com conta, identidade,
modalidade e uso diário no motor do ACS-03. A contagem das passagens confirmadas
pertence ao módulo de acesso e continua por cliente e dia civil, inclusive em
caso de renovação. [Decisões do GATE-08](preparacao-gate-08.md).
