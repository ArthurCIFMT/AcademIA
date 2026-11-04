# TRN-03 — Publicação e avaliação posterior da ficha

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: TRN-02, PES-03, NTF-01.
- Requisitos: RF-17, RF-35; RN-12, RN-14, RN-16, RN-17, RN-18, RN-31, RN-37, RN-38.
- Módulos: MOD-04, MOD-02, MOD-12.

## Objetivo e contexto

Entregar publicação e avaliação posterior da ficha, respeitando os critérios abaixo.
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

1. Separar publicação da validação técnica e do parecer profissional por versão.
2. Publicar conteúdo validado sem aceite prévio e criar fila/aviso para avaliação posterior.
3. Permitir ao instrutor designado aceitar/rejeitar com parecer, autor e data;
   edição integral cria nova versão, nunca altera conteúdo publicado.
4. Conferir snapshot/restrições e versão-base antes de publicar; mudança relevante
   exige revalidação. Parecer aplica-se somente à versão avaliada.
5. Garantir uma versão atual por cliente atomicamente. Rejeitar a vigente mantém
   consulta/chat. Ao rejeitar uma ficha posterior, excluir conteúdo/itens da
   rejeitada anterior e manter a nova rejeitada (CA-35.7/CA-35.8), retirando o
   conteúdo antigo de API, exportações e contexto ativo/cache de chat.
6. Preservar metadados de auditoria e snapshots de treinos executados. Aplicar
   exclusão/troca idempotente e transacional; parecer atrasado não elimina a mais
   recente. Gerar/publicar ou aceitar ficha não dispara a exclusão específica por rejeição.
7. Aplicar independentemente RF-17: publicar a 16ª versão remove conteúdo das mais
   antigas até restarem 15, preservando vigente, auditoria e execuções. Esse limite
   pode expirar versão aceita/rejeitada; não há exceção por parecer. Publicação e
   retenção são atômicas/idempotentes, inclusive em duas publicações concorrentes.

## Critérios de aceite

- Instrutor vigente designado avalia; instrutor não designado é recusado.
- Cliente consulta treino e usa chat com parecer PENDENTE; aceite não é barreira.
- Dois pedidos concorrentes não deixam duas fichas atuais.
- Rejeição preserva versão visível e motivo; aceite identifica revisor e instante.
- Nova versão começa PENDENTE e não herda aceite da versão anterior.
- A rejeitada fica visível até rejeição de versão posterior: A rejeitada → B
  publicada PENDENTE mantém A; rejeitar B exclui conteúdo de A e conserva B.
- Aceite de B, falha de geração, replay e parecer fora de ordem não apagam A
  indevidamente pela regra de rejeição; concorrência não mantém duas rejeitadas
  nem elimina auditoria. Excedente pode ser removido independentemente por RF-17.
- Testar 15 → 16 versões, publicações concorrentes, falha transacional, exclusão
  de versão antiga aceita/rejeitada, preservação da vigente e numeração crescente.
- Conteúdo baseado em restrições/versão-base superadas é revalidado antes de
  publicar; parecer profissional não contorna bloqueio de segurança.

## Testes obrigatórios

BE; INT com concorrência; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Duplicar avaliação no módulo de IA ou condicionar consulta/chat ao aceite.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
