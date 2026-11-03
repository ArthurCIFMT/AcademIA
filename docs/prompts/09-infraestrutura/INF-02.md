# INF-02 — Compose dos serviços selecionados

## Metadados

- Fase: Infraestrutura final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: INF-01.
- Requisitos: RNF-05, RNF-09, RNF-11, RNF-12.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar compose dos serviços selecionados, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `compose.yaml`
- `infra/**`
- `.env.example`
- `docs/instalacao/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Integrar frontend, backend, PostgreSQL, identidade escolhida, banco vetorial, e-mail e worker se existente.
2. Usar versões compatíveis fixadas, variáveis documentadas e políticas de healthcheck.
3. Adicionar migrations como etapa explícita, sem apagar dados ao subir.

## Critérios de aceite

- Compose válido sobe serviços e frontend alcança API com identidade correta.
- Backend alcança bancos/serviços por nomes da rede.
- Serviço ainda não utilizado não é incluído por suposição.

## Testes obrigatórios

INF: validação Compose e smoke de comunicação; API smoke.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Trocar arquitetura para acomodar Docker ou utilizar modo inseguro de desenvolvimento como produção.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
