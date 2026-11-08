# Auditoria e eventos persistentes

FND-08 cria as tabelas `academia.auditoria` e `academia.outbox` na revisão
`0002`. A evidência guarda ator, ação, referência de recurso, motivo codificado,
correlação e instante em UTC. A revisão `0003` liga o UUID do ator ao usuário
para novos registros e preserva referências anteriores. O PostgreSQL
bloqueia alteração, exclusão e truncamento dos registros por gatilho.

O serviço interno `record_audit(session, event)` recebe a sessão da operação
de origem. O chamador confirma ou desfaz as três escritas juntas. Forneça
um UUID de evento estável para repetição. Repetir o mesmo UUID e conteúdo é
idempotente. Reutilizar o UUID com conteúdo diferente causa conflito.

A fila guarda o envelope JSON da versão 1. Os campos são tipados e limitados
a identificadores, códigos de ação, recurso e motivo, correlação e instante.
Use códigos definidos pelo backend para manter fotos, credenciais, fichas e
anamnese fora do evento.

O consumidor interno `consume_next(session, handle)` reserva uma linha
pendente com bloqueio do PostgreSQL. O callback recebe a mesma sessão para
persistir seu efeito. Ao confirmar, o evento fica entregue. Se a transação
falhar, o efeito é desfeito e o evento continua pendente para nova tentativa.
Para efeitos externos, o consumidor da integração precisa usar a chave de
idempotência do evento. O envio de avisos pertence a NTF-01.
