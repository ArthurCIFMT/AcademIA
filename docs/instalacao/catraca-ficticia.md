# Simulador de catraca — ACS-07

A catraca fictícia é um serviço Python/FastAPI em processo separado. Usa o
ambiente Python do backend e escuta em `127.0.0.1:8011` por padrão. O [contrato
do GATE-08](../arquitetura/preparacao-gate-08.md#contrato-da-catraca-fictícia)
define o tráfego com o AcademIA. O simulador executa nativamente no Windows.

## Configuração e início

- No `.env` privado, configure `ACADEMIA_TURNSTILE_COMMAND_TOKEN` e
  `ACADEMIA_TURNSTILE_CALLBACK_TOKEN`, com valores aleatórios distintos,
  URL-safe, de 32 a 256 caracteres. Ambos habilitam o simulador no iniciador.
- `ACADEMIA_TURNSTILE_URL` define a origem HTTP de loopback. A porta deve ser
  distinta das portas do restante do sistema.
- O retorno é fixado por `ACADEMIA_TURNSTILE_CALLBACK_URL`. O caminho aceito é
  `/api/v1/acesso/catraca/passagens` em HTTP de loopback. Com o iniciador, o
  padrão usa a porta configurada para o backend. A origem continua externa
  ao corpo recebido. O timeout do retorno é configurável e começa em dois
  segundos.
- O arquivo local e privado do simulador é definido por
  `ACADEMIA_TURNSTILE_STORE_PATH`. O padrão é `backend/data/turnstile.sqlite3`,
  relativo à raiz. Prepare esse arquivo uma vez, a partir da raiz do projeto:

```powershell
& ./backend/.venv/Scripts/python.exe -c 'from dotenv import load_dotenv; from simulators.turnstile.__main__ import main; load_dotenv(".env"); main()' --prepare
```

Use **Iniciar AcademIA.cmd** para iniciar e encerrar o simulador junto dos
serviços nativos. Para executar somente a catraca em um terminal, rode o
mesmo comando de preparação sem a opção `--prepare`. `GET /health` informa a
prontidão, e `GET /openapi.json` descreve os contratos de entrada. A
inicialização normal abre apenas o armazenamento já preparado.

## Ensaio HTTP e retorno

1. Envie `POST /commands` com Bearer de comando e JSON conforme GATE-08. O
   retorno HTTP 202 contém `schema_version=1`, `request_id` e `status=ACCEPTED`.
   A aceitação registra o comando e aguarda uma operação de passagem separada.
2. Simule a passagem com `POST /commands/{request_id}/passages`, usando o
   mesmo Bearer e JSON com `schema_version=1` e um UUID `event_id`. O simulador
   verifica a decisão `ALLOW` e a expiração. O evento enviado ao destino contém
   aquele UUID, o ID do comando, a direção do comando, o instante UTC e
   `simulated=true`. O envio usa o Bearer de retorno.
3. O simulador confirma a passagem com HTTP 201 e `status=RECORDED` somente
   após o destino devolver HTTP 201 ou 200, com `schema_version=1`,
   o mesmo `event_id` e `status=RECORDED`.
4. Receber novamente o mesmo comando devolve HTTP 200. Repetir uma passagem
   confirmada devolve o recibo existente com HTTP 200, sem novo envio.
   Reutilizar o ID com conteúdo divergente, tentar outro evento para o mesmo
   comando ou simular passagem de um comando `DENY` retorna 409.
   Comando expirado para nova operação retorna 410.
5. Se o retorno falhar, a API devolve 502 ou 504. Basta reenviar o mesmo
   `event_id` para entregar o evento já registrado com o instante original,
   inclusive após o fim da validade. Uma nova passagem exige autorização válida
   no instante da ocorrência. O destino deduplica pelos mesmos identificadores.

Para testar falha do equipamento, configure `ACADEMIA_TURNSTILE_FAULT` como
`UNAVAILABLE` (HTTP 503) ou `TIMEOUT` (HTTP 504 após uma espera controlada),
reinicie e envie um comando. Esses modos impedem registrar o comando. O
padrão `NONE` mantém o fluxo normal.

O [ensaio automatizado](../testes/comandos.md#acs-07--simulador-de-catraca)
usa um receptor HTTP de teste. A rota de recepção do AcademIA integra a
entrega do ACS-03. Frequência e lotação dependem da passagem confirmada pelo
motor de acesso e ficam sob responsabilidade do AcademIA.
