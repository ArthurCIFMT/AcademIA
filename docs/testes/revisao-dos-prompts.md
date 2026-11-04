# Revisão antes da implementação

Data: 2026-11-04. Base anterior: `055e042fee218260b418ade88bc7e03190fdac77`.
Estado: REVISADA_DOCUMENTALMENTE; implementação e gates técnicos ainda pendentes.

Esta é a revisão vigente do planejamento; substitui os snapshots contraditórios
de contagem/estado deste arquivo. Histórico completo no Git. Não implementa
módulos, aprova corpus/políticas clínicas ou encerra gates por inferência.

## Resultado e fontes

O planejamento tem 37 RFs, 39 RNs, 17 RNFs, 19 MRFs/110 critérios, 13 módulos e
61 cartões. Continua monólito modular Python, PostgreSQL operacional e banco
vetorial especializado para literatura aprovada. Mestre e cartões usam Agentic RAG.

Fontes: [RFs](../requisitos/requisitos-funcionais.md),
[RNs](../requisitos/regras-de-negocio.md),
[RNFs](../requisitos/requisitos-nao-funcionais.md),
[MRFs](../requisitos/macrorequisitos-ia-rag.md),
[decisões](../arquitetura/decisoes-iniciais.md), [manifesto](../prompts/README.md),
[MER original](../arquitetura/modelo-de-dados/original/MER_Academia_Completo_v4.drawio.png),
[revisão do MER](../arquitetura/revisao-mer.md) e
[extensão agentiva](../arquitetura/modelo-de-dados/extensao-agentic-rag.md).

## Correções realizadas

| Achado | Correção |
|---|---|
| Mestre/fundação/validação ainda apontavam 15 MRFs e aprovação funcional pendente | Alinhados a MRF01–MRF19, mantendo pendências técnicas/clínicas específicas. |
| Mestre descrevia recuperação única | Incluídos planejamento, ferramentas, suficiência, retornos à pesquisa, orçamento e encerramentos. |
| Contrato exigia modelo lógico antes de FND-03 | Leitura condicionada à existência/aplicabilidade; FND-03 continua responsável por produzi-lo. |
| FND-01 procurava títulos MRF, mas fonte é tabela | Corrigidos regex/invariável e incluído verificador DOC reutilizável. |
| Pré-condições de FND-03 divergiam dos metadados | GATE-01/02/03/05 explícitos no cartão e manifesto. FND-07 continua independente após FND-02B. |
| Checkpoint podia pedir novamente decisões já dadas | ADRs distinguem escolhas abertas de formalização de decisões expressas. |
| AI-01 exigia comando IA criado apenas em AI-06 | Regras/contratos locais usam BE/INT/API; avaliação integrada real fica em AI-06. |
| INF-01 exigia comando INF criado apenas em INF-04 | INF-01 configura build/smoke; INF-04 amplia o conjunto. Docker permanece tardio. |
| Comandos eram registrados sem escopo para o registro | FND-01 pode manter DOC; contrato permite somente atualizar a seção Comandos de AGENTS.md ao configurar testes. |
| PG-02 podia exigir VALs já concluídos | Marco exclui VAL-01–VAL-03, que são posteriores. |
| Rastreabilidade de quatro cartões FND estava apenas em prosa | Incluídas linhas explícitas para os 61 cartões. |
| ONB-02 exigia esquema aprovado sem checkpoint explícito | Campos, tipos, unidades, obrigatoriedade, validações e origem precisam ser registrados antes da parte afetada. |
| Inativação de perfil podia virar bloqueio de toda a conta | Pendência registrada em RF-03 e IAM/PES, sem escolher regra nova. |
| REC-007 tratava responsável principal como recomendação | Alinhada à decisão vigente DEC-008/RF-34. |
| RF-20/RF-31 tinham títulos divergentes do fluxo | Identificação facial e matrícula manual passam a nomear os requisitos, preservando IDs e critérios. |

Não foram retiradas funcionalidades do MVP ou introduzidos pagamento obrigatório,
aceite humano prévio, novos serviços ou novas regras clínicas.

## MER e dados

PNG original conferido também pelo XML draw.io embutido: 307 células, 18 entidades.
SHA-256: `5b57634d6936bc76c82e3f85bfa45a91626ec734af77b45e0a083e2990c1df93`.

É fonte de origem, não schema definitivo. FND-03 ainda produzirá modelo textual,
dicionário e estados com papéis acumuláveis, designação, snapshots, publicação e
parecer independentes, equipamentos, execução/evidências agentivas e matrícula
sem pagamento. Revisão do MER e extensão de dados já descrevem essas diferenças;
a imagem não foi regravada.

## Pendências legítimas por etapa

