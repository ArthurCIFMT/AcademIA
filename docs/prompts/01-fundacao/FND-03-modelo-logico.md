# FND-03 — Revisar MER e modelo lógico

## Metadados

- Fase: Fundação de dados
- Estado inicial: BLOQUEADO até FND-02B
- Dependências: FND-01, FND-02B, GATE-01, GATE-02, GATE-03, GATE-05
- Requisitos: RF-01–RF-37, RN-01–RN-39, MRF01–MRF19
- Módulos: MOD-01–MOD-12
- Próximo prompt desbloqueado: FND-04 conforme GATE-06; FND-07 já depende apenas de FND-02B.

## Objetivo

Transformar o MER inicial em modelo lógico consistente com requisitos, papéis,
designação de instrutor, versionamento, IA/RAG e controle de acesso.

## Contexto obrigatório

- `AGENTS.md`
- `docs/prompts/00-contexto-de-execucao.md`
- `docs/prompts/00-contrato-operacional.md`
- todos os requisitos e ADRs aceitos
- `docs/arquitetura/modelo-de-dados/original/MER_Academia_Completo_v4.drawio.png`
- `docs/arquitetura/modulos.md`
- `docs/arquitetura/modelo-de-dados/extensao-agentic-rag.md`

## Pré-condições

- FND-02B concluído.
- Gates de stack, identidade, tenancy e Git fechados (GATE-01/02/03/05).
- MER original versionado e legível.

## Escopo permitido

- `docs/arquitetura/modelo-de-dados/**`
- `docs/arquitetura/modulos.md`
- `docs/arquitetura/rastreabilidade.md`
- `docs/prompts/README.md`

## Invariantes obrigatórias

- Usuário possui papéis acumuláveis.
- Cliente e funcionário são perfis vinculados à identidade.
- Designação cliente–instrutor preserva histórico.
- Estados de conta, matrícula, biometria e elegibilidade são distintos.
- Onboarding/avaliações e fichas possuem versionamento necessário.
- Conteúdo de ficha publicada não é modificado retroativamente.
- RF-35 prevê exclusão do conteúdo da rejeitada anterior quando uma ficha posterior
  também é rejeitada, mantendo metadados de auditoria e snapshots de execuções.
- Reter no máximo 15 versões publicadas completas por cliente, incluindo vigente;
  excluir conteúdo mais antigo ao publicar excedente, sem apagar auditoria/execuções
  existentes nem reutilizar versão. O limite independe do parecer.
- Equipamentos estão no MVP: modelar disponibilidade e requisitos de recursos por
  exercício/variação, com combinações/alternativas e dispensa explícita.
- `EXERCICIO` não armazena séries/carga específicas de prescrição.
- Validação técnica, publicação e parecer profissional por versão são dimensões
  independentes; consulta/chat não dependem de aceite.
- Matrícula pelo atendente independe de pagamento e precede cadastro facial;
  eventual vínculo financeiro é opcional.
- Referência facial externa, nova captura e comando/passagem simulada são distinguíveis.
- Reconhecimento externo e decisão de acesso são registros separados.
- Cobrança pode possuir múltiplas tentativas de pagamento.
- Corpus vetorial referencia fontes; dados pessoais permanecem operacionais.
- Modelar execução/etapas/evidências/avaliações e orçamento da pesquisa agentiva
  conforme a extensão, sem duplicar catálogo, inventário, publicação ou parecer.
- Distinguir estado da conta, de cada perfil e das permissões acumuladas; alcance
  da inativação de perfil ainda exige decisão explícita antes de codificar a regra.

## Fora do escopo

- Criar migration ou schema físico.
- Implementar ORM, API ou interface.
- Detalhar tabelas de pagamento além do necessário para coerência futura.
- Inventar campos clínicos não aprovados.

## Implementação obrigatória

1. Extrair a fonte XML/draw.io embutida no PNG para facilitar leitura, preservando
   o original. Catalogar entidades, atributos conceituais e ownership por módulo.
2. Corrigir cardinalidades e duplicações do MER inicial.
3. Documentar chaves, unicidades e invariantes importantes.
4. Descrever máquinas de estado de onboarding, ficha, matrícula e acesso.
5. Manter um dicionário de dados conceitual.
6. Produzir obrigatoriamente representação textual versionável em Mermaid ou DBML,
   além do dicionário de dados; artefato visual adicional é opcional.
7. Atualizar a rastreabilidade e o manifesto.

## Critérios de aceite

- Cada RF que persiste dados encontra entidade responsável.
- Relações N:N usam entidade associativa quando possuem histórico/atributos.
- Um instrutor principal vigente pode ser garantido sem perder vínculos antigos.
- Uma única ficha vigente por cliente pode ser garantida.
- Idempotência de eventos externos possui chave identificável.
- O modelo permite matrícula pelo atendente sem pagamento/comprovante nem módulo
  financeiro; validade, plano e autoria permanecem obrigatórios.
- Pontos ainda desconhecidos estão marcados, não inventados.

## Testes obrigatórios

- Revisão cruzada do modelo contra RF/RN/MRF.
- Verificação de cardinalidades e ciclos de dependência entre módulos.
- Validar a sintaxe do Mermaid/DBML com a ferramenta adotada no repositório.
- `git diff --check`.

## Entregáveis

- Modelo textual versionável.
- Dicionário de dados e máquinas de estado.
- Registro das diferenças em relação ao MER original.
- Rastreabilidade e manifesto atualizados.

## Condições de interrupção

Pare na parte afetada se ADR de tenancy/identidade ou política material de
publicação/parecer continuar aberto. Não reintroduza aceite como pré-condição:
a consulta e o chat anteriores ao parecer já foram confirmados.

## Git

- Commit sugerido: `docs: revise logical data model`
- Siga a política Git aceita em FND-02B.

## Relatório final

Resuma entidades, principais correções ao MER, validações, decisões pendentes e
prompts de scaffold desbloqueados.
