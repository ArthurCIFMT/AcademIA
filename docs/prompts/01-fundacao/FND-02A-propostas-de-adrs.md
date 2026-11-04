# FND-02A — Elaborar propostas de ADR

## Metadados

- Fase: Fundação arquitetural
- Estado inicial: BLOQUEADO até FND-01
- Dependências: FND-01
- Requisitos: RNF-01–RNF-18 e requisitos técnicos transversais
- Módulos: MOD-00
- Próximo prompt desbloqueado: FND-02B

## Objetivo

Documentar opções, recomendação e consequências para cada decisão arquitetural
aberta, sem apresentar a recomendação do agente como decisão do responsável.

## Contexto obrigatório

- `AGENTS.md`
- `docs/prompts/00-contexto-de-execucao.md`
- `docs/prompts/00-contrato-operacional.md`
- `docs/arquitetura/decisoes-iniciais.md`
- `docs/requisitos/contexto-e-escopo.md`
- `docs/requisitos/requisitos-nao-funcionais.md`

## Pré-condições

- FND-01 concluído e registrado no manifesto.
- Fontes de verdade sem conflito impeditivo.

## Escopo permitido

- `docs/arquitetura/decisoes/**`
- `docs/arquitetura/decisoes-iniciais.md`
- `docs/prompts/README.md`

## Fora do escopo

- Marcar ADR como `ACEITA` sem confirmação do responsável.
- Instalar dependências, gerar código, migrations, Dockerfiles ou Compose.
- Inventar critérios clínicos ou corpus documental.

## Contratos e invariantes

- Escolha aberta usa status `PROPOSTA`. Decisão já expressa pelo responsável
  pode ser formalizada como `ACEITA`, identificando sua origem, sem novo pedido
  de confirmação. Recomendação do agente não recebe esse tratamento.
- Cada opção registra benefícios, custos e impacto na execução local sem Docker.
- Recomendação deve ser explícita e distinguível da decisão final.

## Implementação obrigatória

1. Propor ADRs para stack Python, ferramentas de teste, identidade, tenancy, banco vetorial,
   LLM/embeddings, designação, publicação/parecer posterior, API facial real,
   matrícula independente de pagamento, catraca fictícia, financeiro tardio, política Git,
   dependências locais e governança do corpus. Decisões tardias de acesso e
   pagamentos podem permanecer pendentes nos gates correspondentes.
2. Incluir recomendação existente como opção preferencial quando aplicável.
3. Preparar uma tabela de decisão curta para o checkpoint FND-02B.
4. Atualizar o manifesto sem fechar gates.

## Critérios de aceite

- GATE-01 a GATE-06 e GATE-07 possuem decisão correspondente ou justificativa.
- MRF01–MRF15 e orquestrador com RAG semântico aparecem como escopo vigente;
  checkpoint pede somente escolhas técnicas/clínicas ou parâmetros ainda abertos.
- Nenhuma decisão ainda aberta foi copiada para `AGENTS.md` como confirmada.
- As propostas permitem resposta objetiva do responsável.

## Testes obrigatórios

- `rg -n "^# ADR|Status: PROPOSTA" docs/arquitetura/decisoes`
- Verificação dos links dos ADRs a partir da tabela de decisão.
- `git diff --check`.

## Entregáveis

- ADRs de escolhas abertas com status `PROPOSTA` e formalização das decisões já aceitas.
- Tabela de decisão para FND-02B.
- Manifesto atualizado.

## Condições de interrupção

Somente conflito insolúvel nas fontes de verdade. Dúvidas entre alternativas não
bloqueiam a elaboração da proposta; devem aparecer no checkpoint.

## Git

- Commit sugerido: `docs: propose foundational architecture decisions`
- Até GATE-05, use a política provisória explicitamente autorizada pelo
  responsável na conversa vigente; caso não exista, mantenha as mudanças locais.

## Relatório final

Liste ADRs propostos, recomendação de cada um, dúvidas e o checkpoint necessário.
