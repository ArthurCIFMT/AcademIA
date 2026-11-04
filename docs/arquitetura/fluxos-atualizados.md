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
   publicada e novo parecer PENDENTE. Versões anteriores permanecem preservadas.

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
A política para escolher qual versão permanece atual após rejeição ainda deve ser
definida, preservando essas permissões; não inventar uma retirada automática.
Conteúdo publicado é imutável. Parecer refere-se a uma versão e não passa para outra.

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

## API de reconhecimento facial — recomendação pendente

Recomenda-se Amazon Rekognition como candidato ao adapter facial (REC-011/GATE-08),
por oferecer cadastro de referências em coleção e busca por imagem. A escolha ainda
não está aprovada; comparar disponibilidade de conta, região e orçamento antes do módulo.
Não foram criadas coleções, provisionados recursos ou realizadas chamadas pagas.

Se aceita, a integração deverá:

- Validar exatamente um rosto com DetectFaces antes de cadastrar ou buscar;
  limitar MaxFaces a 1 não basta para recusar imagens com vários rostos.
- Cadastrar referência com IndexFaces e filtro de qualidade; associar FaceId ao
  UUID local do cliente, sem usar nome/e-mail como identificador externo.
- Buscar uma nova captura com SearchFacesByImage, resolver FaceId no backend e
  tratar resultado desconhecido ou ambíguo como não identificado.
- Usar Similarity como pontuação de correspondência, separada da confiança de
  detecção do rosto. Limiar inicial de 95, na escala 0–100, precisa de calibração;
  ele não demonstra acurácia de 95% nem probabilidade de identidade correta.
- Substituir referências com controle de falha parcial e limpeza por DeleteFaces,
  sem abandonar referências antigas pesquisáveis após conclusão da substituição.
- Manter credenciais somente no backend e fora do Git, com permissões necessárias
  ao adapter, limites de requisição e timeouts.

Os vetores faciais pertencem ao serviço biométrico; não são documentos do RAG nem
devem compartilhar a coleção vetorial de literatura. Foto e metadados biométricos
ficam em armazenamento protegido e separado dos relatórios comuns.
A busca deve testar outra captura da pessoa, e não apenas reenviar a foto cadastrada.
Cadastro e busca por imagem não incluem prova de vida; eventual exigência será
decisão adicional explícita, sem presumir que comparação de fotos a oferece.

Fontes técnicas: [IndexFaces](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_IndexFaces.html),
[SearchFacesByImage](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_SearchFacesByImage.html),
[DetectFaces](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DetectFaces.html),
[DeleteFaces](https://docs.aws.amazon.com/rekognition/latest/APIReference/API_DeleteFaces.html)
e [limiares de similaridade](https://docs.aws.amazon.com/rekognition/latest/dg/thresholds-collections.html).

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
