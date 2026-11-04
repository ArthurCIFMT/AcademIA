# TRN-04 — Ficha atual no celular e exportação autorizada

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: TRN-03, IAM-04.
- Requisitos: RF-16, RF-17; RN-05, RN-28, RN-37, RN-38, RN-39; MRF07.
- Módulos: MOD-04.

## Objetivo e contexto

Entregar ficha atual no celular e exportação autorizada, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/training/**`
- `backend/tests/training/**`
- `frontend/src/features/my-training/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Expor versão atual publicada e parecer separado na tela por dias/microciclos.
2. Mostrar exercício, cadência, séries, repetições, intervalo e observações.
3. Disponibilizar exportação JSON consolidada autenticada; outro formato depende de requisito.

## Critérios de aceite

- Cliente vê ficha própria publicada com parecer PENDENTE, ACEITO ou REJEITADO;
  sem ficha recebe estado vazio. Nenhum desses pareceres impede consulta/chat.
- Trocar ID na consulta/exportação não revela treino de terceiro.
- Conteúdo excluído por RF-17/RF-35 não é retornado, nem por URL direta
  ou exportação; metadados de auditoria não reconstituem a prescrição na tela.
- Prescrição e versão exibidas correspondem ao banco e são legíveis em celular.
- Histórico consultável/exportável possui no máximo 15 versões completas incluindo
  vigente; metadados de exclusão não reconstituem conteúdo antigo.
- Conteúdo ao usuário é em português; equipamento que ficou indisponível é
  sinalizado sem reescrever ficha histórica ou trocar exercício silenciosamente.

## Testes obrigatórios

API; INT; FE; verificar exportação e estados vazio/erro.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Ocultar treino publicado ou bloquear chat por falta de aceite profissional.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
