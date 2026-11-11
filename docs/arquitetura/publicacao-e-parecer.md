# Publicação, parecer posterior e retenção

TRN-03 implementa o fluxo manual do MOD-04. Em **Meus clientes → Fichas de
treino**, o instrutor salva um rascunho e abre **Publicar ou avaliar a versão
salva**. A tela mostra a prescrição persistida e o acesso às avaliações/onboarding.
O instrutor confirma que conferiu suas restrições e solicita a publicação.

## Validação e publicação

O backend revalida designação, autoria, revisão do rascunho, onboarding atual,
avaliação vinculada, versão-base, dias preenchidos, catálogo e alternativa completa
de equipamentos. Alteração do snapshot do catálogo exige salvar novamente.
A confirmação pertence ao instrutor e ao conteúdo salvo. Não existe inferência
de saúde a partir de campos ausentes. O fluxo manual não acrescenta bloqueio
clínico implícito, seguindo a [triagem acadêmica](../requisitos/onboarding-e-triagem.md).

A conferência técnica persiste em `validacao_ficha`, com revisão, responsável,
solicitação e instante UTC. Essa validação estrutural e de referências não é
parecer profissional nem avaliação clínica. O contrato de publicação manual
recusa origem IA; AI-03 terá de integrar a triagem/evidências/validações do
MOD-06 antes de publicar. Esta entrega não implementa nem libera geração por IA.

Na mesma transação, a vigente anterior passa a SUBSTITUIDO, o rascunho passa a
PUBLICADO/vigente, a retenção é aplicada e o aviso interno/auditoria são
persistidos. A versão começa PENDENTE. Consulta própria já funciona pela API,
inclusive sem responsável atual. A consulta móvel e a exportação foram entregues em [TRN-04](ficha-do-cliente.md).
O chat segue nos cartões AI.

## Parecer e fila

**Avaliar fichas publicadas** abre a fila paginada de versões retidas ainda sem
parecer conclusivo. Ela usa a designação vigente e não depende do sucesso de
e-mail. Trocar/remover o responsável retira a autorização do anterior; o novo
designado vê a pendência existente. Nenhum outro funcionário ganha acesso.

O parecer conclusivo por versão é ACEITO ou REJEITADO, com ID, instrutor,
instante UTC e motivo obrigatório na rejeição. É imutável. Corrigir a prescrição
parte de uma cópia para nova versão no editor; o novo conteúdo não herda aceite.
O formulário mostra essa regra antes de registrar. Replay com a mesma solicitação
e conteúdo retorna o registro anterior; decisão conflitante retorna 409.

Rejeitar a vigente mantém sua consulta, prescrição e motivo. Se uma versão
posterior também for rejeitada, expirar o conteúdo das rejeitadas anteriores com
motivo REJEITADA_ANTERIOR. Ordenar pela numeração das versões impede que um parecer
atrasado elimine a rejeitada mais recente. Aceitar/publicar outra versão não
dispara esse expurgo específico.

## Retenção e concorrência

Publicar além de quinze versões completas expira as mais antigas por LIMITE_15,
incluindo aceitas/rejeitadas, preservando sempre a vigente. Rascunhos não contam.
Ambas as regras de retenção marcam a exclusão e removem itens/dias; mantêm versões,
numeração, validações, pareceres e auditoria. Consultar uma expirada retorna dias
vazios. As rotas são `no-store`; leituras futuras de chat/exportação devem usar o
contrato `published_workout` e não conservar cópias de conteúdo expirado.

O registro de execuções de treino não foi implementado e não é criado neste
cartão. Seus snapshots futuros continuam independentes da prescrição expurgável;
nenhuma rotina desta entrega remove outros históricos.

Bloqueios por cliente, compatíveis com designação e onboarding, serializam criação,
publicação e parecer. O índice parcial garante uma vigente. Publicações de
rascunhos concorrentes com a mesma base produzem um sucesso e um conflito; replay
da mesma publicação não promove novamente a versão. Falha transacional desfaz
a troca, a retenção, o parecer e seus efeitos relacionados.

## API JSON v1

Prefixo de cliente: `/api/v1/treinos/clientes/{client_id}`.

| Método e sufixo | Contrato |
|---|---|
| GET /versoes/{version_id}/revisao | Instrutor designado consulta conteúdo salvo, parecer e validação separados. |
| POST /versoes/{version_id}/publicacao | `solicitacao_id`, `revisao`, `onboarding_id`, `versao_base_id` e `restricoes_conferidas=true`. Retorna treino e estado do aviso por e-mail. |
| POST /versoes/{version_id}/parecer | `solicitacao_id`, `estado` ACEITO/REJEITADO e `motivo` opcional no aceite. |
| POST /versoes/{version_id}/aviso | Reenvio explícito com `tentativa_anterior` null para primeiro envio, ou 1/2 para repetir falha; respeita idempotência e limite do MOD-12. |
| GET /atual | Cliente próprio/instrutor designado consulta a vigente ou `null`. |
| GET /publicadas/{version_id} | Mesma autorização; rascunho retorna 404, expirada não retorna conteúdo. |

A fila fica em `GET /api/v1/treinos/pendentes?pagina=1&limite=20`.
Mutações exigem sessão, origem e CSRF. IDs de outro contexto não concedem acesso.
Os schemas são expostos pelo OpenAPI.

## Avisos e limites

O MOD-02 fornece um contato tipado do instrutor ativo, sem acesso direto do treino
às suas tabelas. A integração usa pequenos acréscimos nos contratos de designação
e pessoas. No frontend, rotas e links de entrada integram a nova feature de revisão
ao editor existente; o restante da funcionalidade fica em training-review.

Após o commit, MOD-12 tenta SMTP local com mensagem genérica, sem dados de saúde
ou prescrição. Falha/resultado incerto fica registrado e não remove publicação ou
pendência. O reenvio é explícito, até três tentativas, e replay não duplica envio.
Uma falha técnica após o commit pode exigir consultar o estado salvo. Não existe
worker nem envio automático contínuo neste cartão.

A migration 0011 cria a validação e protege validações/pareceres contra UPDATE
ou DELETE. O índice parcial limita a um parecer conclusivo por versão e a constraint
exige motivo em rejeições. A migration 0010 permanece intacta.

## Integração AI-03

[Publicação por IA](geracao-persistente.md) usa o contrato interno
ValidatedGeneration/treinos, sem passar pelo atalho de publicação manual.
Reutiliza validação, retenção, pendência/aviso e parecer posterior do mesmo domínio.
Explicação da versão é imutável; o expurgo remove-a junto à prescrição. Não existe
cópia da ficha na execução IA que possa restaurar conteúdo expirado.

## Acompanhamento AI-04

[Interface e fontes](solicitacao-e-acompanhamento-ia.md) mostram contexto da
geração e mudanças posteriores, sem criar parecer paralelo. No aviso existente,
tentativa_anterior=null permite envio inicial; 1/2 solicita repetir a tentativa
falha exata. A tela lê o ledger atual antes do reenvio.
