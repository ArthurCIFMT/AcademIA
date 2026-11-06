# PES-01 — Cadastro e manutenção de funcionários

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: IAM-02, IAM-03, IAM-04, FND-08, NTF-01.
- Requisitos: RF-07, RF-08; RN-01, RN-03, RN-04, RN-26, RN-33.
- Módulos: MOD-01.

## Objetivo e contexto

Entregar cadastro e manutenção de funcionários, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/people/**`
- `backend/tests/people/**`
- `frontend/src/features/staff/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

Aplicar a matriz de estados conta/perfis de IAM-02. A inativação de funcionário
remove suas permissões operacionais conforme a decisão registrada; preserva
eventual perfil cliente ativo quando a conta global continua ativa (ADR-002).

1. Criar API e telas administrativas de listagem, cadastro, atualização e inativação.
2. Atribuir papéis operacionais conforme política; manter histórico e auditoria.
3. Evitar cadastro parcial quando criação de identidade ou perfil falhar.
4. Fechar primeiro acesso pelo mecanismo escolhido em IAM-02; se houver convite,
   registrar envio/expiração e recuperação de falha pelo adapter de notificações.

## Critérios de aceite

- Administrador cadastra e reencontra funcionário por nova consulta.
- E-mail duplicado/dados inválidos não deixam perfil parcial.
- Funcionário inativado perde operações e histórico permanece.
- Funcionário recém-cadastrado consegue estabelecer credencial/sessão pelo fluxo
  documentado, sem gerar outra identidade para a mesma pessoa.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Folha de pagamento e gestão trabalhista.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
