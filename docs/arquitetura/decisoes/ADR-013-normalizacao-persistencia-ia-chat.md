# ADR-013 — Normalização da persistência de IA e chat

Status: ACEITA por solicitação explícita do responsável em 2026-11-19.
Escopo: otimizar a modelagem existente, fazer backup antes da mudança, preservar
os dados/requisitos e comparar o resultado com o MER original.

## Contexto

A [análise anterior](../../analises/2026-11-19-tamanho-modelagem.md) identificou
duplicações na persistência de IA e um marcador de conversa sem atributos próprios.
O modelo completo descrevia 43 tabelas/335 colunas; o MVP físico tinha 32/262.
Diminuir essa contagem não é motivo para fundir entidades com regras distintas
ou retirar constraints de titularidade, auditoria e históricos necessários.

## Decisão

- Remover a tabela conversa, que continha somente o identificador do cliente.
  Mensagem vincula-se diretamente a cliente.usuario_id pela coluna cliente_id.
  Continuam unicidade por cliente/solicitação, índice temporal e FK composta
  (cliente_id,versao_contexto_id) → versao_ficha(cliente_id,id). Remover apenas a
  FK simples de contexto redundante; não retirar a proteção contra outro titular.
- Pergunta possui uma única fonte em mensagem.pedido.mensagem. Não há coluna
  pergunta duplicada; propriedade de leitura e DTO continuam disponíveis. Pedido
  é objeto JSON com mensagem string obrigatória de 1 a 1.000 caracteres após btrim.
  O pedido completo e hashes permanecem congelados para idempotência e replay.
- O resumo completo de triagem fica em execucao_ia.resultado.triagem. Triagem
  conserva seus metadados de snapshot, política, estado e motivos, sem resumo JSON
  duplicado. Manter a retenção privada de 90 dias e os recibos de auditoria.
- Consumo possui fonte canônica nas colunas de etapa_ia: remover JSON dados e
  cópia consumo do resultado da execução. Hidratar o DTO na leitura e derivar
  total_tokens da soma de entrada/saída. Ambos os campos são nulos ou conhecidos
  não negativos; não converter ausência de uso reportado em zero artificial.
- Manter catálogos/recursos, versões/dias/itens, publicação/parecer/validação,
  identidade/perfis, literatura/versões/ingestões/fragmentos e auditoria separados.
  Não introduzir requisito funcional, API, dependência ou camada nova.

## Migração, backup e reversão

A revisão nova 0016 sucede 0015; migrations aplicadas permanecem intactas.
Antes de descartar cópias, conferir consistência das perguntas, triagens e consumo
legados. Divergência interrompe a migration com erro seguro, sem expor dados
privados nem escolher silenciosamente qual cópia vence. Consumo em resultado
podia ficar desatualizado enquanto uma execução estava em voo; as etapas já
eram a fonte autoritativa de leitura e continuam sendo.

Fazer backup privado dos fontes/estado Git e dump PostgreSQL antes de aplicar ao
desenvolvimento. Guardar hashes, conferir o dump e restaurá-lo em banco isolado
para verificar a recuperação; dados, credenciais e backups ficam fora do Git.
O [guia do banco](../../../database/README.md#backup-e-restauração-da-revisão-0016)
e as [evidências desta entrega](../../testes/otimizacao-modelagem-20261119.md)
registram o procedimento e seu resultado efetivo.

Downgrade para 0015 recria as representações anteriores a partir das fontes
canônicas e os marcadores de conversa dos titulares com mensagens. Marcador vazio
sem mensagens não possui identidade independente no domínio; restauração exata
do estado anterior usa o backup. Para voltar a executar a versão antiga, combinar
schema e fontes compatíveis; não rodar código 0015 sobre schema 0016.

## Resultado estrutural e limites

O modelo lógico do escopo completo passa a 42 tabelas/331 colunas. O MVP físico
passa a 31 tabelas/258 colunas/51 FKs; onze tabelas planejadas continuam futuras.
São uma tabela e quatro colunas a menos, além de duas FKs; a normalização também
elimina cópias internas de JSON. Não equivale a redução percentual de tamanho em
disco, melhora de latência ou resultado de teste de carga. Essas métricas exigem
medição própria e uma amostra representativa.

O MER original é preservado como origem conceitual de 18 entidades. A
[comparação e os diagramas](../modelo-de-dados/visualizacao-otimizada/README.md)
separam essa origem, o físico entregue e as capacidades futuras. O diagrama físico
usa metadados ORM para representar as FKs compostas reais.

## Verificação exigida

Testar upgrade/downgrade com dados legados, abortar cópias divergentes antes de
descarte, comparar schema e ORM, verificar contexto nulo/inexistente/alheio,
pedidos inválidos, replay e fonte única de consumo/triagem. Executar regressão do
MVP e checagens documentais com resultados atuais no relatório vinculado.
Não herdar aprovação de testes antigos nem declarar nova qualificação AI-06/TST-01.
Sem chamadas LLM extras, alteração de prompts enviados ao modelo, corpus, quotas,
triagem, parecer posterior ou seleção de recursos disponíveis.
