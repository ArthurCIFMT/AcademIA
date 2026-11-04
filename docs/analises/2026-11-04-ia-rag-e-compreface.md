# Análise da IA/RAG e escolha do CompreFace

> Registro da análise anterior às decisões adicionais do responsável em 2026-11-04.
> A política de rejeitadas, a evidência obrigatória e a adoção de CompreFace foram
> incorporadas depois em [funcionamento vigente](../arquitetura/funcionamento-ia-rag.md).
> A estimativa de coleta abaixo foi seguida por 11 novos PDFs: ver
> [catálogo atualizado](../../materiais/rag/README.md). Os números e pendências
> restantes neste relatório descrevem a base examinada naquela análise.

Data: 2026-11-04. Base examinada: commit
`aa63caa3a20764b9fee8c45f6cf173d9682030f9` do AcademIA.
Escopo: registrar a escolha explícita de CompreFace e analisar compatibilidade,
detalhamentos recomendados e necessidade de fontes. Este relatório não altera
RFs, RNs, RNFs, MRFs, prompts, MER ou o catálogo de materiais. As sugestões abaixo
não representam aprovação automática nem implementação.

## Conclusão

Os 15 macrorequisitos atuais formam uma estrutura suficiente para a IA de treino
com RAG. MRF01–MRF07 sozinhos deixam incompletas capacidades que MRF08–MRF15 já
descrevem: triagem, restrições, parecer posterior, evidências, isolamento,
avaliação, chat e governança. Não há necessidade demonstrada de novos agentes,
microserviços ou novos IDs de macrorequisitos nesta etapa.

A versão atual já é compatível com treino e chat antes do aceite do instrutor.
Os ajustes prioritários são de precisão e verificabilidade, e não de reintroduzir
aprovação humana prévia. MRF08–MRF15 continuam formalmente pendentes de validação
no documento vigente; esta análise não muda esse estado.

Os sete PDFs atuais são uma coleção inicial, não uma base já aprovada ou completa.
Recomenda-se planejar mais 8–12 fontes relevantes, deduplicadas e utilizáveis,
e validar a suficiência por cobertura e testes. A faixa é estimativa de trabalho,
não um número científico obrigatório nem garantia de qualidade.

## Fontes internas examinadas

- [Requisitos funcionais](../requisitos/requisitos-funcionais.md).
- [Regras de negócio](../requisitos/regras-de-negocio.md).
- [Requisitos não funcionais](../requisitos/requisitos-nao-funcionais.md).
- [Macrorequisitos IA/RAG](../requisitos/macrorequisitos-ia-rag.md).
- [Decisões atuais](../arquitetura/decisoes-iniciais.md),
  [fluxos](../arquitetura/fluxos-atualizados.md) e [manifesto](../prompts/README.md).
- [Estratégia de testes](../testes/estrategia.md), cartões RAG/AI, ONB-04 e TRN.
- [Catálogo bibliográfico](../../materiais/rag/catalogo.json) e
  [lacunas já registradas](../../materiais/rag/referencias-complementares.md).

A avaliação do acervo usa catálogo, proveniência e cobertura temática registrados.
Não equivale a uma revisão clínica integral das 326 páginas ou a uma avaliação
experimental de recuperação, que ainda não existe.

## CompreFace: decisão confirmada e impactos

**Escolha expressa do responsável: usar CompreFace na biometria facial.**
A recomendação anterior de Amazon Rekognition fica superada por esta decisão.
Não é necessário pedir novamente a escolha do fornecedor.

A troca não altera o propósito de RF-20–RF-23/RF-36/RF-37 ou RN-06–RN-10/RN-35/RN-36.
Python permanece o backend do AcademIA; CompreFace é uma integração externa.
A escolha não fecha sozinha GATE-08: contrato, configuração, testes e execução
continuam necessários.

