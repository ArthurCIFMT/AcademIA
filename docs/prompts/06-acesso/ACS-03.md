# ACS-03 — Motor de autorização de entrada

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: ACS-02, MEM-01, ACS-07.
- Requisitos: RF-21, RF-36, RF-37; RN-06, RN-07, RN-24, RN-35, RN-36.
- Módulos: MOD-07, MOD-08.

## Objetivo e contexto

Entregar motor de autorização de entrada, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/authorization/**`
- `backend/app/modules/access/integrations/turnstile/**`
- `backend/app/contracts/memberships/**`
- `backend/tests/access/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Aplicar identidade, conta, matrícula, validade, modalidade e limite por contrato.
2. Definir semântica de evento: tentativa/decisão é distinta de passagem confirmada pela catraca.
3. Retornar código de decisão e registrar regra/instante utilizados.
4. Enviar comando autenticado/idempotente à API fictícia de ACS-07, com validade
   e correlação; confirmação de comando não significa passagem.
5. Receber passagem simulada autenticada e correlacionada com autorização válida;
   timeout, negação ou repetição não gera sucesso nem registro duplicado.

## Critérios de aceite

- Cobrir CA-21.5/CA-21.6: conta/perfil cliente, matrícula e limites são validados
  separadamente da correspondência facial e do financeiro. Compra paga sem
  matrícula é negada; matrícula válida sem pagamento continua elegível.

- Sem matrícula/vencida, modalidade incompatível ou limite excedido nega entrada.
- Reconhecimento válido sozinho não permite acesso.
- Matrícula vigente permite seguir as regras de acesso sem pagamento registrado
  e sem consulta obrigatória ao módulo financeiro.
- Concorrência não ultrapassa limite; recusa e falha externa não contam presença.

## Testes obrigatórios

BE com tabela de decisão e relógio; INT; API; troca HTTP real com o simulador,
incluindo negação, expiração, timeout e comando/passagem repetidos.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Aplicar bloqueio financeiro não configurado ou calcular frequência de tentativa negada.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
