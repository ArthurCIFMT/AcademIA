# Macrorequisitos de IA e RAG

## Situação

- MRF01 a MRF07: fornecidos pelo responsável do projeto.
- MRF08 a MRF15: derivados durante a análise e sujeitos a validação formal antes
  da implementação do módulo correspondente.

## Requisitos fornecidos

### MRF01 — Ingestão e processamento de documentos

Extrair texto de literatura validada em PDF/TXT, dividir em blocos e gerar
embeddings por provedor configurável.

- Preservar conteúdo clínico, unidades e símbolos relevantes.
- Tratar limites, tentativas e falhas do provedor de embeddings.
- Persistir vetor, texto e metadados correspondentes.
- Manter fonte, versão, página/seção, hash e estado de aprovação.

### MRF02 — Consulta semântica ao banco vetorial

Converter contexto minimizado do cliente em consulta vetorial e recuperar
diretrizes biomecânicas/fisiológicas pertinentes.

- Retornar `top-K` blocos por similaridade de cosseno e suas pontuações; outra
  métrica exige decisão arquitetural explícita.
- Aplicar filtros por corpus e versão aprovada.
- Registrar baixa similaridade e permitir abstenção.
- Busca vetorial com latência p95 menor ou igual a dois segundos no ambiente de
  teste definido.

### MRF03 — Perfil e anamnese clínica/funcional

Coletar dados físicos, experiência, limitações, lesões e condições informadas.

- Campos obrigatórios são validados.
- Dados são serializados em JSON padronizado nas fronteiras.
- A versão utilizada por cada geração permanece identificável.

### MRF04 — Orquestração multiagente

Coordenar estado entre agentes especialistas sob controle central.

- Fluxo controlado: triagem → biomecânica → periodização → revisor.
- Timeout, tentativas e limite máximo de ciclos.
- Agentes retornam JSON tipado e não ativam ficha diretamente.

### MRF05 — Geração delimitada por regras

Gerar seleção de exercícios, volume e intensidade dentro das restrições do cliente
e das políticas estruturadas, usando o RAG como evidência.

- Exercício incompatível com restrição é bloqueado.
- Limites numéricos passam por validação determinística.
- Saída segue JSON Schema estrito.
- Exercícios são referenciados pelo catálogo do sistema.

### MRF06 — Auditoria automática por revisor

Revisar redundâncias, conflitos e inconsistências da proposta.

- Revisor pode rejeitar e devolver feedback ao orquestrador.
- Ciclos de correção possuem limite.
- Tentativas e rejeições são persistidas para auditoria.
- Somente proposta validada segue para revisão profissional.

### MRF07 — Disponibilização estruturada da ficha

Renderizar ficha aprovada por microciclos/dias.

- Mapear exercício, cadência, séries, repetições e demais prescrições.
- Disponibilizar API e exportação autorizada do consolidado.
- Exibir apenas versão ativa e aprovada ao cliente.

## Requisitos derivados pendentes de validação

### MRF08 — Triagem e decisão de segurança

Classificar solicitação como dados insuficientes, bloqueada por segurança,
dependente de liberação profissional ou elegível para geração. Nenhum treino é
gerado nos três primeiros estados, e a explicação não constitui diagnóstico.

### MRF09 — Motor de restrições estruturadas

Aplicar regras determinísticas a exercícios, volume e intensidade depois da
geração. Falha de validação impede avanço, e políticas são versionadas.

### MRF10 — Revisão e aprovação profissional

Permitir que instrutor designado modifique, aprove ou rejeite uma proposta,
registrando responsável, parecer e data/hora. Aprovação cria versão imutável.

### MRF11 — Evidências e rastreabilidade

Vincular recomendações a documento, versão, página/seção e fragmento recuperado.
Ausência de evidência suficiente deve permitir abstenção.

### MRF12 — Isolamento de contexto

Garantir que cada execução utilize apenas dados autorizados de um cliente, sem
identificadores pessoais desnecessários na consulta vetorial.

### MRF13 — Avaliação automatizada da IA

Executar casos sintéticos saudáveis, restritos, graves, incompletos,
contraditórios, adversariais e com falha de provedor. Medir bloqueios, aderência,
isolamento, validade do JSON, recuperação e latência.

### MRF14 — Chat e adaptação de ficha

Nova dor ou limitação relatada no chat reexecuta a triagem e pode criar uma nova
proposta. A ficha ativa nunca é alterada silenciosamente.

### MRF15 — Segurança e governança do corpus

Documentos entram em quarentena e somente versões aprovadas são recuperáveis.
Conteúdo documental é evidência, não instrução capaz de substituir os prompts do
sistema.
