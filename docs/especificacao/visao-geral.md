# SPEC — Especificação completa do AcademIA para reconstrução

Versão documental: 1.0. Revisão: 2026-11-11.
Natureza: especificação de uma aplicação web acadêmica para uma única academia.
Esta revisão consolida a especificação existente e incorpora seu conteúdo
para transporte a outra IA. Requisitos e decisões conservam IDs e autoridade.

<!-- SUMARIO_SPEC -->

## 1. Finalidade e leitura

Este arquivo reúne a definição do produto: capacidades, regras, arquitetura,
dados, contratos e critérios de verificação. Serve de entrada para compreender,
modificar ou reconstruir funcionalmente o sistema, inclusive com outra IA.

A manutenção da especificação é modular. Este arquivo reúne a visão geral e
o conteúdo das fontes responsáveis por cada assunto. As cópias incorporadas
são geradas a partir dessas fontes, evitando versões independentes de requisitos.

| Documento | Função |
|---|---|
| Este SPEC e suas fontes vinculadas | Definem o comportamento e a estrutura esperados do sistema. |
| [AGENTS.md](../../AGENTS.md) | Estabelece instruções permanentes para trabalhar no repositório. |
| [Prompt mestre](../../docs/prompts/00-prompt-mestre.md) | Orienta a elaboração/revisão de um plano a partir da especificação. |
| [Prompts operacionais](../../docs/prompts/README.md) | Delimitam tarefas de implementação, dependências, entregáveis e testes. |
| Código, migrations e lockfiles | Materializam uma implementação reproduzível de um determinado commit. |

Leia AGENTS.md, este SPEC e as fontes da capacidade afetada antes de planejar ou
implementar. O [manifesto](../../docs/prompts/README.md) registra o estado de cada cartão.
Uma capacidade especificada pode ainda estar pendente de implementação.

## 2. Fontes oficiais e resolução de divergências

| Assunto | Fonte detalhada |
|---|---|
| Domínio, atores, escopo e glossário | [Contexto e escopo](../../docs/requisitos/contexto-e-escopo.md) |
| Comportamentos e critérios de aceite | [Requisitos funcionais](../../docs/requisitos/requisitos-funcionais.md) |
| Invariantes do domínio | [Regras de negócio](../../docs/requisitos/regras-de-negocio.md) |
| Segurança, qualidade e restrições técnicas | [Requisitos não funcionais](../../docs/requisitos/requisitos-nao-funcionais.md) |
| Capacidades e critérios específicos da IA | [Macrorequisitos IA/RAG](../../docs/requisitos/macrorequisitos-ia-rag.md) |
| Origem e normalização dos requisitos | [Registro de normalização](../../docs/requisitos/registro-de-normalizacao.md) |
| Decisões técnicas aprovadas | [ADRs aceitos](../../docs/arquitetura/decisoes/README.md) |
| Responsabilidade e fronteiras dos módulos | [Módulos](../../docs/arquitetura/modulos.md) |
| Fluxos do domínio | [Fluxos atualizados](../../docs/arquitetura/fluxos-atualizados.md) |
| Dados relacionais previstos | [DBML](../../docs/arquitetura/modelo-de-dados/modelo-logico.dbml), [JSON](../../docs/arquitetura/modelo-de-dados/modelo-logico.json), [dicionário](../../docs/arquitetura/modelo-de-dados/dicionario.md) e [invariantes/estados](../../docs/arquitetura/modelo-de-dados/invariantes-e-estados.md) |
| Origem conceitual e diferenças conhecidas | [MER preservado](../../docs/arquitetura/modelo-de-dados/original/README.md) e [revisão do MER](../../docs/arquitetura/revisao-mer.md) |
| Contratos REST | [Convenções](../../docs/arquitetura/contratos-rest.md), contratos de cada módulo e schemas OpenAPI da API |
| Cobertura requisito → módulo/tarefa | [Rastreabilidade](../../docs/arquitetura/rastreabilidade.md) e [rastreabilidade dos prompts](../../docs/arquitetura/rastreabilidade-prompts.md) |
| Aceite, execução e evidências | [Estratégia](../../docs/testes/estrategia.md), [comandos/resultados](../../docs/testes/comandos.md) e [manifesto](../../docs/prompts/README.md) |

