# TST-01 — Aceitação ponta a ponta do MVP

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: IAM-05, PES-03, ONB-03, ONB-04, TRN-04, AI-06.
- Requisitos: RF-01–RF-19, RF-34, RF-35; RNF-07, RNF-10, RNF-14.
- Módulos: MOD-00, MOD-01, MOD-02, MOD-03, MOD-04, MOD-05, MOD-06, MOD-12.

## Objetivo e contexto

Entregar aceitação ponta a ponta do mvp, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

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
- Caso bloqueado não chega à publicação; instrutor alheio e cliente alheio são recusados.
- Treino e chat funcionam antes do aceite; rejeição não oculta conteúdo nem conversa.
- Execução local reproduzível passa; serviço real obrigatório ausente mantém aceite pendente.
- Repetir bootstrap não duplica administrador e usuário convidado consegue o
  primeiro login; mudança de restrição durante revisão exige revalidação prevista.

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
