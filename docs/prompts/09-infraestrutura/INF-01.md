# INF-01 — Dockerfiles da aplicação

## Metadados

- Fase: Infraestrutura final.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: PG-01, PG-03.
- Requisitos: RNF-10, RNF-11; RNF-08.
- Módulos: MOD-00.

## Objetivo e contexto

Entregar dockerfiles da aplicação, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/Dockerfile`
- `frontend/Dockerfile`
- `backend/.dockerignore`
- `frontend/.dockerignore`
- `infra/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar imagens a partir dos comandos locais já validados e dependências fixadas.
2. Configurar build frontend, processo backend e usuário/arquivos necessários.
3. Evitar segredos na imagem e validar artefatos produzidos.

## Critérios de aceite

- Build de ambas imagens conclui e inicia processo esperado.
- Imagem não contém .env, credenciais ou dados de cliente.
- Configuração por ambiente funciona e guia local continua válido.

## Testes obrigatórios

INF: build e smoke das imagens; suites locais afetadas; DOC.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Começar antes do MVP e maioria dos módulos ou instalar Docker sem autorização necessária.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