Dentro do repositório, respeite a solicitação vigente do responsável e AGENTS.md.
Requisitos aprovados e ADRs aceitos governam as escolhas; o cartão operacional
define o escopo da execução. Este SPEC incorpora e organiza essas fontes, sem autorizar
mudança de regra apenas por editar um resumo ou prompt.

Contratos específicos detalham as convenções gerais. Divergência material entre
requisito, ADR, schema, código ou teste deve ser registrada e resolvida na fonte
afetada; não presumir que o código ou o texto mais recente aprovou uma mudança.
Dúvidas que não afetem o trabalho independente não interrompem outras capacidades.

O MER original preserva a origem do projeto. O modelo lógico descreve também
partes futuras; as [migrations](../../database/README.md) indicam o schema físico entregue.
Análises datadas, relatórios de preparação e documentos marcados como substituídos
são histórico. A arquitetura agentiva foi substituída pela
[arquitetura semântica vigente](../../docs/arquitetura/rag-semantico.md).

## 3. Produto, atores e limites

Centralizar cadastros, atendimento, onboarding, avaliações, treinos, equipamentos,
acesso e indicadores de uma academia, com apoio de IA. Interface, prescrição e
explicações ao usuário são em português.

Uma identidade pode acumular os papéis cliente, atendente, administrador e
instrutor, com perfis específicos de cliente/funcionário. Permissões consideram
o recurso e a designação vigente, conforme [autorização](../../docs/arquitetura/autorizacao.md).

O projeto é didático. A triagem usa regras/casos acadêmicos documentados e
preserva bloqueios funcionais. Laudos, aprovação médica externa e processos
jurídicos comerciais ficam fora do MVP, conforme AGENTS.md e os requisitos.
O parecer posterior do instrutor continua sendo uma funcionalidade do produto.

## 4. Arquitetura e contratos

Monólito modular com frontend React/TypeScript/Vite, backend Python/FastAPI e
PostgreSQL. Sessão opaca integrada e papéis acumuláveis seguem
[ADR-001](../../docs/arquitetura/decisoes/ADR-001-stack-e-arquitetura.md) e
[ADR-002](../../docs/arquitetura/decisoes/ADR-002-identidade-e-papeis.md).
Ambiente de academia única, Git e tempo seguem
[ADR-003](../../docs/arquitetura/decisoes/ADR-003-academia-git-e-tempo.md).

Cada módulo possui suas regras, tabelas e repositórios. Comunicação interna
síncrona usa interfaces/serviços tipados; REST, integrações e eventos usam
JSON com schema versionado. Um módulo não acessa repositórios internos de outro.
Auditoria, idempotência e transações protegem efeitos importantes.

IA/RAG seguem [ADR-004](../../docs/arquitetura/decisoes/ADR-004-rag-llm-e-corpus.md):
Qdrant especializado separado do PostgreSQL, embeddings E5 multilíngues e
adaptador do LLM gratuito configurado. São decisões aprovadas; os ensaios reais
de qualidade/latência pertencem às entregas de RAG/IA.
Execução local e containerização tardia seguem
[ADR-005](../../docs/arquitetura/decisoes/ADR-005-servicos-locais-e-entrega.md).

## 5. Capacidades e estágio da implementação

Retrato desta revisão, após RAG-04. Consulte o manifesto para estados por cartão,
dependências, gates e evidências; atualize este resumo quando a entrega evoluir.

