# PES-02 — Cadastro e manutenção de clientes

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: IAM-02, IAM-03, IAM-04, FND-08, NTF-01.
- Requisitos: RF-01, RF-02, RF-03; RN-01, RN-04, RN-05, RN-33.
- Módulos: MOD-01.

## Objetivo e contexto

Entregar cadastro e manutenção de clientes, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/people/**`
- `backend/tests/people/**`
- `frontend/src/features/clients/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

Aplicar a matriz de estados conta/perfis de IAM-02. Antes de inativar uma identidade
que também seja funcionário, resolver a pendência de alcance indicada em RF-03;
não implementar revogação global como consequência implícita do perfil de cliente.

1. Criar API/telas para cadastrar, pesquisar por nome/e-mail, consultar, atualizar e inativar clientes.
2. Distinguir estado da conta de matrícula, biometria e elegibilidade.
3. Permitir cadastro inicial antes de biometria e onboarding conforme modelo aceito.
4. Integrar o primeiro acesso escolhido em IAM-02. Distinguir convite de credencial
   de link de onboarding e permitir recuperar provisionamento/envio com falha.

## Critérios de aceite

- Cadastro válido retorna identificador e persiste após recarregar.
- Duplicidade ou validação rejeitada não cria dados parciais.
- Cliente não consulta terceiro; inativar preserva histórico.
- Cliente cadastrado realiza o primeiro login pelo mecanismo documentado sem
  cadastro duplicado; token de onboarding não abre sessão geral por si só.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Cobrança automática e exigir biometria para cadastrar cliente.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
