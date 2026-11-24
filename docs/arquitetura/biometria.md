# Referência facial — ACS-01

O atendente autorizado seleciona o cliente na área **Atendimento → Matrículas**
e envia ou captura a foto. O backend exige perfil de cliente habilitado e uma
matrícula registrada pelo atendente. A data de vigência será avaliada no motor
de acesso. Uma matrícula com início futuro permite preparar a referência.

## Validação e privacidade

O AcademIA aceita JPG ou PNG estático de até 4 MiB e 4096 px por lado. A foto
é decodificada, orientada e recodificada sem metadados no backend. O CompreFace
valida exatamente um rosto com confiança inicial de detecção de 0,8, sem
limitar a quantidade devolvida pelo detector. A similaridade inicial de 0,95
pertence ao reconhecimento de uma nova captura.
[Contrato do CompreFace 1.2.0](https://github.com/exadel-inc/CompreFace/blob/v1.2.0/docs/Rest-API-description.md).

Os bytes da foto transitam somente em memória no backend. A instância local
segue a configuração do GATE-08 e conserva a representação facial necessária,
com armazenamento da imagem bruta desativado no provedor. O banco da aplicação
guarda um identificador opaco por foto, o identificador do exemplo no provedor,
estado, atendente e horário. A resposta ao navegador contém apenas o status.
Auditoria e aviso interno para administradores registram a operação, sem
armazenar foto, imagem codificada, credenciais ou IDs do provedor.

## Troca e recuperação

1. O backend valida a foto e grava uma reserva `PREPARANDO` com identificador
   próprio antes de enviar o exemplo ao CompreFace.
2. Após o provedor confirmar o cadastro, a candidata fica `PRONTA`. Se houver
   referência ativa anterior, o backend exige confirmação da remoção daquele
   exemplo antes de concluir.
3. A transação publica a nova referência `ATIVA`, remove o vínculo anterior
   e grava auditoria e aviso. Uma referência pendente fica indisponível
   para identificação. O PostgreSQL permite uma ativa e uma pendente por cliente,
   e as escritas são serializadas pelo serviço de pessoas.
4. Se houver falha do provedor, a API informa que a troca está pendente e
   registra a falha. A referência anterior segue registrada. Se a exclusão
   tiver ocorrido sem resposta, o retry confirma a ausência antes de publicar.
   A ação **Verificar pendência** consulta o identificador reservado. Pode
   encerrar um envio ausente ou concluir com o exemplo confirmado, sem pedir
   novamente a foto. Se a resposta do provedor continuar incerta, a pendência
   continua registrada.

`active_client_for_subject` devolve apenas o cliente associado ao identificador
de uma referência `ATIVA`. A captura de reconhecimento, a prova de identidade
e a autorização do acesso são entregas posteriores. Confiança de detecção e
similaridade são medidas diferentes.

## Rotas e configuração

Com sessão e papel ATENDENTE, sob `/api/v1/atendimento/clientes/{client_id}/biometria`:

| Método | Entrada | Saída |
|---|---|---|
| GET | Identificador de cliente | `cadastrada`, `elegivel`, `disponivel`, `atualizada_em` e `pendencia` |
| POST | JSON com `imagem_base64` e cabeçalho CSRF | Status atualizado (200) |
| POST em `/pendencia` | Cabeçalho CSRF, sem foto | Status após consultar e recuperar a tentativa pendente (200) |

`disponivel` informa configuração local do adapter. Foto inválida retorna 422,
conflito de elegibilidade ou pendência retorna 409 e falha de configuração ou
operação externa retorna 503. A API não expõe fotos ou retorno bruto do provedor.

Defina em `.env` local `ACADEMIA_COMPREFACE_URL`,
`ACADEMIA_COMPREFACE_DETECTION_KEY` e `ACADEMIA_COMPREFACE_RECOGNITION_KEY`.
Use chaves distintas de uma aplicação local de desenvolvimento e mantenha
a coleção de testes separada. A URL aceita HTTPS ou HTTP de loopback.
`ACADEMIA_COMPREFACE_TIMEOUT_SECONDS`, `ACADEMIA_COMPREFACE_DETECTION_THRESHOLD`
e `ACADEMIA_COMPREFACE_MAX_IMAGE_BYTES` têm os valores iniciais em `.env.example`.
O iniciador lê essas variáveis. A instância já provisionada do CompreFace é
ligada separadamente conforme o [GATE-08](preparacao-gate-08.md#execução-local-da-instância-dedicada).