| Antes de | Decisão/dado necessário | Situação |
|---|---|---|
| FND-03/FND-04 e scaffolds dependentes | Framework/ferramentas Python, identidade, academia única/múltipla, política Git e plano local sem Docker | Gates pertinentes abertos; recomendações não são decisões aceitas. |
| IAM-02/PES-01/PES-02 | Efeito de inativar cliente que também é funcionário e vice-versa | Não presumir bloqueio global nem restrição somente do perfil. |
| ONB-02 | Esquema, unidades, obrigatoriedade, validações e origem declarada/medida | Registrar aprovação sem exigir fechar todos os provedores de IA. |
| RAG-01/AI-01 e aceite da IA | Provedores/modelos, corpus/curador, política de gravidade/liberação, limites de prescrição, orçamento, suficiência e casos esperados | GATE-04 aberto; aprovação funcional dos 19 MRFs já registrada. |
| Aceite da persistência agentiva | Retenção operacional de execuções/evidências e consistência de revisão de fontes/inventário | Limite de 15 fichas não define retenção de todo o banco. |
| Biometria pós-MVP | Hospedagem/versão/ensaio do CompreFace e fluxo alternativo | Preferir instância externa; eventual contêiner do serviço antes do Docker da aplicação exige decisão específica. |
| AUL-02/FIN-02 | Escopo de reservas e gateway/sandbox | Decisões tardias; não bloquear fundação nem exigir pagamento para matrícula. |

Pendências bloqueiam somente a parte dependente. Critérios clínicos não podem ser
inventados para fechar o checklist. A auditoria não marca cartões CONCLUIDO por si só.

## Referências e materiais

- Catálogo: 18 PDFs originais, 783 páginas, 8 PT/10 EN; hashes/tamanhos, IDs e
  caminhos/metadados conferidos. Nenhum foi aprovado automaticamente para RAG.
- URLs bibliográficas: 11 origens abriram diretamente; 7 PMC apresentaram reCAPTCHA.
  Essas sete identidades foram conferidas por fontes primárias alternativas (4)
  ou metadados primários indexados (3), com limitação de acesso. Não foi observado
  título/DOI incompatível nem URL comprovadamente inválido.
- reCAPTCHA, 403/429 e redirecionamento inacessível não foram tratados como link
  quebrado. Não houve nova coleta/download. REST/limiar do CompreFace conferem
  com as referências de [fluxos](../arquitetura/fluxos-atualizados.md).
- Preservados [32 casos](casos-documentais-rag-2026-11-04.json) e seu
  [relatório](avaliacao-documental-rag-2026-11-04.md), candidatos à avaliação futura,
  sem aprovação clínica automática.

## Limpeza

- Removida a análise histórica de IA/CompreFace anterior à ampliação do acervo,
  sem referências de entrada e substituída pelas fontes normativas, catálogo,
  avaliação de evidências e arquitetura atuais; histórico recuperável no Git.
- Este arquivo consolida snapshots antigos de contagens/estados.
- Temporários: removidos 106 arquivos de `tmp/` (20.412.160 bytes, cerca de 19,5 MiB),
  incluindo 24 scripts Python pontuais, payloads, extrações, imagens e logs.
  O caminho absoluto foi validado e não continha junctions/links simbólicos.
- Preservados `.git`, MER, PDFs, catálogo/metadados, normalizações, casos de
  perguntas/respostas e comparação didática com o professor.
- Mantido [um verificador reutilizável](../../scripts/verificar_documentacao.py),
  somente leitura, sem publicar commits, baixar arquivos ou modificar documentos.

## Verificação reproduzível

Na raiz, com Python 3.10+ e sem pacotes externos:

```text
python scripts/verificar_documentacao.py
python scripts/verificar_documentacao.py --json
git diff --check
```

DOC confere referências locais, IDs, manifesto/rastreabilidade, grafo com marcos,
hashes/tamanhos e dados dos casos. Páginas dos casos são conferidas contra o
catálogo; a contagem física dos PDFs foi conferida separadamente. URLs externas
foram verificadas por navegação; o script não depende de rede ou valida semântica
clínica. Destinos futuros apenas citados em crases não são tratados como links quebrados.

Resultado executado nesta revisão: 94 Markdown, 657 links locais, 61 cartões e
61 registros de rastreabilidade, 12 gates/marcos e grafo sem ciclos; 18 PDFs,
MER e 32 casos com 94 referências de páginas íntegros. Foram preservados os
110 critérios de IA/RAG e os 150 critérios funcionais identificados.

Também passaram oito verificações em memória do próprio auditor: intervalos
Unicode, exclusão de links em código, ID duplicado, ciclo por marco PG, link
ausente, hash divergente, página inválida e remoção do último critério. Nenhuma
dessas simulações alterou arquivos. O comando foi executado com o Python real
disponível no runtime, sem instalar bibliotecas; `git diff --check` passou.

Não foram executados testes da aplicação BE/INT/API/DB/FE/E2E/RAG/IA/INF: não há
projetos/migrations/provedores configurados. [AR-01–AR-25](agentic-rag.md) continua
especificação de testes, sem resultado real de modelo.

## Leitura manual sugerida

1. Esta revisão, contexto/requisitos e decisões abertas.
2. Mestre, contexto e contrato comuns.
3. Manifesto por dependências: fundação, identidade/designação, onboarding,
   equipamentos/catálogo/fichas e RAG/IA/testes do MVP.
4. Resolver decisões da etapa antes de executar seu cartão.
5. Pós-MVP: matrícula/acesso, complementares, financeiro e infraestrutura conforme
   dependências/escopo, sem antecipar Docker.