| Módulo | Especificação da capacidade | Estado neste marco |
|---|---|---|
| MOD-00 — Plataforma | [Stack/contratos](../../docs/arquitetura/contratos-rest.md), configuração, persistência e execução | Fundação entregue; infraestrutura final planejada |
| MOD-01 — Identidade/pessoas | [Autenticação](../../docs/arquitetura/autenticacao.md), [clientes](../../docs/arquitetura/clientes.md) e [funcionários](../../docs/arquitetura/funcionarios.md) | Entregue nos cartões IAM/PES correspondentes |
| MOD-02 — Designação | [Vínculo cliente–instrutor e histórico](../../docs/arquitetura/designacoes.md) | Entregue |
| MOD-03 — Onboarding/avaliações | [Convite, preenchimento, snapshots e avaliações](../../docs/arquitetura/onboarding.md) | Entregue |
| MOD-04 — Exercícios/fichas | [Catálogo](../../docs/arquitetura/catalogo-exercicios.md), [editor manual](../../docs/arquitetura/fichas-manuais.md), [publicação/parecer](../../docs/arquitetura/publicacao-e-parecer.md) e [consulta/exportação](../../docs/arquitetura/ficha-do-cliente.md) | Fluxo manual entregue; integração da geração depende de IA |
| MOD-05 — Conhecimento | [Curadoria e versões](../../docs/arquitetura/corpus.md), [conexão vetorial](../../docs/arquitetura/banco-vetorial.md), [extração](../../docs/arquitetura/extracao-documental.md), [ingestão e recuperação semântica](../../docs/arquitetura/rag-semantico.md) | Curadoria, extração e indexação idempotente com E5 CPU entregues; quatro fontes com revisão técnica pendente; recuperação semântica futura |
| MOD-06 — Orquestrador/IA | [Triagem resumida, geração, chat e adaptação](../../docs/arquitetura/funcionamento-ia-rag.md) | Especificado; implementação pendente |
| MOD-07 — Biometria/acesso | [CompreFace, autorização, catraca fictícia e frequência](../../docs/arquitetura/fluxos-atualizados.md) | Planejado para pós-MVP |
| MOD-08 — Matrícula/financeiro | [Planos, matrícula independente de pagamento e financeiro](../../docs/requisitos/contexto-e-escopo.md) | Planejado para pós-MVP; financeiro tardio |
| MOD-09 — Agenda | [Aulas e eventual reserva](../../docs/requisitos/requisitos-funcionais.md) | Planejado; reserva depende do gate próprio |
| MOD-10 — Equipamentos | [Inventário e disponibilidade](../../docs/arquitetura/equipamentos.md) | Entregue |
| MOD-11 — Indicadores | [Dashboard/relatórios](../../docs/arquitetura/modulos.md) | Planejado para pós-MVP |
| MOD-12 — Auditoria/avisos | [Auditoria/eventos](../../docs/arquitetura/auditoria-e-eventos.md) e [notificações](../../docs/arquitetura/notificacoes.md) | Base transversal entregue |

O MVP ainda requer RAG-05, AI-01 a AI-06 e TST-01. O próximo cartão na
sequência é RAG-05. As pendências de extração estão no contrato/relatório do módulo.
A [indexação](../../docs/arquitetura/indexacao-documental.md) fixa a revisão E5,
a seleção técnica, os limites e a migration 0013. Os pesos ficam fora do Git.
O ensaio PG/Qdrant/E5 usou texto sintético; não representa carga integral do corpus
ou avaliação de relevância da busca. Esta entrega não fecha o aceite do MVP.

## 6. Fluxos e invariantes que coordenam as capacidades

Os detalhes e critérios completos estão nas fontes da seção 2.

1. **Atendimento:** cadastro/primeiro acesso → designação de instrutor →
   convite/preenchimento do onboarding → conclusão imutável/versionada →
   avaliação datada e atribuída.
2. **Treino manual:** instrutor designado → catálogo e equipamentos elegíveis →
   rascunho → conferência/publicação → consulta móvel e exportação próprias.
   Falhas de IA/RAG não impedem esse fluxo.
