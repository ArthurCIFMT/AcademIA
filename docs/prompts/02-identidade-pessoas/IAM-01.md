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

1. Implementar porta de identidade/sessão do ADR-002: senha Argon2id e token opaco,
   expiração absoluta/ociosidade, revogação, CSRF e validação de origem.
2. Resolver identidade por UUID e contratos, sem e-mail como chave primária.
   Não integrar Keycloak, JWT ou OIDC neste escopo.
3. Definir interfaces dos repositórios; modelos/adapters persistentes ficam em
   IAM-02 para evitar dependência circular. Testar porta aqui com doubles;
   fluxo persistente completo é verificado após IAM-02 e no login IAM-04.
4. Configurar sessão/cookies por ambiente e mesma origem via proxy Vite.

## Critérios de aceite

- Sessão ausente, expirada/revogada, token adulterado ou origem/CSRF inválidos são recusados.
- Uma sessão resolve apenas a identidade autorizada; troca de senha/logout revoga.
- Sem sessão retorna 401; falha de persistência não concede acesso por fallback.
- Regras de papel/perfil são aplicadas em IAM-02/IAM-03, sem adiantar permissões aqui.

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
