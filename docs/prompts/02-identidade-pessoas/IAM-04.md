# IAM-04 — Login e sessão no frontend

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-07, IAM-01, IAM-02, IAM-03.
- Requisitos: RF-04, RF-05; RN-02, RN-04; RNF-14.
- Módulos: MOD-01.

## Objetivo e contexto

Entregar login e sessão no frontend, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `frontend/src/features/auth/**`
- `frontend/src/app/**`
- `frontend/src/lib/api/**`
- `frontend/tests/auth/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Integrar fluxo de login aceito e navegação por papéis.
2. Tratar expiração, logout e erros 401/403 sem ciclos infinitos.
3. Usar tratamento de sessão definido no ADR sem expor segredos no bundle.

## Critérios de aceite

- Login válido abre área permitida; inválido não abre sessão.
- Acesso direto a rota protegida exige sessão e 403 apresenta estado adequado.
- Após logout/expiração a interface não continua exibindo dados protegidos.

## Testes obrigatórios

FE; API; roteiro de integração navegador-backend.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Aprovar acesso no frontend sem validação de backend.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
