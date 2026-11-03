# IAM-01 — Adaptador de autenticação

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-06, GATE-02, GATE-06.
- Requisitos: RF-04; RN-02, RN-04; RNF-08.
- Módulos: MOD-01.

## Objetivo e contexto

Entregar adaptador de autenticação, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/identity/**`
- `backend/tests/identity/**`
- `.env.example`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar estratégia aceita em ADR; para OIDC validar assinatura, emissor, audiência e expiração.
2. Definir vínculo estável entre identidade externa/local e usuário, sem usar e-mail como chave primária.
3. Documentar execução/configuração local do provedor sem Docker.

## Critérios de aceite

- Credencial/token válido é aceito; expirado, adulterado ou de emissor/audiência inválidos é recusado.
- Rota protegida sem credencial retorna 401.
- Indisponibilidade do provedor não permite acesso por fallback inseguro.

## Testes obrigatórios

BE; API; integração local do mecanismo aceito, com evidência de autenticação real.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Escolher outra autenticação por conveniência ou implementar toda gestão de pessoas.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
