# Fluxos atualizados — treino, matrícula e biometria

Origem: correções explícitas do responsável após a revisão do planejamento.
Este documento atualiza a especificação e os prompts; não comprova implementação.
O MER original permanece preservado e será revisado em FND-03.

## Treino disponível antes do parecer

1. Cliente com onboarding concluído solicita treino; triagem e regras continuam obrigatórias.
2. IA/RAG produz conteúdo; backend valida schema, catálogo, restrições e contexto atual.
3. Conteúdo válido é publicado ao cliente, com parecer profissional PENDENTE.
4. Cliente consulta o treino e conversa com a IA sem esperar aceite do instrutor.
5. Instrutor designado recebe aviso/fila e pode aceitar ou rejeitar a versão, com
   parecer, responsável e data; também pode modificar integralmente criando nova versão.
6. Adaptação pelo chat passa novamente pela triagem/validações, cria nova versão
   publicada e novo parecer PENDENTE. Versões anteriores seguem RF-17/RF-35.

Publicação e parecer são dimensões independentes:

| Dimensão | Estados propostos | Efeito |
|---|---|---|
| Geração técnica | EM_PROCESSAMENTO, VALIDADA, BLOQUEADA, FALHOU | Validação é necessária para publicar |
| Publicação | RASCUNHO, PUBLICADO, SUBSTITUIDO | Conteúdo publicado pode ser consultado |
| Parecer por versão | PENDENTE, ACEITO, REJEITADO | Informa avaliação posterior, sem bloquear consulta/chat |

Aprovação do agente revisor é uma validação automática, não um aceite profissional.
Caso grave bloqueado pela política continua sem geração/publicação de treino.
Chat pode funcionar sem ficha avaliada; ausência de ficha não permite inventar contexto.
Cliente sem instrutor mantém consulta/chat, com pendência de designação para revisão.
Falha de aviso não desfaz publicação nem perde a tarefa de avaliação.
Rejeição deve aparecer ao cliente, com motivo, e não ocultar conteúdo ou bloquear chat.
Rejeitar a ficha vigente não a oculta: ela permanece atual e consultável. Quando
uma ficha posterior também é rejeitada, excluir o conteúdo da rejeitada anterior
e manter a nova rejeitada enquanto retida. Gerar/publicar ou aceitar não dispara
essa exclusão específica. RF-17 aplica independentemente o limite de 15 versões:
publicar excedente remove conteúdo mais antigo, inclusive aceito/rejeitado.
A vigente e os registros de treinos executados não são apagados; manter
metadados de auditoria, sem reexpor o conteúdo excluído em API, exportação ou chat.
Aplicar exclusão e troca atomicamente, com idempotência e ordem de versões;
parecer atrasado não elimina a rejeitada mais recente (CA-35.7/CA-35.8).
Conteúdo publicado é imutável. Parecer refere-se a uma versão e não passa para outra.

Adaptação por saúde exige evidência pertinente recuperada do corpus aprovado e
vinculada à recomendação. Falta de suporte, população/condição incompatível ou
conflito não resolvido retorna abstenção; não gerar/publicar adaptação nem
substituir evidência pela memória do modelo. Regras de bloqueio continuam prevalecendo.

## Matrícula e cadastro facial sem pagamento obrigatório

Fluxo confirmado: cliente cadastrado → atendente autorizado registra matrícula
sem exigir pagamento → captura/cadastro da foto de referência → nova captura para acesso.

A matrícula manual (MEM-01) deve funcionar sem registro financeiro, comprovante,
gateway ou execução de MEM-00. Atendente escolhe plano ativo, validade, modalidade
e limites; o sistema registra responsável e histórico, inclusive nas renovações.
Ausência de pagamento, pagamento pendente/recusado ou falha do serviço financeiro
não impedem essa operação nem invalidam automaticamente uma matrícula vigente.

Financeiro permanece na fase tardia. MEM-00 é opcional para registrar pagamentos,
sem criar pré-requisito para MEM-01. Gateway/webhook futuro atualiza situação
financeira, sem matricular automaticamente ou introduzir bloqueio de acesso.

Conta ativa, matrícula válida e referência facial são estados diferentes. Um
cadastro não significa autorização de entrada. Matrícula contém plano, validade,
modalidade e limites; vencimento não apaga histórico nem referência.
Funcionário autorizado pode substituir a foto, mantendo auditoria e retirando
a referência anterior conforme política. Cliente não troca sua própria biometria.

## API de reconhecimento facial — CompreFace confirmado

CompreFace é a escolha confirmada em DEC-015. GATE-08 ainda define versão/modelo,
hospedagem, critérios de captura, contratos e ensaio real; não reabre o fornecedor.

- Validar exatamente um rosto antes de cadastrar ou reconhecer, usando detecção
  do provedor com limiar definido; limitar a resposta a um resultado não comprova
  que havia apenas um rosto na imagem.
- Cadastrar com POST /api/v1/recognition/faces?subject=..., usando identificador
  opaco associado ao cliente, e guardar image_id para controle de substituição.
- Comparar nova captura com POST /api/v1/recognition/recognize e resolver subject
  no backend; resultado desconhecido ou ambíguo não é identificação positiva.
- Usar subjects[].similarity na escala 0–1, com limiar inicial 0,95 (95 na tela).
  box.probability/det_prob_threshold dizem respeito à detecção, não à correspondência.
  O limiar exige calibração; 0,95 não comprova acurácia de 95%.
- Substituir a referência com compensação de falhas parciais e exclusão do exemplo
  anterior por DELETE /api/v1/recognition/faces/{image_id}; o serviço aceita vários
  exemplos, mas o projeto mantém uma referência ativa conforme RF-22.
