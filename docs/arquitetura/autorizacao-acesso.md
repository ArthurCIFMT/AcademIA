# Decisão de acesso e passagem simulada — ACS-03

O motor consome o identificador interno de uma tentativa de reconhecimento
gravada por ACS-02. A sessão de atendente e o CSRF protegem a operação.
O cliente e a direção vêm da identificação persistida. O [ACS-04](confirmacao-manual.md)
vincula uma confirmação manual auditada à falha facial e usa o mesmo motor.

| Operação | Contrato |
|---|---|
| `POST /api/v1/atendimento/acessos/{event_id}/autorizacao` | Gera decisão e comando, com HTTP 201. Repetir a operação retorna HTTP 200 e pode reenviar um comando pendente ou com falha usando o mesmo UUID. |
| `POST /api/v1/acesso/catraca/passagens` | Recebe retorno autenticado do simulador. Uma confirmação válida retorna 201. O mesmo evento e conteúdo retornam 200, e conflito de chave, corpo ou direção retorna 409. |

O recibo de autorização expõe ALLOW/DENY, motivo, matrícula consultada,
regra e instante aplicados, além do estado e UUID do comando. O ponto de acesso
usa a modalidade local configurada, inicialmente **Musculação**. Cada
identificação deve ser recente, com janela inicial de 60 segundos.

## Regras e concorrência

- Entrada exige identificação positiva, conta e perfil de cliente ativos,
  matrícula vigente e modalidade compatível. O financeiro não faz parte
  dessa decisão no modelo acadêmico.
- O limite usa entradas confirmadas mais reservas ainda válidas daquele
  cliente no dia civil de São Paulo. Uma autorização de entrada vence em até
  30 segundos ou na virada do dia, o que ocorrer primeiro. Saída exige uma
  identidade reconhecida e recente, com direção própria e sem reservar entrada.
- A transação serializa decisões e confirmações por cliente. Uma decisão é única
  por identificação e congela os parâmetros aplicados. A decisão e o comando
  são gravados antes do envio HTTP. O simulador deduplica o UUID do comando.
- A confirmação do comando muda seu estado para ACEITO. Falha ou timeout
  de envio é registrada em FALHOU. Uma reserva ainda vigente fica retida,
  inclusive em timeout, porque o destinatário pode ter aceitado o comando.
- O primeiro retorno deve chegar antes da expiração e indicar um instante
  entre a decisão e a recepção. Deve corresponder ao UUID e à direção de um
  comando ALLOW. Cada comando aceita até uma passagem. Um retorno duplicado
  já confirmado continua idempotente após a expiração.
- A passagem confirmada é um evento `PASSAGEM_SIMULADA`, separado de
  `IDENTIFICACAO`, e é gravada atomicamente com CONFIRMADO no comando.
  A mesma transação atualiza a [projeção de frequência e lotação](frequencia-lotacao.md).
  O limite diário continua contando entradas confirmadas e reservas da autorização.

## Execução local

O backend reutiliza as chaves privadas `ACADEMIA_TURNSTILE_COMMAND_TOKEN`
e `ACADEMIA_TURNSTILE_CALLBACK_TOKEN`, uma por sentido. O destino de
comandos usa `ACADEMIA_TURNSTILE_URL` e só aceita loopback. A configuração
de modalidade, janela, validade e timeout está no `.env.example`.
O [guia da catraca](../instalacao/catraca-ficticia.md) descreve a operação
nativa com o iniciador e como provocar uma passagem simulada.