3. **Geração assistida planejada:** snapshot concluído → resumo minimizado,
   preservando ausências e alertas → regras/busca e análise assistida →
   decisão do backend → catálogo/recursos e evidências → geração JSON →
   validações → publicação pelo MOD-04 com parecer PENDENTE.
4. **Consulta e parecer:** cliente consulta o publicado antes do aceite;
   instrutor designado avalia posteriormente. Edição cria outra versão.
   Rejeição mantém consulta; rejeitar uma versão posterior remove o conteúdo
   da rejeitada anterior. Limite independente de quinze versões publicadas
   completas inclui a vigente e preserva metadados/auditoria e execuções existentes.
5. **Chat/adaptação planejados:** dúvida usa recuperação semântica e resposta com
   fontes ou abstenção. Conversa informativa não altera ficha. Adaptação explícita
   exige contexto confirmado/versionado, nova triagem e publicação de nova versão.
6. **Acesso pós-MVP:** atendente matricula sem pagamento obrigatório → referência
   facial e nova captura pelo CompreFace → identidade → autorização por matrícula
   e regras de acesso → API de catraca fictícia → passagem/frequência/lotação.

Preservar também os seguintes invariantes:

- Autorização no backend e isolamento entre clientes; instrutor depende da
  designação vigente. Administrador não recebe acesso irrestrito a dados de saúde.
- Ausência de dado não significa saudável/zero/média. Bloqueios acadêmicos graves
  não são removidos por resposta do LLM ou parecer do instrutor.
- Exercícios/alternativas exigem recursos disponíveis ou dispensa explícita.
  Backend revalida antes de publicar; mudança posterior é sinalizada sem
  reescrever a prescrição histórica.
- Orquestrador de etapas fixas, sem planner ou pesquisa iterativa. Chat tem até
  uma geração; ficha/adaptação até uma análise de triagem e uma geração, sem
  retry automático de etapa LLM. Falha técnica não equivale a elegibilidade.
- Adaptação por saúde exige evidência pertinente do corpus aprovado. Documentos
  são dados, nunca instruções; dados privados não entram na literatura compartilhada.
- UTC/ISO 8601, migrations reproduzíveis, segredos em ambiente e dados sintéticos
  nos testes. Auditoria e históricos necessários sobrevivem à inativação/expurgo.

## 7. Contratos e evidências especializados

| Área | Especificação/contrato verificável |
|---|---|
| Campos do onboarding e triagem | [Campos/regras](../../docs/requisitos/onboarding-e-triagem.md), [JSON Schema](../../docs/requisitos/schemas/onboarding-v1.schema.json) e [casos sintéticos](../../docs/testes/casos-triagem-v1.json) |
| IA e RAG | [Parâmetros](../../docs/requisitos/configuracao-ia-rag.md), [configuração JSON](../../docs/requisitos/schemas/configuracao-ia-v1.json), [dados RAG/IA](../../docs/arquitetura/modelo-de-dados/dados-rag-ia.md) e [cenários de avaliação](../../docs/testes/rag-ia-semantico.md) |
| Literatura | [Acervo](../../materiais/rag/README.md), [catálogo](../../materiais/rag/catalogo.json) e [seleção inicial](../../materiais/rag/corpus-inicial.json) |
| REST e DTOs implementados | [Convenções](../../docs/arquitetura/contratos-rest.md), documentos do módulo e OpenAPI gerado conforme [guia do backend](../../backend/README.md) |
| Aceite funcional e regressão | Critérios de cada RF/MRF, [estratégia](../../docs/testes/estrategia.md), [regressões RF/RN](../../docs/testes/aceite-rf-rn-2026-11-06.md) e testes do módulo |

Documento selecionado para ingestão não demonstra indexação/recuperação funcionando.
Caso sintético, schema válido e teste com double não comprovam qualidade clínica
ou desempenho real de um modelo. Ensaios exigidos são registrados nas entregas
correspondentes e no manifesto.

## 8. Reproduzir ou reconstruir o sistema

