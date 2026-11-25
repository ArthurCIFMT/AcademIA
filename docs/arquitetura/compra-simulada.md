# Compra simulada de plano — FIN-02

Em **Administração → Gerenciar planos**, o administrador informa o preço
simulado em reais. Deixar o campo vazio mantém o plano disponível para
matrícula manual, de acordo com seu estado. No catálogo da simulação aparecem
apenas planos ativos com preço, incluindo os de valor zero.

Em **Cliente → Simular compra de plano**, ou pelo link de **Minhas cobranças**,
o cliente escolhe o plano e o resultado de demonstração: confirmado, pendente
ou recusado. O backend lê o preço do cadastro e grava um recibo com plano,
nome e valor no instante da operação. O histórico continua consultável após
alteração de preço ou inativação do plano.

Cada recibo usa a tabela de pagamentos já existente e a origem `SIMULACAO`.
Somente um resultado confirmado tem data de pagamento e confirmação. Cada
simulação registra o resultado escolhido uma vez. Se a demonstração precisar
de outro resultado, o cliente inicia nova simulação. Cobranças lançadas pelo
administrador continuam consultáveis separadamente. A compra simulada gera
o próprio recibo financeiro e a matrícula continua a cargo do atendente.

## Contratos REST

As rotas abaixo usam `/api/v1/cliente/compra-simulada` como base. A sessão
identifica o cliente. A resposta usa `Cache-Control: no-store` e a escrita
exige CSRF.

| Método e sufixo | Operação |
|---|---|
| `GET /planos` | Oferta paginada de planos ativos com preço. |
| `GET` | Histórico paginado do cliente autenticado. |
| `GET /{purchase_id}` | Detalhe de recibo próprio. ID ausente ou de terceiro retorna 404. |
| `POST` | Grava o resultado da simulação. Recebe `solicitacao_id`, `plano_id` e `resultado`. |

A criação devolve 201. O mesmo ID e conteúdo devolvem 200 com o recibo original.
Reutilizar um ID com dados divergentes ou selecionar um plano que deixou de
estar disponível retorna 409. Valores são strings decimais e datas de eventos
usam UTC. O painel converte o instante para São Paulo.

A revisão `0027` acrescenta o nome do plano no recibo, o instante da simulação,
uma constraint de estados e um índice de histórico por cliente. A reversão
preserva lançamentos anteriores e interrompe se já houver recibos simulados,
para proteger os campos do histórico.
