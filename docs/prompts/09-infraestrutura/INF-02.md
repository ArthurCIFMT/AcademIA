# INF-02 — Comunicação e prontidão dos serviços locais

## Metadados

- Fase: Infraestrutura final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: INF-01.
- Requisitos: RNF-05, RNF-09, RNF-11, RNF-12.
- Módulos: MOD-00.

## Objetivo e contexto

Validar a comunicação dos serviços locais usados na demonstração.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `.env.example`
- `docs/instalacao/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Conferir frontend e API pelo proxy local, PostgreSQL e Mailpit em loopback.
2. Verificar Qdrant persistente no processo do backend, com um único worker.
3. Testar comando e retorno da catraca fictícia em loopback. A instância
   dedicada do CompreFace continua local, conforme GATE-08.

## Critérios de aceite

- O iniciador abre os serviços locais e o frontend alcança a API.
- O backend acessa PostgreSQL, Mailpit e catraca por loopback e abre o Qdrant pelo diretório configurado.
- Migrations seguem uma etapa explícita e o iniciador preserva dados.

## Testes obrigatórios

INF: smoke de comunicação local e do iniciador; API smoke.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Compose da aplicação, Qdrant servidor e pagamentos por integração externa.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