- Manter x-api-key somente no backend, fora do Git, com timeout e limites de uso.

Os vetores faciais pertencem ao serviço biométrico; não são documentos do RAG nem
devem compartilhar a coleção vetorial de literatura. Foto e metadados biométricos
ficam em armazenamento protegido e separado dos relatórios comuns.
A busca deve testar outra captura da pessoa, e não apenas reenviar a foto cadastrada.
Cadastro e busca por imagem não incluem prova de vida; eventual exigência será
decisão adicional explícita, sem presumir que comparação de fotos a oferece.

Fontes técnicas: [REST CompreFace](https://github.com/exadel-inc/CompreFace/blob/master/docs/Rest-API-description.md)
e [limiar de similaridade](https://github.com/exadel-inc/CompreFace/blob/master/docs/Face-Recognition-Similarity-Threshold.md).

A distribuição oficial do serviço usa Docker/Compose. Para manter Docker do
AcademIA no final, preferir instância externa já disponível; se não houver,
registrar com o professor a decisão de execução antes de ACS-01/ACS-02. A escolha
do fornecedor não antecipa Docker nem aprova uma exceção de infraestrutura.

## Catraca fictícia — serviço externo de teste

O serviço simulador representa o equipamento, não o reconhecimento facial.
Fica separado em simulators/turnstile/, executado localmente sem Docker nesta fase,
com REST/JSON e OpenAPI. Não exige microserviços para o restante da aplicação.

Contrato proposto a fechar em GATE-08:

| Operação | Dados mínimos | Semântica |
|---|---|---|
| POST /commands | schema_version, request_id, access_decision_id, client_id quando identificado, direction, decision ALLOW/DENY, expires_at | Recebe decisão autenticada e devolve confirmação do comando |
| Evento de passagem para o AcademIA | schema_version, event_id, request_id, occurred_at, direction, simulated=true | Confirma passagem simulada vinculada a uma autorização válida |

Destino do retorno é configurado no serviço; não aceitar URL arbitrária no comando.
Autenticar comandos e retornos, validar esquema e impedir replay. Idempotência
preserva correlação sem criar novo comando ou frequência ao repetir o mesmo ID.
Mesmo ID com conteúdo diferente gera conflito, não uma segunda autorização.
Comando DENY pode constar no histórico de teste, mas não produz passagem autorizada.
Comando aceito não conta presença: confirmação de passagem é etapa separada.
Repetição ou falha após envio usa a mesma chave; timeout não é sucesso.
Uma passagem só conta com decisão ALLOW válida na ocorrência, direção compatível
e evento autenticado. Entrada e saída têm regras próprias; negação de entrada não
deve impedir saída. Registrar sempre quando o evento é simulado.

Fluxo de demonstração: foto nova → API facial real → identidade local → motor
valida conta/matrícula/modalidade/limites → comando à API fictícia → confirmação
de passagem simulada → frequência/lotação. Liberação manual continua auditada.

## Evidências de aceite

- Treino e chat acessíveis com parecer PENDENTE; aceite/rejeição posterior por versão.
- Atendente matricula/renova sem pagamento e sem módulo financeiro disponível.
- Cliente com matrícula válida e referência facial passa pelas regras de acesso
  mesmo sem pagamento; matrícula ausente/vencida continua negando entrada.
- Cadastro facial depois da matrícula e reconhecimento com captura distinta.
- Rosto conhecido/desconhecido, baixa qualidade, múltiplos rostos e falha do provedor.
- Matrícula ausente/vencida e limite excedido negam entrada mesmo com rosto reconhecido.
- Comando aceito sem passagem não altera frequência; repetição não duplica presença.
- Testes unitários usam mocks; biometria exige ensaio real com provedor configurado.
- Catraca e passagens continuam explicitamente simuladas, sem hardware físico.

IDs afetados: RF-15–RF-19, RF-22, RF-31, RF-35–RF-37; TRN-02–04, AI-03–05,
TST-01, MEM-01, ACS-01–03/07, MEM-00 (financeiro opcional) e FIN-02. São refinamentos de MOD-04/06/07/08,
sem necessidade de criar outro módulo de domínio.

## Equipamentos, retenção e idioma no MVP

Administrador mantém recursos disponíveis → catálogo relaciona requisitos por
exercício/variação → backend filtra candidatos conforme recursos e saúde → IA
gera somente entre candidatos → revalidação do inventário e do contexto → publicação
atômica com retenção de 15 versões completas → cliente consulta em português.

Recurso disponível é cadastrado, ativo e operacional, sem controle de ocupação em
tempo real. Uma combinação exige todos os itens e uma alternativa só é válida
quando completa. Peso corporal exige dispensa explícita; cadastro faltante não libera.
Inventário vem de MOD-10, evidência da literatura vem de MOD-05. Equipamento que
fica indisponível depois é sinalizado para adaptação, sem reescrever o passado.

Fonte PT/EN pode sustentar explicação em português; original, localização e idioma
permanecem identificados. Avaliar recuperação, tradução, unidades e negações.
Dados de exemplo de equipamentos serão criados somente na implementação.

O limite de 15 conta versões publicadas completas incluindo a vigente; rascunhos,
tentativas e registros/snapshots de execuções não entram na contagem. Conteúdo
excedente é removido também de exportação/cache/contexto ativo. Auditoria guarda
identificação, autoria, parecer, datas e motivo, sem reexpor a prescrição excluída.
Preservar execuções existentes não exige criar agora um módulo de execução de treino.
