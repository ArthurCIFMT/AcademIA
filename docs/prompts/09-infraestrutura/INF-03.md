# INF-03 — Rede, volumes e restrição de exposição

## Metadados

- Fase: Infraestrutura final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: INF-02.
- Requisitos: RNF-08, RNF-11, RNF-12, RNF-15.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar rede, volumes e restrição de exposição, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `compose.yaml`
- `infra/**`
- `docs/instalacao/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Restringir portas, redes de bancos e administração conforme ambiente.
2. Configurar volumes persistentes e healthchecks verificáveis.
3. Documentar regras de firewall/aplicação da plataforma; não alterar firewall do computador sem autorização.

## Critérios de aceite

- PostgreSQL e banco vetorial não ficam expostos publicamente.
- Reiniciar/recriar serviços preserva dados e referências.
- Falha em dependência aparece em healthcheck sem publicar segredos.

## Testes obrigatórios

INF: inspeção de portas, persistência e healthchecks; DOC.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Desligar firewall do host ou executar remoção ampla de volumes.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
