# Triagem acadêmica — AI-01

MOD-06 entrega regras de triagem, projeção compacta, porta de análise assistida e
preparação autorizada. Requisitos RF-15/RF-19, RN-13/RN-15/RN-29/RN-30/RN-37 e
MRF03/MRF08/MRF09/MRF12; regras do [onboarding](../requisitos/onboarding-e-triagem.md)
e casos sintéticos já aprovados por delegação. Não é diagnóstico ou validação
clínica universal. Não exigir laudo, aprovação médica ou jurídica externa.

## Fronteiras e estágio

TriageService usa serviços públicos para obter snapshot MOD-03, papéis MOD-01,
designação MOD-02 e catálogo elegível MOD-04, que consulta os recursos MOD-10.
Não lê tabelas ou repositórios internos desses módulos. Snapshot concluído não
exige avaliação/parecer prévio do instrutor. Instrutor designado pode usar o
serviço interno no seu escopo de saúde; contexto privado do chat continua próprio.

A política e os DTOs são tipados. StrictModel/digest ficam na camada compartilhada
app/contracts/structured.py; não dependem da implementação interna de extração
RAG. Evidence é contrato público da recuperação MOD-05. JSON é usado nas
fronteiras externas; chamadas internas não são serializadas artificialmente.
O ponto de composição no main.py e o contrato compartilhado são ajustes equivalentes
necessários ao cartão. Não houve dependência, migration ou frontend novos.

AI-01 define a porta Analyst, testada com doubles rotulados. AI-02 fará a composição
com RAG-05 e o provedor gratuito, com timeouts reais. Não há chamada LLM ou vetorial
na rota de preparação desta entrega; importar/iniciar a API não cria sucesso falso.
Sem Analyst, caso que precisa de análise retorna AGUARDANDO_ANALISE, estado de
saúde null e geracao_permitida=false. É um estado técnico, sem quarto estado clínico.
Treino manual continua independente.

## Projeção e regras

O resumo contém apenas idade congelada no snapshot e os campos de OnboardingData:
altura_cm, peso_kg, objetivo, experiência, atividade, dias/duração, flags e listas
de saúde/medicamentos/limitações e observações. Preservar textos, negações,
gravidade e desconhecido. Nome, e-mail, telefone, biometria, autoria e IDs privados
não compõem o conteúdo enviado à porta. A referência de snapshot (ID/número/revisão)
faz parte do registro interno separado, e não do resumo entregue ao Analyst.

O backend cria o resumo sem LLM. Conta caracteres da serialização JSON compacta,
ensure_ascii=False, incluindo chaves e conteúdo; teto padrão 2400. O hash SHA-256
usa esses bytes UTF-8. Excesso produz CONTEXTO_EXCEDIDO e não chama o Analyst;
não truncar alertas. Se um bloqueio determinístico tiver precedência, mantém-se
BLOQUEADO_POR_SEGURANCA mesmo sem resumo que caiba. O original permanece em MOD-03.
A porta recebe cópia profunda do conteúdo; não pode alterar a projeção original.

Ordem de decisão implementada:

1. Autorizar ator/perfil e cliente no backend antes de obter contexto privado.
2. Ausência de snapshot concluído ou schema inválido: DADOS_INSUFICIENTES.
3. Idade ausente/inválida: insuficiência; menor de 18: bloqueio ESCOPO_ETARIO.
4. GRAVE declarado em condição/limitação, restrição ou evento importante=SIM:
   bloquear ALERTA_GRAVE_DECLARADO, antes de considerar flags desconhecidas.
5. Flag necessária/gravidade=NAO_SEI: insuficiência; contexto excessivo também
   impede análise. Ausente não é preenchido com saudável, zero ou média.
6. Sem bloqueio, fazer até uma análise assistida, quando configurada. A porta recebe
   resumo, evidências fornecidas pelo chamador autorizado e referência da política.
7. Alerta grave no texto sinalizado pela análise: bloquear ALERTA_GRAVE_TEXTO.
   Lacuna/contradição: DADOS_INSUFICIENTES. Retorno válido não bloqueante:
   ELEGIVEL_PARA_GERACAO, ainda sujeito a recursos e validações da geração.

A política não inventa taxonomia clínica ou busca palavras soltas para diagnosticar.
Condição/medicamento não grave não bloqueia automaticamente. Suporte específico
para adaptação é exigido na geração, não inferido de um estado de elegibilidade.

## Estados, sinais e recursos

[Contratos JSON](../requisitos/schemas/triagem-v1.schema.json) distinguem:

