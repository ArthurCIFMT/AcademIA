# IAM-05 — Recuperação de acesso por e-mail

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: IAM-01, IAM-04, NTF-01.
- Requisitos: RF-06; RN-02; RNF-09, RNF-15.
- Módulos: MOD-01, MOD-12.

## Objetivo e contexto

Entregar recuperação de acesso por e-mail, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/identity/**`
- `backend/tests/identity/**`
- `frontend/src/features/auth/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar recuperação no componente responsável pelas credenciais segundo ADR.
2. Configurar e-mail de teste e token/link sem expor existência de contas na resposta pública.
3. Integrar solicitação e confirmação ao frontend ou à página do provedor aceita.

## Critérios de aceite

- Token válido permite trocar credencial e autenticar com a nova.
- Token expirado/reutilizado é recusado e senha antiga deixa de funcionar.
- Falha de envio é observável sem registrar token ou senha em logs.

## Testes obrigatórios

BE; API; FE; integração com caixa/sink de e-mail de teste.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

SMTP em Docker e envio a destinatários reais.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
