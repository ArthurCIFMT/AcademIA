# GATE-08 — Preparação de matrícula, biometria e catraca

Estado **FECHADO** em 24/11/2026. O gate foi tratado em conjunto por escolha
do responsável. O [manifesto](../prompts/README.md) registra a liberação de
MEM-01 e ACS-07. Os testes integrados de cada módulo pertencem ao seu cartão.

## Decisões vigentes

- O atendente autorizado matricula e renova com plano ativo, sem exigir
  confirmação de pagamento. A validade começa e termina em datas civis
  inclusivas no fuso de São Paulo. Alterações no plano preservam a modalidade
  e os limites já contratados na matrícula.
- CompreFace realiza reconhecimento real. A identidade reconhecida entra
  no motor de acesso do AcademIA, que avalia conta, matrícula, modalidade e
  limites. O limiar inicial é 0,95 de similaridade.
- A catraca acadêmica é uma API fictícia separada. A confirmação do comando
  e a passagem simulada são eventos distintos. Frequência e lotação usam
  passagens confirmadas. A alternativa manual registra responsável e motivo.
- Em 22/11/2026 o responsável autorizou Docker apenas para uma instância
  local dedicada do CompreFace, cuja distribuição oficial usa Compose. O
  AcademIA e a catraca fictícia continuam com execução nativa nesta fase.
  Os cartões INF-01–INF-04 seguem na etapa final.
- O responsável aprovou, em 22/11/2026, as três regras abaixo para matrícula
  e acesso. Aplicá-las nos cartões correspondentes.

Fontes do projeto: [fluxos de acesso](fluxos-atualizados.md),
[regras de negócio](../requisitos/regras-de-negocio.md) e
[invariantes](modelo-de-dados/invariantes-e-estados.md).

## Regras aprovadas para os cartões de implementação

| Tema | Regra | Cartão |
|---|---|---|
| Janela e unidade | Limite de entradas confirmadas por cliente no dia civil de São Paulo, configurável no plano e congelado na matrícula. Limite ausente representa acesso sem teto diário. Renovar no mesmo dia conserva o uso já realizado. | MEM-01, ACS-03 |
| Renovação | Evitar sobreposição de períodos de matrícula do cliente. Uma renovação antecipada pode começar no dia seguinte ao fim do período já contratado. Preservar o histórico. | MEM-01 |
| Alternativa manual | Após falha de reconhecimento, atendente autorizado confirma a identidade, informa o motivo e solicita passagem pelo mesmo motor. Conta, matrícula, validade, modalidade e limite continuam obrigatórios. O registro distingue a origem manual. | ACS-04 |

## Contratos para a integração

| Tema | Decisão técnica | Cartão |
|---|---|---|
| Validade e modalidade | A consulta retorna a matrícula ativa no intervalo civil e a modalidade contratada. Para a demonstração, comparar essa modalidade com a do ponto de entrada configurado no backend. | MEM-01, ACS-03 |
| Concorrência | Uma decisão de entrada pendente reserva uma unidade do limite aplicável até a passagem ou expiração do comando. A passagem confirmada consome a entrada. Repetição, negação, saída e autorização expirada não incrementam o uso. A reserva do limite e o registro da decisão são atômicos. | ACS-03, ACS-05 |
| Serviço simulado | Serviço Python/FastAPI separado em `simulators/turnstile/`, executado nativamente. O AcademIA e a catraca trocam JSON versionado, com credenciais distintas por sentido e endereços fixados na configuração. | ACS-07, ACS-03 |

### Contrato da catraca fictícia

| Mensagem | Dados | Resultado |
|---|---|---|
| `POST /commands` pelo AcademIA | `schema_version=1`, `request_id`, `access_decision_id`, `direction` (`ENTRY` ou `EXIT`), `decision` (`ALLOW` ou `DENY`), `expires_at` e `client_id` quando identificado | 202 com `schema_version=1`, `request_id` e `status=ACCEPTED`. A aceitação mantém frequência e lotação inalteradas. |
| `POST /api/v1/acesso/catraca/passagens` pelo simulador | `schema_version=1`, `event_id`, `request_id`, `occurred_at`, `direction` e `simulated=true` | 201 com `schema_version=1`, `event_id` e `status=RECORDED` para passagem vinculada a uma autorização válida, de direção correspondente. |

Os identificadores são UUIDs. Datas e horas trafegam em ISO 8601 com fuso.
Comando e passagem repetidos com a mesma chave e conteúdo devolvem o recibo
anterior com HTTP 200. Divergência na mesma chave retorna 409. O retorno tem deduplicação
por origem e ID do evento. O sucesso também é limitado a uma passagem por
comando. `DENY`, expiração e indisponibilidade são verificáveis no simulador.
A URL de retorno vem da configuração do serviço. Validar
`Authorization: Bearer` antes de processar, com tokens distintos para comando
e retorno e sem incluí-los em logs. Usar loopback na demonstração local.

### Contrato de integração com CompreFace