- Estado de saúde: DADOS_INSUFICIENTES, BLOQUEADO_POR_SEGURANCA ou
  ELEGIVEL_PARA_GERACAO. Pode ser null enquanto não há decisão técnica válida.
- Estado técnico: CONCLUIDA, AGUARDANDO_ANALISE, FALHA ou TIMEOUT.
- Motivos enumerados, versão/hash da política, snapshot, hash do resumo e IDs das
  evidências declaradas. Nenhum raciocínio interno, diagnóstico ou aceite humano.
- Quantidade de exercícios viáveis e fingerprint do catálogo/alternativas atuais.
  Falta de recursos não transforma o cliente em caso grave ou saudável.

Signals tem booleanos estritos para alerta_grave/lacuna/contradicao e IDs de
fragmentos fornecidos na chamada. Validar novamente mesmo instância Pydantic;
saída inválida ou referência inventada retorna falha técnica, sem elegibilidade.
Não aceitar campos adicionais como diagnóstico, autorização, medicamento ou aceite.
Timeout, quota e indisponibilidade não viram ELEGIVEL. Não há retry automático;
resposta válida depois de 25 s é recusada. O timeout/cancelamento de transporte
pertence ao adaptador AI-02; AI-01 não cria thread de reparo nem loop.

Geracao_permitida só pode ser true após decisão elegível concluída e existência
de candidato viável. Não é autorização de publicar uma ficha: AI-03 ainda valida
catálogo, equipamentos, restrições, fontes, JSON e versão-base antes de TRN-03.
A rota entregue não tem Analyst configurado e não retorna elegibilidade presumida.

## Concorrência, registro e persistência

As leituras SQL usam transações curtas, fechadas antes da análise. Depois, o
serviço reconsulta papéis/designação, snapshot e recursos. Perda de permissão
nega entrega. Snapshot novo devolve CONTEXTO_SUPERADO, remove resumo/evidências
do resultado e exige nova execução; não roda análise automaticamente outra vez.
Recurso/catálogo alterado mantém a decisão de saúde, mas nega geração e sinaliza
RECURSOS_ALTERADOS com a disponibilidade atual. Publicação ainda revalida em AI-03.

O registro estruturado TriageResult contém códigos, evidências, resumo, fonte e
política para o futuro orquestrador. Não expor seu resumo privado como resultado
público da preparação. Auditoria MOD-12 persiste ai.triage.checked, ator, referência,
correlação, UTC e policy_v1, sem anamnese ou motivos de saúde em logs operacionais.

As tabelas planejadas execucao_ia/triagem/etapa/evidência serão materializadas
em AI-02/AI-03, conforme seus cartões. AI-01 não cria execução fictícia ou tabela
paralela de triagem para contornar a dependência do modelo lógico. O endpoint é
consulta de preparação, não pedido idempotente de geração; suas leituras podem
produzir registros distintos de auditoria. Nova tentativa e persistência de
execução continuam no contrato do orquestrador.

## API entregue

GET /api/v1/ia/triagem/preparacao, autenticada, sem body nem seleção de cliente.
O backend usa exclusivamente actor.user_id e o snapshot concluído mais recente.
Exige cliente titular (USE_AI_CONTEXT); administrador/atendente/instrutor sem papel
de cliente não acessam por essa rota. Parâmetros extras de cliente/onboarding não
mudam o escopo. Sessão ausente/inválida retorna 401; papel/contexto proibido, 403.
Resposta 200 usa TriageView: estados, motivos, política, referências e contagens;
sem resumo/anamnese, com Cache-Control: no-store. Sem onboarding: insuficiência;
com caso bloqueado: bloqueio; caso apto às próximas verificações: aguardando análise.
Sem parâmetro que permita ao cliente injetar Signals ou configurar um double.

## Testes e limites

[Comandos](../testes/comandos.md#triagem-acadêmica-e-preparação-ai-01) cobrem regras,
API real/PostgreSQL, autorização, catálogo/equipamentos e trocas durante análise.
Os 19 casos aplicáveis da tabela T01–T24 são executados no núcleo. T16 é coberto
por autorização na integração, T21 por versionamento e T22 por recurso indisponível.
T18 (adaptação/publicação sem suporte) e T23 (revogação antes da publicação) são
critérios de AI-03/RAG-05, sem antecipar publicação nesta etapa. T10 usa limite de
teste reduzido e há também teste de excesso real acima de 2400 caracteres.

Doubles não comprovam identificação semântica de alertas no provedor real.
AI-06 verificará o modelo, latência e qualidade integrada. Nenhuma aprovação manual
do responsável é necessária entre esses testes; ele fará a revisão manual no MVP,
conforme a orientação vigente. O aceite integrado e o E2E continuam em TST-01.
