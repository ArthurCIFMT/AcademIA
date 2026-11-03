# PES-03 — Designação de instrutor responsável

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: PES-01, PES-02.
- Requisitos: RF-34; RN-03, RN-04, RN-11, RN-31, RN-33.
- Módulos: MOD-02.

## Objetivo e contexto

Entregar designação de instrutor responsável, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/assignments/**`
- `backend/tests/assignments/**`
- `frontend/src/features/assignments/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Criar vínculo histórico, troca de responsável e consulta dos clientes designados.
2. Aplicar regra de um principal ativo conforme ADR e evitar dupla designação concorrente.
3. Atualizar política de leitura profissional via contrato, sem acessar tabelas internas de outro módulo.

## Critérios de aceite

- Somente instrutor ativo pode receber designação.
- Troca encerra vínculo anterior e preserva datas e autor.
- Instrutor sem vínculo não lê dados de saúde; concorrência mantém um principal vigente.

## Testes obrigatórios

BE; INT com concorrência; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Distribuição automática de carga e múltiplos principais sem regra aprovada.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
