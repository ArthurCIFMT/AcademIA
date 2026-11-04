# ACS-07 — API externa fictícia de catraca

## Metadados

- Fase: Pós-MVP / base do acesso.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-06, GATE-08.
- Requisitos: RF-37; RN-06, RN-09, RN-32; RNF-04, RNF-17.
- Módulos: MOD-07.

## Objetivo e contexto

Entregar api externa fictícia de catraca, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte requisitos citados, modelo lógico, ADRs aceitos e os
[fluxos atualizados](../../arquitetura/fluxos-atualizados.md).
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `simulators/turnstile/**`
- `backend/tests/contracts/turnstile/**`
- `docs/instalacao/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar serviço HTTP separado que simula equipamento, com REST/JSON/OpenAPI e
   execução local sem Docker; framework segue ADR/contrato aceito.
2. Receber POST /commands autenticado com request_id, access_decision_id,
   direction, decision ALLOW/DENY, expires_at e client_id quando identificado.
3. Confirmar recebimento separadamente de passagem; permitir produzir retorno
   autenticado e configurado com event_id, request_id, occurred_at e simulated=true.
4. Rejeitar expiração, divergência de conteúdo na mesma chave e credencial inválida;
   simular timeout/falha deterministicamente, sem converter erro em sucesso.
5. Documentar inicialização, configuração e ensaio para integração em ACS-03;
   destino de callback é fixado na configuração, não recebido livremente no comando.

## Critérios de aceite

- Nenhum algoritmo facial é simulado como prova de biometria; este serviço só representa a catraca.
- Comando repetido é idempotente; confirmação de comando não cria passagem sozinha.
- DENY/expirado não produz passagem autorizada; callback tem correlação e autenticação.
- Fluxo permite demonstrar ALLOW, DENY, timeout e repetição por chamadas HTTP reais.
- Serviço e registros identificam explicitamente passagem simulada, sem hardware.

## Testes obrigatórios

BE; API; INT com servidor HTTP do simulador e falhas/replays controlados.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Hardware, algoritmo facial, provisionamento de API paga e Docker/Compose.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
