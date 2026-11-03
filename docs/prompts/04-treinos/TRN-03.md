# TRN-03 — Workflow de revisão e aprovação da ficha

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: TRN-02, PES-03, NTF-01.
- Requisitos: RF-17, RF-35; RN-12, RN-14, RN-16, RN-17, RN-18, RN-31.
- Módulos: MOD-04, MOD-02, MOD-12.

## Objetivo e contexto

Entregar workflow de revisão e aprovação da ficha, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/training/**`
- `backend/tests/training/**`
- `frontend/src/features/training-review/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar fila, edição integral, parecer, aprovação, rejeição e ajustes.
2. Centralizar workflow para rascunhos manuais e propostas futuras da IA.
3. Ativar versão aprovada atomicamente, substituindo anterior e emitindo eventos de aviso.
4. Definir política de atualidade e conferir snapshot de avaliação/restrições,
   designação e versão-base antes de aprovar. Mudança relevante exige reavaliação
   ou nova proposta conforme essa política, sem sobrescrever silenciosamente.

## Critérios de aceite

- Instrutor vigente designado aprova; instrutor não designado é recusado.
- Dois pedidos concorrentes não deixam duas fichas atuais.
- Rejeição preserva proposta e motivo; aprovação identifica autor/revisor e instante.
- Proposta baseada em restrições ou versão-base superadas recebe o tratamento
  previsto antes da ativação; aprovação não contorna bloqueio de segurança.

## Testes obrigatórios

BE; INT com concorrência; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Reimplementar aprovação dentro do módulo de IA.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
