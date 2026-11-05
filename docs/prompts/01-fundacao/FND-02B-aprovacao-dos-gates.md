# FND-02B — Aprovar ADRs e fechar gates

## Metadados

- Fase: Checkpoint arquitetural
- Estado inicial: CONCLUIDO — preparação documental delegada em 2026-11-04.
- Dependências: FND-02A
- Requisitos: RNF-01–RNF-18, MRF01–MRF15
- Módulos: MOD-00
- Próximo prompt desbloqueado: FND-03 conforme seus gates; FND-07 pode avançar independentemente.

## Objetivo

Apresentar as escolhas ao responsável, registrar suas decisões e fechar apenas os
gates efetivamente confirmados.

## Contexto obrigatório

- `AGENTS.md`
- `docs/prompts/00-contexto-de-execucao.md`
- `docs/prompts/00-contrato-operacional.md`
- ADRs propostos e formalizações das decisões já aceitas
- tabela de decisão criada por FND-02A
- `docs/prompts/README.md`

## Pré-condições

- FND-02A concluído.
- Responsável disponível para aprovar, alterar ou adiar as escolhas.

## Escopo permitido

- `docs/arquitetura/decisoes/**`
- `docs/arquitetura/decisoes-iniciais.md`
- `docs/requisitos/macrorequisitos-ia-rag.md`
- `docs/prompts/README.md`
- decisões arquiteturais do `AGENTS.md`.

## Fora do escopo

- Implementar qualquer ADR.
- Fechar gate com base apenas na recomendação do agente.
- Aprovar critérios de triagem da demonstração ou corpus que o responsável não forneceu/aceitou.

## Contratos e invariantes

- Decisão expressa ou seleção técnica delegada explicitamente pelo responsável
  pode registrar ADR ACEITA, identificando a origem. A delegação de 2026-11-04
  já cobre framework, campos e regras; não pedir aprovação repetida.
- Gate aberto permanece visível e bloqueia apenas os prompts dependentes.
- ADR substituído preserva histórico e aponta para o sucessor.

## Implementação obrigatória

1. Apresentar um único checkpoint conciso com escolhas e recomendações.
2. Registrar as respostas nos ADRs.
3. Registrar a aprovação funcional já autorizada de MRF01–MRF15; solicitar
   decisão somente sobre regras acadêmicas de triagem, provedores e parâmetros ainda abertos.
4. Atualizar `AGENTS.md` somente com decisões aceitas.
5. Atualizar estado e evidência de GATE-01 a GATE-07.
6. Registrar a política Git aceita antes das próximas entregas.

## Critérios de aceite

- GATE-01, GATE-03, GATE-05 e GATE-06 estão fechados antes de FND-04.
- GATE-01, GATE-02, GATE-03 e GATE-05 estão fechados antes do modelo lógico de FND-03.
- GATE-02 está fechado antes de IAM-01.
- GATE-04 está fechado antes de RAG-01/AI-01.
- MRF01–MRF15 refletem a decisão funcional vigente; parâmetros ainda indefinidos
  possuem pendência específica, sem reabrir todo o conjunto funcional.
- Gates adiados não impedem concluir o checkpoint documental, mas continuam
  bloqueando os cartões dependentes.
- Decisões aceitas estão consistentes entre ADRs, `AGENTS.md` e manifesto.

## Testes obrigatórios

- `rg -n "Status: (PROPOSTA|ACEITA|SUBSTITUIDA)" docs/arquitetura/decisoes`
- Conferência dos gates contra os ADRs referenciados.
- `git diff --check`.

## Entregáveis

- ADRs aceitos ou explicitamente pendentes.
- Gates e evidências atualizados.
- `AGENTS.md` alinhado às decisões aceitas.

## Condições de interrupção

Se o responsável adiar uma decisão, mantenha o gate aberto e não execute os
prompts que dependem dele. Não force uma escolha para liberar o grafo.

## Git

- Commit sugerido: `docs: approve foundational architecture decisions`
- Aplicar a política aprovada em GATE-05.

## Relatório final

Liste decisões aceitas, gates abertos, arquivos atualizados e prompts liberados.

## Evidência de execução documental

Executado por delegação expressa do responsável. Consultar
[prontidão](../../arquitetura/preparacao-implementacao.md) para ADRs, contratos,
modelo, verificações e próximos prompts. Não solicitar novamente as escolhas
registradas como aceitas. Não confundir esta conclusão com código/serviços funcionando.
