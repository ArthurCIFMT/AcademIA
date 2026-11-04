# IAM-02 — Usuário, papéis e perfis de domínio

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, IAM-01.
- Requisitos: RF-01, RF-04, RF-05, RF-07; RN-01, RN-02, RN-03, RN-33.
- Módulos: MOD-01.

## Objetivo e contexto

Entregar usuário, papéis e perfis de domínio, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

Pré-condição de domínio: registrar o alcance da inativação da conta e de cada
perfil/papel acumulável. RF-03/CA-03.2 não resolve sozinho se desativar cliente
também afeta seu perfil de funcionário. Não presumir desativação global nem
preservação de todos os acessos; aplicar a matriz de estados aprovada antes de
codificar a parte afetada, mantendo o histórico.

- `backend/app/modules/identity/**`
- `backend/app/modules/people/**`
- `backend/tests/identity/**`
- `backend/scripts/**`
- `docs/instalacao/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Modelar usuário, papéis acumuláveis e perfis cliente/funcionário conforme modelo lógico.
2. Garantir UUID, e-mail normalizado e identificador do provedor conforme regras aceitas.
3. Validar estado local em requisições para que inativação revogue acesso mesmo com token ainda válido.
4. Definir e implementar bootstrap idempotente do primeiro administrador conforme
   a identidade escolhida, com segredo/configuração externos e sem endpoint público
   de autoelevação. Documentar instalação vazia e primeiro login.
5. Expor o fluxo de provisionamento/primeiro acesso reutilizado pelos cadastros,
   distinguindo identidade externa, conta local e convite de onboarding.

## Critérios de aceite

- Mesmo usuário pode ser cliente e instrutor sem duplicar a identidade.
- Unicidade é aplicada pelo banco, inclusive em requisições concorrentes.
- Usuário inativado não acessa rota protegida com token anterior.
- Instalação vazia permite primeiro administrador autenticável; repetir bootstrap
  não duplica identidade nem inclui senha padrão fixa no repositório.

## Testes obrigatórios

BE; INT; DB; API.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Telas de cadastro ou inferir CPF obrigatório não aprovado.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
