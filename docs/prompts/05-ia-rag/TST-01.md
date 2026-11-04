# TST-01 — Aceitação ponta a ponta do MVP

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: IAM-05, PES-03, ONB-03, ONB-04, EQP-01, TRN-04, AI-06.
- Requisitos: RF-01–RF-19, RF-32, RF-33, RF-34, RF-35; RN-37, RN-38, RN-39; RNF-07, RNF-10, RNF-14; MRF04, MRF16, MRF17, MRF18, MRF19 (integração RAG/IA).
- Módulos: MOD-00, MOD-01, MOD-02, MOD-03, MOD-04, MOD-05, MOD-06, MOD-10, MOD-12.

## Objetivo e contexto

Entregar aceitação ponta a ponta do mvp, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.
Consulte o [fluxo agentivo](../../arquitetura/agentic-rag.md), a
[extensão de dados](../../arquitetura/modelo-de-dados/extensao-agentic-rag.md)
e o [conjunto de testes](../../testes/agentic-rag.md). Suíte significa conjunto
organizado de testes; sigla de teste não é comando pronto de terminal.

## Escopo permitido

- `frontend/tests/e2e/**`
- `backend/tests/acceptance/**`
- `docs/testes/**`
- `docs/prompts/README.md`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Configurar E2E e percorrer instalação vazia/bootstrap, primeiro acesso,
   cadastro, designação, convite, onboarding, treino publicado, consulta/chat antes
   do parecer, aviso, avaliação posterior e nova versão.
2. Exercitar também ficha manual, recuperação, rejeição visível, cliente sem
   instrutor, bloqueio de saúde e acesso indevido.
3. Registrar aceite do MVP PG-01 somente com critérios e evidências por requisito.

## Critérios de aceite

- Fluxo completo persiste após logout/login e recarga.
- Administrador cadastra recursos e geração só usa equipamentos disponíveis;
  revalidação impede publicar prescrição inviável após alteração do inventário.
- Publicar 16 versões deixa 15 completas consultáveis incluindo vigente; testar
  rejeitadas, exclusões, exportação/chat, concorrência e preservação de auditoria/execuções.
- Consulta em português usa fonte PT/EN e resposta é em português com sentido,
  unidades e negações preservados.
- Caso bloqueado não chega à publicação; instrutor alheio e cliente alheio são recusados.
- Treino e chat funcionam antes do aceite; rejeição não oculta conteúdo retido nem conversa.
- Execução local reproduzível passa; serviço real obrigatório ausente mantém aceite pendente.
- Repetir bootstrap não duplica administrador e usuário convidado consegue o
  primeiro login; mudança de restrição durante revisão exige revalidação prevista.

## Complementos obrigatórios para Agentic RAG

Acrescentar apenas cenários de RAG/IA ao E2E já previsto:

- AR-03/04: solicitação demanda pesquisa complementar/contexto e gera resposta
  fundamentada em português com comportamento agentivo observado no backend.
- AR-06/13: necessidade de dados, abstenção e falha/limite técnico têm estados
  distintos; preservam consulta/chat e ficha vigente, sem publicação indevida.
- AR-16/17/21/22: fonte revogada ou recurso indisponível não sustenta publicação;
  ferramentas/contexto respeitam retenção e parecer posterior existentes.
- Repetir pedido ou recarregar acompanhamento não reinicia publicação/orçamento.
  Não ampliar escopo de identidade, matrícula, financeiro, acesso ou infraestrutura.

## Testes obrigatórios

E2E; API; INT; BE; FE; IA/RAG nas suites críticas. Registrar comando E2E.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Docker, integração financeira e fingir navegação E2E com API isolada.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
