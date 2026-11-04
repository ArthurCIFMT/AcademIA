# Contexto de execução — AcademIA

## Uso

Este arquivo acompanha o prompt operacional escolhido explicitamente. O prompt
mestre de planejamento é `00-prompt-mestre.md` e não deve ser executado junto como
uma segunda tarefa. O contrato comum está em `00-contrato-operacional.md`.

## Texto do prompt

Você trabalha no projeto **AcademIA**, uma aplicação acadêmica para gestão de
academia e geração assistida de fichas de treino.

### Missão

Implementar o sistema incrementalmente por prompts operacionais pequenos,
testáveis e rastreáveis. Preserve o domínio, o histórico e os limites entre
módulos. Não antecipe capacidades de prompts futuros.

### Leitura obrigatória

Antes de agir:

1. leia integralmente o `AGENTS.md` aplicável;
2. leia `docs/requisitos/contexto-e-escopo.md`;
3. leia os RF, RN, RNF e MRF citados pelo prompt operacional;
4. leia os ADRs e documentos arquiteturais citados;
5. verifique dependências e estado em `docs/prompts/README.md`;
6. examine o estado e o diff do repositório sem apagar alterações alheias.

### Precedência e conflitos

Dentro do material do projeto, considere a seguinte precedência:

1. solicitação atual e explícita do responsável;
2. `AGENTS.md`;
3. requisitos e ADRs aprovados;
4. prompt operacional vigente;
5. este contexto de execução como orientação geral.

Especificidade não autoriza contrariar uma regra superior. Se houver conflito,
dependência ausente ou decisão ainda aberta que mude materialmente a solução,
interrompa a implementação e relate o gate; não escolha silenciosamente.

### Contexto funcional permanente

- Um usuário pode acumular papéis de cliente, administrador, atendente e instrutor.
- Cliente e funcionário são perfis de domínio vinculados à identidade.
- A designação cliente–instrutor preserva histórico e responsabilidade.
- A instalação e os cadastros possuem caminho de bootstrap/primeiro acesso,
  distinto do link de onboarding.
- O onboarding e as avaliações fornecem contexto versionado para o treino.
- Exercícios formam catálogo; prescrição pertence ao item da ficha.
- Equipamentos disponíveis são restrição obrigatória no MVP; administrador mantém
  inventário e gerador/publicador validam recursos por contrato.
- Reter até 15 versões publicadas completas incluindo vigente; aplicar RF-17/RF-35
  preservando metadados e execuções existentes. Saída ao usuário é em português,
  com fontes estrangeiras permitidas e evidência original rastreável.
- O backend publica treino validado e o cliente pode consultá-lo e usar o chat
  sem aceite prévio do instrutor. Validação técnica não é aceite profissional.
- O instrutor designado aceita/rejeita posteriormente; modificação cria versão.
- Publicação verifica onboarding/restrições e versão-base; parecer identifica a
  versão avaliada e não é herdado por novas versões.
- Dados de clientes diferentes nunca compartilham contexto de IA.
- Orquestrador coordena chat, triagem de resumo e geração/adaptação com busca
  semântica fixa. Não implementar planner, pesquisa iterativa ou cadeia de agentes.
- Até uma geração no chat; até uma análise de triagem e uma geração na ficha,
  com limites globais e validações em código (MRF01–MRF15/RNF-18).
- O RAG recupera somente documentos e versões aprovados; falta de suporte,
  conflito e falha técnica têm encerramentos distintos e não contornam bloqueios.
- Regras críticas e numéricas são validadas por código, não somente por LLM/RAG.
- Reconhecimento facial por API real é separado da autorização e da catraca fictícia.
- Matrícula pelo atendente, sem pagamento obrigatório → foto de referência → nova
  captura facial → decisão → simulador externo. Financeiro continua tardio e não
  bloqueia matrícula nem acesso acadêmico com matrícula válida.
- Consulte `docs/arquitetura/fluxos-atualizados.md` para os contratos e estados.
- Docker é fase final, depois do MVP e da maioria dos módulos.

### Arquitetura permanente

- Prefira monólito modular até que um ADR aprovado determine o contrário.
- Use JSON em REST, eventos e integrações; use tipos internos nas chamadas locais.
- Cada módulo possui seus dados e contratos; não acesse repositórios internos de
  outro módulo diretamente.
- Mudança de schema acompanha migration e teste da capacidade que a utiliza.
- Efeitos externos e eventos repetíveis precisam de idempotência.
- Timestamps são consistentes e rastreáveis.
- Falhas de IA, e-mail ou integração não podem corromper o estado de domínio.

### Protocolo de execução

1. Confirme objetivo, dependências, arquivos permitidos e itens fora de escopo.
2. Faça inspeções somente leitura antes de editar.
3. Implemente a menor mudança que satisfaça todos os critérios.
4. Adicione ou ajuste testes proporcionais ao risco.
5. Execute os comandos do prompt; não declare testes que não executou.
6. Revise o diff e a rastreabilidade.
7. Faça somente a operação Git explicitamente autorizada.
8. Atualize o estado do prompt quando a política Git permitir.

### Critério global de pronto

A entrega só está pronta quando:

- todos os critérios do prompt foram observados;
- os testes obrigatórios passaram;
- o diff está dentro do escopo;
- contratos, migrations e documentação afetados estão coerentes;
- nenhuma decisão aberta foi disfarçada como implementação;
- arquivos locais e repositório remoto estão sincronizados quando autorizado.

### Relatório final

Informe objetivamente:

- resultado implementado;
- arquivos alterados;
- migrations/contratos relevantes;
- testes executados e resultados;
- riscos, gates ou pendências;
- próximo prompt desbloqueado.
