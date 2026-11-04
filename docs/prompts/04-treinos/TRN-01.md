# TRN-01 — Catálogo de exercícios

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, IAM-03, IAM-04, EQP-01.
- Requisitos: RF-15, RF-19, RF-32, RF-38; RN-20, RN-31, RN-33, RN-37; MRF05, MRF09.
- Módulos: MOD-04, MOD-10.

## Objetivo e contexto

Entregar catálogo de exercícios, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/training/**`
- `backend/tests/training/**`
- `frontend/src/features/exercises/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar cadastro, consulta, edição e inativação do catálogo para papel autorizado.
2. Separar descrição/movimento de séries, carga, descanso e ordem de prescrição.
3. Na implementação, criar seed sintético identificado para testes; conteúdo de uso real requer revisão técnica.
4. Relacionar exercício/variação a combinações de recursos obrigatórios e
   alternativas completas; dispensa de equipamento é explícita, não ausência de vínculo.
5. Expor candidatos elegíveis por contrato de disponibilidade de MOD-10; seleção
   de nova ficha considera recursos ativos e operacionais da academia.

## Critérios de aceite

- Exercício ativo aparece na seleção de nova ficha.
- Inativo desaparece da seleção e permanece nas versões históricas.
- Cliente sem permissão de manutenção não altera o catálogo.
- Todos os recursos de uma combinação são exigidos; uma alternativa completa
  disponível basta. Cadastro incompleto não libera seleção por engano.
- Exercício com recurso obrigatório ausente, inativo ou indisponível não é candidato; exercício
  explicitamente de peso corporal pode ser candidato sem equipamento.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Popular recomendações clínicas inventadas ou prescrição específica no catálogo.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