A documentação oficial oferece cadastro de exemplos por `subject`, retorno de
`image_id`, reconhecimento e exclusão de imagem. Recomenda-se vincular
identificadores opacos ao cliente e guardar a chave `x-api-key` no backend.
`subjects[].similarity` é diferente de `box.probability`/`det_prob_threshold`.
Limitar a quantidade retornada não demonstra que a captura contém só um rosto.
O serviço aceita vários exemplos; o fluxo do projeto deve efetuar a substituição
exigida por RF-22, conferindo exclusão da referência antiga e falhas parciais.
[API oficial](https://github.com/exadel-inc/CompreFace/blob/master/docs/Rest-API-description.md).

| Capacidade | Contrato da API consultado |
|---|---|
| Cadastrar referência | POST /api/v1/recognition/faces?subject=... |
| Reconhecer captura nova | POST /api/v1/recognition/recognize |
| Excluir exemplo específico | DELETE /api/v1/recognition/faces/{image_id} |

O limiar de RF-21 deve ser mapeado à escala do fornecedor: 95 na apresentação
percentual corresponde numericamente a 0,95 na escala 0–1. Isso não comprova 95%
de acurácia. A seleção de limiar precisa de ensaio do modelo/versão escolhido,
com pessoas conhecidas e desconhecidas e condições de captura documentadas.
O score facial também não se confunde com similaridade do RAG.
[Orientação oficial sobre limiares](https://github.com/exadel-inc/CompreFace/blob/master/docs/Face-Recognition-Similarity-Threshold.md).

O fluxo continua: matrícula pelo atendente, sem pagamento obrigatório → referência
facial → captura nova → CompreFace → autorização do AcademIA → API fictícia de
catraca → passagem simulada confirmada. Reconhecimento não libera entrada sozinho.
Fotos e vetores faciais não pertencem ao banco vetorial de literatura do RAG.

### Ponto de infraestrutura a resolver

O modo de instalação documentado do CompreFace usa Docker/Compose.
[README oficial](https://github.com/exadel-inc/CompreFace#readme).

Isso exige uma decisão sobre a aplicação de RNF-10/RNF-11, DEC-011 e GATE-06/08:

1. Usar uma instância externa já disponibilizada por servidor/laboratório; o
   AcademIA apenas consome sua API.
2. Autorizar, na fase pós-MVP de biometria, o contêiner do serviço externo,
   preservando a containerização do AcademIA para INF-01–INF-04.
3. Se a restrição for proibir qualquer Docker antes de PG-03, rever a sequência:
   PG-03 hoje exige ACS-06, cujo aceite real depende do serviço facial. Adiar o
   serviço até esse mesmo gate criaria uma dependência circular de planejamento.

Recomendação: opção 1 quando houver instância disponível; caso contrário, discutir
a opção 2 com o professor. Nenhuma exceção foi adotada neste relatório. Mock
continua útil nos testes isolados, mas não substitui o ensaio real da biometria.

### Atualizações documentais futuras, sem execução nesta análise

| Documento/cartão | Atualização necessária quando solicitada |
|---|---|
| decisões iniciais, REC-011 | Trocar a recomendação AWS pela escolha confirmada de CompreFace e registrar modo de execução |
| fluxos atualizados e mestre | Substituir operações/termos específicos de Rekognition pelos contratos de CompreFace |
| ACS-01 | Adequar cadastro, identificadores, substituição e qualidade |
| ACS-02/ACS-03 | Adequar resposta normalizada, limiar, falhas e teste com fornecedor real |
| GATE-06/GATE-08 e infraestrutura | Documentar a decisão sobre hospedagem/Docker, sem fechar os demais itens automaticamente |

## Compatibilidade de cada macrorequisito

“Detalhar” significa propor critérios mais precisos para uma capacidade existente.
Não significa que a capacidade esteja ausente de todos os documentos: vários
detalhes já estão nos cartões operacionais e na estratégia de testes.

| MRF | Cruzamento principal | Diagnóstico e recomendação |
|---|---|---|
| MRF01 | MRF15; RNF-05/08/17; RAG-03/04 | Compatível. Detalhar extração de tabelas/unidades, PDF sem texto/OCR, retomada idempotente e versão/modelo/dimensão dos embeddings. RAG-04 já prevê parte disso; consolidar no aceite do macrorequisito. |
| MRF02 | RF-15/18/19; RN-15/29; RNF-13; RAG-05 | Compatível. Calibrar top-K/limiares com consultas rotuladas; filtrar público, tema, versão e estado; medir relevância, e não apenas score/latência. Manter p95 ≤ 2 s somente para busca vetorial no cenário definido. |
| MRF03 | RF-11–RF-15; RN-11/21/29; ONB-02/04 | Compatível, esquema incompleto para implementação. Definir campos, unidades, obrigatoriedade e origem declarada/medida. Experiência, disponibilidade de dias/tempo e objetivos devem ser definidos no formulário; campos adicionais são proposta a aprovar. Não presumir medições ou diagnóstico. |
| MRF04 | RF-15/18/19; RN-13/16/19; RNF-17; AI-02/03 | Compatível. Explicitar ramos de bloqueio/abstenção, estado persistido, idempotência, limite de custo/tempo, falha parcial e validação da versão-base antes de publicar. Os papéis dos agentes podem permanecer sob um controlador no monólito. |
| MRF05 | RF-15/19; RN-13/15/20; MRF09; TRN-01 | Compatível. Catálogo e restrições estruturadas limitam a geração; validar novamente o resultado por código. Definir unidades/faixas e impedir IDs inativos/inexistentes, sem deixar ao LLM a criação de limites clínicos. |
| MRF06 | RF-15/17/35; RN-16/17/18; AI-02/06 | Compatível com a decisão recente. Revisor automático não dá aceite profissional nem revoga regra determinística. Explicitar publicação apenas após validações; guardar tentativas/falhas separadamente do conteúdo publicável. |
| MRF07 | RF-16/17/35; RN-05/28/31; RNF-14; TRN-04 | Manter o conceito. Definir organização de períodos, sessões e dias no JSON, campos de prescrição, estado vazio/erro e parecer separado. Exportação deve preservar versão e autorização. |
| MRF08 | CA-15.4; RF-19; RN-12/13/15/30; AI-01 | Precisa esclarecer “liberação profissional”. Parecer rotineiro do instrutor não pode virar pré-requisito de consulta/chat. Caso grave bloqueado não é liberado por texto de um agente ou simples aceite do instrutor. Formalizar política, responsáveis e transições para dados insuficientes/incertos. |
| MRF09 | RN-13/15/20; MRF05/08; AI-01/03 | Compatível, mas o texto menciona aplicação depois da geração. Recomenda-se restrições disponíveis antes da seleção e validador obrigatório depois, com política versionada. Isso reforça a regra existente, sem substituir a triagem anterior. |
| MRF10 | RF-34/35; RN-12/14/16/31; TRN-03 | Manter: avaliação posterior por instrutor designado, edição em nova versão e autoria. Nova versão não herda aceite. Falha de aviso/ausência de designação é pendência explícita de revisão, sem recriar barreira de aceite para leitura/chat. |
| MRF11 | RF-15/19; RN-15/30; RAG-05; AI-02 | Compatível. Tornar operacional a abstenção quando falta suporte suficiente; cada recomendação deve apontar a evidência efetivamente recuperada. Definir tratamento de fontes conflitantes/revogadas e citações que não sustentam a resposta. |
| MRF12 | RF-12/14/18; RN-04/05/11/23/29; RNF-15 | Manter e testar contexto, histórico, cache e acesso a recursos. A identidade do cliente vem da autorização no backend; literatura compartilhada é diferente de histórico/anamnese privados. |
| MRF13 | RNF-07/13; RN-13/15/29; AI-06/TST-01 | Compatível; falta fixar dados e limiares de qualidade para o ensaio. A estratégia já exige bloqueios críticos e isolamento. Separar avaliação do RAG, geração, chat, regras e teste com provedor real. |
| MRF14 | RF-18/19; RN-12/16/17/18/29; AI-05 | Ampliar a descrição para cobrir chat comum além de dor/limitação. Explicitar contexto da versão vigente, nova triagem quando necessário, diff e nova versão. Definir resposta para risco novo sem reescrever ou apagar histórico. |
| MRF15 | MRF01/02/11/12; RN-23/29; RAG-01/04/05 | Manter. Detalhar aprovação/revogação, vigência, conflitos, proveniência e isolamento entre evidência e instrução maliciosa. Aprovar documento do corpus é um processo diferente de avaliar posteriormente o treino. |

A dependência de implementação AI-01 → ONB-04 não significa exigir, em tempo de
uso, um parecer do instrutor para toda conversa ou geração. Dependência entre
cartões e pré-condição funcional do cliente são conceitos distintos.

## Mudanças recomendadas em ordem de prioridade

### Prioridade alta

- Esclarecer MRF08, sem alterar RN-13: política explícita de triagem/bloqueio e
  significado de “liberação profissional”. O sistema analisa declarações e
  restrições; não produz diagnóstico nem uma autorização médica autônoma.
- Completar MRF03 com esquema aprovado da anamnese. Campos ausentes devem gerar
  validação ou estado de dados insuficientes, não suposições do modelo.
- Refinar MRF05/MRF09 com seleção limitada pelo catálogo/restrições e validação
  determinística final. Faixas numéricas precisam de política estruturada
  rastreável; recuperar um trecho não equivale a executar uma regra.
- Reforçar MRF02/MRF11 para abstenção e evidência suficiente, inclusive em
  recuperação vazia, irrelevante, contraditória ou insuficiente.
- Detalhar MRF14 para chat geral, adaptação e risco novo, preservando isolamento,
  versão-base e consulta anterior ao parecer.

### Antes do aceite da IA

- Consolidar MRF01/MRF04: processamento idempotente, versões, transições,
  concorrência, falhas, limite de execução e publicação consistente.
- Fixar avaliação de MRF13 com casos e consultas rotuladas, configuração reprodutível
  e critérios definidos antes de rodar. JSON válido não comprova treino adequado.
- Formalizar curadoria de MRF15 e situação de MRF08–MRF15, sem marcar todos como
  aceitos apenas porque este relatório foi produzido.

### O que não precisa mudar de conceito

- Treino e chat antes do aceite humano: já está coerente em RF-15–RF-19,
  RF-35, RN-12, MRF06/MRF07/MRF10/MRF14.
- Casos graves bloqueados, restrições com precedência e ausência de diagnóstico:
  RN-13/RN-15/RN-30 continuam sendo os limites do produto.
- Autoria, nova versão e histórico: RF-17/RF-35 e RN-16–RN-18/RN-31.
- Isolamento entre clientes e autorização: RN-04/RN-05/RN-11/RN-29.
- Ficha manual com IA indisponível: RN-19.
- Matrícula sem pagamento obrigatório: RF-31/RN-24; isso não é pré-condição financeira
  da IA ou da biometria.
- Banco vetorial especializado e backend Python: RNF-02/RNF-05.

### Ambiguidades nos demais documentos a esclarecer futuramente

| Item | Recomendação sem alterar o arquivo atual |
|---|---|
| CA-19.1 diz que relato de dor gera adaptação | Escrever explicitamente “quando elegível e suportada por evidências”; para bloqueio/insuficiência, retornar estado correspondente. CA-19.2 e RN-13 já limitam o fluxo; é clareza de aceite, não autorização para treinar caso grave. |
| Cliente pode consultar treino REJEITADO | Definir qual versão permanece atual após rejeição. Preservar acesso ao conteúdo, motivo e chat conforme RF-16/RF-35; não esconder silenciosamente. |
| Nova restrição relevante com ficha já publicada | Definir sinalização e encaminhamento para revisão sem reescrever histórico ou tratar bloqueio de nova geração como exclusão do treino anterior. |
| Documentos ainda citam Rekognition | Atualizar depois para CompreFace; a escolha já foi feita, mas os textos foram preservados nesta análise. |
| RNF-11 e instalação do CompreFace | Resolver a política de infraestrutura descrita acima antes do ensaio facial real. |

## Acervo atual e cobertura

Contagem conferida no catálogo e nos arquivos, sem mudança de aprovação:

| Grupo | Itens | Páginas PDF | Cobertura e limite principal |
|---|---:|---:|---|
| Guia do Ministério, complemento e artigos relacionados de adultos/idosos | 4 | 91 | Base brasileira de atividade física; conteúdos relacionados e parcialmente sobrepostos |
| Revisão narrativa de treinamento resistido/hipertrofia | 1 | 36 | Início da cobertura de prescrição; requer confronto com sínteses atualizadas |
| Hipertensão 2025 e reabilitação cardiovascular 2020 | 2 | 199 | Contexto cardiovascular; inclui conteúdo clínico fora do escopo da academia |
| Total | 7 | 326 | Todos ainda pendentes de revisão para RAG |

As duas diretrizes cardiovasculares representam aproximadamente 61% das páginas.
Quantidade de páginas não demonstra equilíbrio temático ou evidências suficientes
para cada cenário. Os quatro materiais ligados ao guia brasileiro não equivalem
a quatro fontes independentes para todas as recomendações.

## Quanto material adicional buscar

**Faixa recomendada para planejar a próxima coleta: 8–12 fontes adicionais,
chegando a aproximadamente 15–19 itens bibliográficos.** Contar cada fonte uma vez,
mesmo se ela contribuir para mais de uma linha; não inflar a coleção separando
capítulos do mesmo documento. Ajustar a faixa depois da leitura e matriz de cobertura.
São metas editoriais propostas para a primeira entrega acadêmica, não novos RFs.

| Cobertura adicional | Faixa de fontes | Prioridade e propósito |
|---|---:|---|
| Prescrição de força, hipertrofia, progressão e organização do treino | 2–3 | Alta: complementar a revisão narrativa com consensos/sínteses mais recentes |
| Limitações musculoesqueléticas: lombar, joelho e ombro | 3 | Alta: uma fonte pertinente por área como ponto inicial; condições distintas podem exigir outras |
| Avaliação pré-participação, encaminhamento e restrições | 1–2 | Alta: apoiar a construção revisada da política, sem inventar limiares |
| Exercício e condições metabólicas, especialmente diabetes | 1 | Alta: preencher a lacuna que as duas diretrizes cardiovasculares não resolvem integralmente |
| Biomecânica, execução e alternativas dos exercícios do catálogo | 1–2 | Alta: dar suporte às escolhas/substituições; não basta uma lista de nomes |
| Público específico ainda sem cobertura suficiente | 0–1 | Condicional ao escopo confirmado; não implica que uma fonte cubra todos os públicos |
| Total de planejamento | 8–12 | Reavaliar por cobertura, atualidade e independência |

A estimativa pressupõe uma primeira entrega com cobertura delimitada e comportamento
de abstenção para cenários sem suporte. Não remove públicos/condições dos requisitos.
Se forem exigidas prescrições para muitos públicos específicos ou várias patologias,
o acervo necessário aumenta; não existe número universal de PDFs que cubra isso.

Fontes já localizadas ou a avaliar, sem novo download nesta etapa:

- [ACSM 2026, registro bibliográfico](https://pubmed.ncbi.nlm.nih.gov/41843416/):
  candidato para comparar evidências de prescrição; já estava nas referências
  externas, não nos sete PDFs. Idioma e condições de uso permanecem relevantes.
- [OMS, diretriz de lombalgia crônica primária de 2023](https://www.who.int/publications/i/item/9789240081789):
  candidata para a lacuna lombar dentro de seu público e contexto próprios,
  sem generalizar para qualquer causa de dor lombar.
- [SBD, exercício no pré-diabetes e DM2](https://diretriz.diabetes.org.br/atividade-fisica-e-exercicio-no-pre-diabetes-e-dm2/):
  referência já localizada, ainda sem cópia no acervo. Conferir edição e condições
  de uso antes de arquivar/ingerir; página pública não equivale a licença aberta.
- Para joelho, ombro e técnica dos exercícios, ainda selecionar documentos
  específicos adequados ao público do projeto. Esta análise não afirma que essas
  fontes já tenham sido coletadas ou aprovadas.

Priorizar português. Fontes internacionais podem complementar a base e respostas
podem continuar em português, com modelo/recuperação avaliados nesse cenário.
Tradução, quando necessária, deve manter autoria, contexto e condições de uso.

## Dados necessários além de PDFs

| Conjunto | Destino principal | Proposta inicial de planejamento |
|---|---|---|
| Literatura aprovada com metadados | Banco vetorial especializado e metadados de documentos | Os sete itens existentes mais a coleta dirigida proposta |
| Catálogo validado de exercícios | PostgreSQL, com IDs estáveis | Aproximadamente 30–50 exercícios para uma demonstração delimitada, com técnica, recursos e alternativas revisadas; quantidade não é requisito aprovado |
| Políticas e restrições estruturadas | Backend/PostgreSQL e controle de versões | Regras rastreáveis às fontes e ao responsável pela revisão, sem valores clínicos inventados |
| Perfis, onboarding, versões e conversas | PostgreSQL e contexto autorizado por execução | Dados de clientes não entram como literatura compartilhada |
| Biometria | CompreFace e referências protegidas | Separada do corpus de treino |
| Consultas/casos de avaliação | Conjunto de testes separado | Não indexar o gabarito no corpus consultável |

Sugestão de início para MRF13: 20–30 consultas de recuperação com evidências
esperadas e 40–60 casos sintéticos de geração/chat/triagem, revisados e separados
dos documentos de conhecimento. A quantidade é proposta, não resultado medido.

Um núcleo de 40 casos pode distribuir-se em 10 elegíveis, 10 com restrições,
5 bloqueados por política, 5 insuficientes/contraditórios, 5 adversariais/isolamento
e 5 de falhas operacionais. Ampliações e combinações podem elevar esse total.
Nenhum caso clínico é considerado validado apenas por ter sido gerado por IA.

## Critério de suficiência da base

A próxima coleta deve produzir evidência para conferir:

1. Cobertura dos objetivos, restrições e públicos definidos para o ensaio.
2. Identificação de fonte, edição, população, contexto e páginas relevantes.
3. Resolução de sobreposição/conflito e exclusão de documentos não aprovados.
4. Recuperação de trechos pertinentes nas consultas rotuladas e ausência explícita
   de suporte quando necessário; o limiar de relevância será definido antes do teste.
5. Aderência das recomendações às evidências e às regras estruturadas.
6. Bloqueio de todos os casos críticos definidos na suíte e ausência de mistura
   entre clientes, conforme estratégia atual. Isso não garante segurança universal.
7. Preservação de tabelas, unidades e referências ao extrair e dividir documentos.
8. Atendimento do p95 vetorial no ambiente documentado, separado do tempo do LLM.

Nenhum benchmark, ingestão, embedding, implantação do CompreFace ou teste clínico
foi executado por esta análise. Não foram baixados novos documentos. As pendências
não impedem fundação/identidade/treino manual; afetam o aceite da IA e da biometria.

## Fontes técnicas externas e evidência de leitura

Consultadas em 2026-11-04:

- [CompreFace: API REST](https://github.com/exadel-inc/CompreFace/blob/master/docs/Rest-API-description.md),
  blob observado `1aefe283776718dd200e0b0d4d1d4afa531f3577`.
- [CompreFace: similaridade](https://github.com/exadel-inc/CompreFace/blob/master/docs/Face-Recognition-Similarity-Threshold.md),
  blob observado `507c175f046a915d785046023f95c45a16e6919a`.
- [CompreFace: apresentação/instalação](https://github.com/exadel-inc/CompreFace#readme),
  blob README observado `2e402007256277cc63aeb765995c54ba6dca868b`.

Os dados bibliográficos internos foram lidos do catálogo. Os documentos-fonte
mantêm suas licenças e situação de curadoria; este relatório não muda esses registros.

## Verificações desta entrega

- Matriz com os 15 MRFs, sem criar ou alterar seus IDs.
- Links relativos do relatório conferidos.
- Sete hashes SHA-256 do acervo conferidos; 326 páginas no catálogo, sem mudança de aprovação.
- Revisão do diff: somente este relatório é acrescentado; arquivos normativos,
  prompts, MER e materiais anteriores permanecem idênticos à base.
- A faixa de fontes adicionais soma 8–12; é recomendação editorial, não benchmark.