Referência validada no ensaio local: CompreFace 1.2.0 com FaceNet em CPU,
detector `facenet.FaceDetector` e comparador `facenet.Calculator`. Usar
`x-api-key` somente no backend, credenciais distintas para os serviços de
detecção e reconhecimento, coleção de teste isolada, identificadores de
pessoa opacos e limites de carga e tempo configuráveis. Referências de versão e API:
[release 1.2.0](https://github.com/exadel-inc/CompreFace/releases/tag/v1.2.0) e
[contrato REST](https://github.com/exadel-inc/CompreFace/blob/v1.2.0/docs/Rest-API-description.md).

| Operação | Verificação esperada |
|---|---|
| Detecção | Usar `POST /api/v1/detection/detect` e conferir exatamente um rosto, sem truncar a resposta a um resultado. No ensaio, o limiar de detecção foi 0,8. A resposta 400 com código 28 identificou a imagem sem rosto. |
| Cadastro | Enviar a referência a `POST /api/v1/recognition/faces`, relacionando `subject` opaco e `image_id` no backend. |
| Reconhecimento | Usar `POST /api/v1/recognition/recognize` com uma nova captura. Resolver o `subject` local e considerar o limiar inicial de similaridade. Desconhecido, ambíguo e falha do provedor têm saídas distintas. |
| Substituição | Confirmar a nova referência e descartar o exemplo anterior por `DELETE /api/v1/recognition/faces/{image_id}`. Tratar falhas parciais e impedir que uma referência não vigente autorize acesso. |

Calibrar os critérios de captura e registrar a resposta por cenário.
Similaridade de 0,95 é o limiar inicial da decisão, com desempenho a medir
na instância. Comparar imagens não comprova prova de vida. Consultar a
[documentação de similaridade](https://github.com/exadel-inc/CompreFace/blob/v1.2.0/docs/Face-Recognition-Similarity-Threshold.md).

## Ensaio e condição de fechamento

| Etapa | Evidência esperada |
|---|---|
| Prontidão do provedor no GATE-08 | Instância acessível e autorizada para teste, versão e modelo identificados, autenticação e chamadas reais de detecção/cadastro/comparação/exclusão em coleção isolada. |
| Biometria no ACS-01/02 | Referência e nova captura da mesma identidade, rosto diferente, imagem sem rosto, múltiplos rostos, pontuação insuficiente, troca de referência e falha do provedor. |
| Acesso no MEM-01 e ACS-03/04 | Matrícula sem pagamento, vencimento, modalidade incompatível, limite, falha facial e alternativa manual auditada. |
| Catraca e frequência no ACS-07, ACS-03 e ACS-05 | Comando aceito sem passagem, passagem autorizada, negação, expiração, timeout e repetição. A lotação muda só após passagem confirmada. |

Usar dados de teste sintéticos e capturas distintas. A evidência registra
versão, modelo, casos e resultados, com fotos e credenciais fora do Git
e dos logs. A prontidão do provedor no gate verifica a API diretamente.
O aceite integrado com o sistema ocorre nos cartões correspondentes.

### Resultado da prontidão do provedor em 24/11/2026

O ensaio autenticado usou uma aplicação isolada no CompreFace e amostras
renderizadas do DigiFace-1M. A referência e a nova captura vieram de
quadros distintos do painel sintético. O download manteve as amostras
fora do Git. [DigiFace-1M](https://microsoft.github.io/DigiFace1M/) e
[revisão das amostras](https://github.com/microsoft/DigiFace1M/tree/1d173f305de9afefafb8589ce8e726ec685863e5/docs/img).

| Cenário | Resultado observado |
|---|---|
| Detecção de referência, nova captura e outra identidade | HTTP 200 com um rosto em cada imagem |
| Múltiplos rostos | HTTP 200 com dois rostos |
| Imagem sem rosto | HTTP 400, código 28 |
| Credencial inválida | Consulta recusada com HTTP 400 |
| Cadastro de referência | HTTP 201 |
| Nova captura da mesma identidade | Similaridade 0,99989 |
| Terceira apresentação da mesma identidade | Similaridade 0,98737 |
| Outra identidade | Similaridade 0,07171, abaixo do limiar de 0,95 |
| Substituição | Novo exemplo criado, exemplo anterior excluído e listagem confirmando a troca |
| Limpeza | Exemplos e identidade de teste removidos. Consulta autenticada confirmou coleção vazia |

A primeira chamada coincidiu com o aquecimento do serviço e recebeu HTTP 502.
A repetição após a API responder passou. Os valores medidos descrevem esta
amostra sintética. ACS-01 e ACS-02 continuam responsáveis pelo aceite
integrado de cadastro e reconhecimento.

### Execução local da instância dedicada

O CompreFace publicou somente o endereço local `127.0.0.1:18080` e usa
volume e rede próprios. O projeto Compose `academia-compreface` fica em
`backend/data/compreface-v1.2.0/academia-local/`, fora do Git. O pacote
oficial usa imagens 1.2.0. A cópia local vincula a porta 80 do frontend
somente ao loopback, usa senha própria para seu PostgreSQL, configura a
API para dispensar o armazenamento da imagem bruta no banco do provedor e reduz o log do núcleo
para `WARNING`. A configuração privada guarda as chaves dos dois serviços.

Para reiniciar a instância já provisionada, a partir da raiz e com Docker
Desktop ativo:

```powershell
$p = "backend/data/compreface-v1.2.0/academia-local"
docker compose -p academia-compreface --env-file "$p/.env" -f "$p/compose.yaml" up -d --pull never --no-build
```

O iniciador de dois cliques do AcademIA continua com a configuração
existente. A conexão do backend ao provedor é responsabilidade de ACS-01.
