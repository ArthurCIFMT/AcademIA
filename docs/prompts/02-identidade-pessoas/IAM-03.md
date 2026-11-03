# IAM-03 — Permissões e acesso a recursos

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: IAM-02.
- Requisitos: RF-05; RN-04, RN-05, RN-11, RN-28, RN-29.
- Módulos: MOD-01.

## Objetivo e contexto

Entregar permissões e acesso a recursos, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/identity/**`
- `backend/app/policies/**`
- `backend/tests/authorization/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Definir matriz de operações por papel e política de propriedade dos recursos.
2. Criar pontos de extensão para designação profissional e dados de saúde.
3. Centralizar negação por padrão e aplicar políticas também a exportações.

## Critérios de aceite

- Cliente não executa operação administrativa nem muda ID para acessar terceiro.
- Papéis acumulados permitem somente operações previstas.
- Rota chamada diretamente aplica mesma política da interface.

## Testes obrigatórios

BE; API; INT com dois clientes e funcionário sem permissão.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Usar apenas ocultação de botões como autorização.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
