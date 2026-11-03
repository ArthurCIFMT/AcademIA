# ACS-02 — Endpoint de eventos faciais externos

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-06, ACS-01.
- Requisitos: RF-20, RF-21; RN-06, RN-07; RNF-04, RNF-17.
- Módulos: MOD-07.

## Objetivo e contexto

Entregar endpoint de eventos faciais externos, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/events/**`
- `backend/tests/access/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Acordar JSON de evento: ID externo, fonte, identidade, confiança, instante e direção.
2. Autenticar origem, validar limites de payload e rejeitar replays conforme contrato.
3. Persistir recebimento idempotente e separar identidade reconhecida da decisão de entrada.

## Critérios de aceite

- JSON malformado ou credencial inválida não processa evento.
- Mesmo evento recebido duas vezes não duplica registro.
- Identidade desconhecida e confiança inferior a 95% não viram reconhecimento positivo.

## Testes obrigatórios

API com exemplos contratados; BE; INT incluindo duplicidade e concorrência.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Liberar catraca apenas porque rosto foi reconhecido.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