Para reproduzir a implementação existente, selecione o commit desejado e siga
os guias de [banco](../../database/README.md), [backend](../../backend/README.md),
[frontend](../../frontend/README.md) e [primeiro administrador](../../docs/instalacao/primeiro-administrador.md).
Use os lockfiles versionados, as migrations desse commit e exemplos de ambiente
([raiz](../../.env.example) e [frontend](../../frontend/.env.example)); configure segredos
localmente, fora do Git. Recursos externos/credenciais pessoais não são
reconstituídos pela especificação.

Para reconstruir funcionalmente com outra IA:

1. Leia AGENTS.md e este SPEC, identifique se a meta é reproduzir o estágio atual
   ou implementar capacidades planejadas e consulte as fontes do escopo escolhido.
2. Use RF/RN/RNF/MRF, ADRs, modelo de dados e contratos como entrada do plano.
   Preserve os IDs e registre lacunas; não dependa de mensagens antigas desta conversa.
3. Implemente por capacidades pequenas com interfaces entre módulos, migrations,
   contratos, testes e documentação. Os cartões existentes podem orientar a
   execução; a definição do produto permanece nas fontes da especificação.
4. Verifique critérios e comandos aplicáveis antes de declarar a capacidade pronta.
   Atualize a rastreabilidade e o manifesto com evidência.

Reconstrução funcional exige equivalência aos requisitos/contratos aceitos;
reprodução do mesmo código e ambiente usa o histórico Git e os arquivos travados.

## 9. Protocolo de alteração e manutenção

Ao receber uma mudança aprovada:

1. Identifique os requisitos, critérios e módulos afetados.
2. Atualize a fonte especializada e registre a origem/decisão; mantenha IDs estáveis
   e distinga proposta de decisão aceita. ADR novo/substituto é usado quando pertinente.
3. Ajuste modelo, contratos e plano/cartões afetados; migration nova acompanha
   mudança física de schema e migrations já aplicadas permanecem preservadas.
4. Implemente e teste no escopo autorizado. Caso código e especificação divirjam,
   corrija a divergência ou registre a pendência, sem declarar conclusão artificial.
5. Atualize este mapa/resumo quando mudar seu conteúdo, a rastreabilidade,
   as evidências e o manifesto. Registre a revisão no Git.

Refinamentos de implementação não mudam silenciosamente regras aprovadas.
Documentação de análise histórica deve continuar identificada como histórica.
Evite copiar requisitos completos em prompts ou criar fontes concorrentes.

A manutenção do documento completo usa `python scripts/gerar_spec.py --write`
e a verificação `python scripts/gerar_spec.py --check`. A validação documental
`python scripts/verificar_documentacao.py` verifica links, IDs e referências.
Testes da aplicação, integrações e avaliação de IA seguem comandos próprios.

## 10. Origem no MER fornecido e evolução aceita

O MER original do responsável, denominado MER_Academia_Completo_v4.drawio.png,
foi preservado sem regravar sua imagem/XML. Ele possui 18 entidades e 307 células
draw.io, em imagem 6492 × 3187. SHA-256 de referência:
`5b57634d6936bc76c82e3f85bfa45a91626ec734af77b45e0a083e2990c1df93`.

As entidades originais são USUÁRIO, CLIENTE, FUNCIONÁRIO, ACADEMIA,
REGISTRO_ACESSO, BIOMETRIA, ONBOARDING, Queixa, INTERACAO_IA, VERSAO_FICHA,
ITEM_FICHA, EXERCÍCIO, ASSINATURA, PLANO, COBRANÇA, PAGAMENTO,
AULA DE GINÁSTICA e EQUIPAMENTO.

O modelo lógico completo incorporado adiante materializa a evolução aceita
desse MER e dos requisitos fornecidos, incluindo refinamentos posteriores:

| Base original | Especificação atual para reconstrução |
|---|---|
| USUÁRIO com perfil único | Identidade única e papéis acumuláveis; cliente e funcionário podem coexistir; credenciais/sessões/tokens são separados. |
| Cliente sem designação histórica | Designação principal vigente e histórico cliente–instrutor, com autor e datas. |
| ONBOARDING e Queixa | Dados físicos/saúde estruturados, rascunho, snapshots imutáveis e avaliações datadas; evitar duas fontes divergentes para queixas. |
| VERSAO_FICHA / ITEM_FICHA / EXERCÍCIO | Catálogo independente, dias/itens prescritos, autoria/origem, validação técnica, publicação e parecer separados. |
| Relação INSTRUCAO entre pessoa, exercício e equipamento | Separar responsabilidade do instrutor, prescrição e requisitos/alternativas de equipamento. |
| INTERACAO_IA como pergunta/resposta | Conversa/mensagens privadas, execução idempotente, triagem, etapas, consumo e referências às evidências. |
| Ausência de entidades do corpus | Documento, versão, ingestão e fragmento com proveniência; vetores no Qdrant. |
| BIOMETRIA / REGISTRO_ACESSO | Referência do CompreFace, identificação separada da autorização, evento externo, comando e passagem/presença. |
| ASSINATURA / PLANO / COBRANÇA / PAGAMENTO | Matrícula com atendente/validade/limites; pagamento opcional e financeiro tardio, sem gate financeiro para matrícula acadêmica. |
| AULA DE GINÁSTICA por dia da semana | Ocorrências com datas/horários; reservas/capacidade somente no escopo aprovado. |
| ACADEMIA / EQUIPAMENTO | Academia única e recursos cadastrados ativos/operacionais, com imagens e vínculo explícito aos exercícios. |
| Histórico/auditoria implícitos | Versionamento, retenção/expurgo de conteúdo, auditoria protegida, notificações e eventos duráveis. |

Reproduzir literalmente o PNG não atenderia aos refinamentos aprovados.
Use o texto/DBML incorporado para o modelo atual e preserve a imagem como origem.
Não reintroduzir pagamento obrigatório, aceite prévio do instrutor, Agentic RAG
ou exigência de laudo ao usar requisitos históricos de entrada.

## 11. Uso como documento portátil e limites de completude

Os capítulos seguintes incorporam os requisitos completos com critérios,
regras, decisões técnicas, modelo de dados, contratos, campos/schemas,
configuração IA, corpus inicial, testes e sequência de etapas.
Assim, outra IA pode receber apenas este arquivo para planejar e reconstruir
o comportamento especificado, usando os capítulos pertinentes em cada prompt.

Links continuam úteis para navegação no repositório e identificação da fonte.
A compreensão das especificações essenciais não depende de abrir esses links.
A versão de transporte é um instantâneo; o quadro de integridade identifica
as fontes usadas para produzi-la.

O texto não contém os binários PDF do corpus, pesos de embedding ou credenciais.
A seleção incorporada informa títulos, URLs, hashes, finalidade e limites dos
documentos aprovados. Provisionar esses recursos e validar sua integridade
pertence às etapas de RAG; arquivo diferente não se torna aprovado por ter o
mesmo título. Serviços/provedores continuam sujeitos ao ensaio real previsto.

As pendências pós-MVP estão explicitadas no roteiro incorporado. O SPEC não
inventa a versão/hospedagem de CompreFace nem parâmetros de reserva, acesso ou
gateway ainda não decididos. Uma reconstrução pode concluir o MVP antes desses
gates e tratar o escopo posterior quando suas decisões forem fechadas.

Este arquivo é gerado de fontes versionadas. No projeto de origem, editar os
documentos especializados e a visão geral/roteiro, atualizar o SPEC com
`python scripts/gerar_spec.py --write` e validar com
`python scripts/gerar_spec.py --check` e
`python scripts/verificar_documentacao.py`. Fontes e cópia completa acompanham
o mesmo commit. Em outro projeto que recebeu só o SPEC, a IA pode primeiro
materializar os documentos especializados a partir de seus capítulos.
