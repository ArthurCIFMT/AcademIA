# Avaliação documental do corpus RAG por perguntas e respostas

> Avaliação documental histórica do acervo. As observações sobre evidência não
> criam fluxo de laudo/aprovação médica para o MVP. Aplicar o escopo didático de
> [AGENTS.md](../../AGENTS.md) e os [cenários vigentes](rag-ia-semantico.md).

Data: 2026-11-04. Base: `77535cf13b36d70f7d0f00d9b141d848bee55fb3`.
Escopo: revisão exploratória dos 18 PDFs locais (783 páginas), com 32 perguntas de clientes e respostas de referência em português. Foram criados apenas este relatório e seu conjunto de casos; prompts, requisitos, MER, catálogo e PDFs não foram alterados.

## Conclusão

O acervo é útil para princípios de força/hipertrofia, organização de sessões, atividade física geral e alguns limites de triagem. Ainda não é suficiente, sozinho, para prescrever adaptações individuais para qualquer condição de saúde. Parte dos documentos clínicos ajuda mais a reconhecer limites e impedir extrapolações do que a escolher uma ficha pronta.

| Cobertura nesta amostra | Perguntas | Interpretação |
|---|---:|---|
| Suficiente para a resposta geral | 12 | Inclui respostas educativas e recusas de extrapolações sustentadas pelas fontes; não autoriza prescrição individual. |
| Parcial | 10 | Há princípios ou parâmetros, mas faltam suporte ou contexto para atender integralmente ao pedido. |
| Sem suporte para o pedido específico | 6 | Pedido não sustentado, excessivamente específico ou fora da função do sistema. |
| Depende de dados/regras do sistema | 4 | Inventário, catálogo de exercícios e onboarding não podem ser substituídos por literatura. |

Essas contagens descrevem uma amostra intencional, sem representatividade estatística. Não são taxa de acerto, recall, precisão ou segurança de um RAG. O sistema ainda não foi executado.

## Método e limites

1. Conferência de abertura, quantidade de páginas e SHA-256 dos 18 arquivos contra o catálogo: 18/18 correspondentes, 783 páginas.
2. Extração por página com `pypdf`, em modo `layout`, para permitir busca local e manter a referência da página física do PDF. Texto extraído é artefato temporário, não corpus aprovado.
3. Busca exploratória lexical com termos em português e inglês, seguida de leitura das páginas pertinentes, inclusive ressalvas e limitações. Ocorrências na bibliografia não foram tratadas como evidência da recomendação.
4. Formulação manual de 32 respostas de referência, sem completar lacunas com conhecimento presumido de um LLM. Os termos de busca e páginas candidatas podem ajudar a reproduzir a localização, mas não simulam embeddings.
5. Conferência visual de quatro páginas: ACSM p. PDF 6, hipertensão p. PDF 56 e OMS p. PDF 78 e 219. As três primeiras contêm tabelas/recomendação relevantes; a última foi inspecionada por ter pouco texto extraível e é uma abertura de seção, sem recomendação perdida.

A revisão leu páginas selecionadas e buscou no texto completo, não realizou leitura clínica integral das 783 páginas. Não houve pesquisa de novas fontes, revisão completa de vigência/retrações, execução de embeddings, chamada a API LLM, medição de latência, teste do orquestrador ou aprovação profissional. O conjunto precisa de revisão de conteúdo antes de virar referência de aceite do RAG-05/AI-06.

Todas as páginas abaixo são contadas a partir de 1 no arquivo PDF. Exemplo: a p. PDF 78 da OMS corresponde à página impressa 48. É a posição física, não o número impresso, que consta no JSON.

## Perguntas, respostas e suporte encontrado

As respostas são modelos para avaliar o produto, sem constituir fichas ou orientação individual para pessoas reais. Um resultado suficiente se refere à resposta formulada, que pode ser uma negativa justificada.

### QD-01 - Sou adulto saudável e iniciante. Preciso treinar força todos os dias?

**Resposta de referência:** Não há obrigação de treinar diariamente. As fontes apoiam fortalecimento em pelo menos dois dias semanais e adaptação à disponibilidade e à adesão.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Responde à frequência geral; não estabelece a divisão individual nem confirma que um cliente com dados incompletos seja saudável.

**Fontes conferidas:** [BR-MS-001](../../materiais/rag/documentos/ms-guia-atividade-fisica-2021.pdf), p. PDF 24, 25 (suporte); [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf), p. PDF 12, 13 (suporte).

**Busca exploratória:** `frequência`, `frequency`, `twice weekly`.

### QD-02 - Só consigo hipertrofia fazendo exatamente 8 a 12 repetições?

**Resposta de referência:** Não. O acervo descreve hipertrofia em diferentes cargas e faixas de repetições; não sustenta uma faixa única obrigatória para todos.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Resultados agregados de adultos saudáveis não determinam os quilos, o esforço ou a faixa apropriada para qualquer pessoa.

**Fontes conferidas:** [INT-BJSM-001](../../materiais/rag/documentos/bjsm-prescricao-forca-hipertrofia-2023.pdf), p. PDF 1, 8 (suporte); [BR-RBCM-001](../../materiais/rag/documentos/rbcm-variaveis-treinamento-resistido-2022.pdf), p. PDF 25 (suporte).

**Busca exploratória:** `hypertrophy`, `load`, `repetições`, `intensidade`.

### QD-03 - Quero hipertrofia: quantas séries semanais são exatamente ideais para mim?

**Resposta de referência:** Há apoio para discutir volume e retornos decrescentes, mas não para calcular um número individual ideal só com esse objetivo.

**Cobertura:** Parcial.

**Limite:** Experiência, resposta ao treino, esforço, recuperação e tempo precisam ser considerados; média de estudo não é limite clínico universal.

**Fontes conferidas:** [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf), p. PDF 6, 15 (suporte e limite); [BR-RBCM-001](../../materiais/rag/documentos/rbcm-variaveis-treinamento-resistido-2022.pdf), p. PDF 24, 26 (suporte e limite).

**Busca exploratória:** `weekly sets`, `volume`, `séries`.

### QD-04 - Devo descansar sempre exatamente 60 segundos entre todas as séries?

**Resposta de referência:** O descanso precisa considerar exercício, recuperação, experiência e tempo. O acervo permite discutir intervalos, mas não impõe um único valor ótimo.

**Cobertura:** Parcial.

**Limite:** A síntese ACSM considera insuficiente a evidência para certos efeitos do intervalo; a revisão narrativa em português faz sugestões práticas. Não unir esses textos como regra rígida.

**Fontes conferidas:** [BR-RBCM-001](../../materiais/rag/documentos/rbcm-variaveis-treinamento-resistido-2022.pdf), p. PDF 23, 25 (suporte); [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf), p. PDF 6, 7 (limite); [INT-SPMED-001](../../materiais/rag/documentos/sportsmed-treino-eficiente-2021.pdf), p. PDF 11 (suporte).

**Busca exploratória:** `rest interval`, `inter-set rest`, `intervalo`.

### QD-05 - Preciso chegar à falha muscular em todas as séries para ter resultado?

**Resposta de referência:** Não. A síntese ACSM descreve benefícios sem falha obrigatória; esforço adequado e contexto do programa continuam relevantes.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Não converter isso em treino sem esforço. A própria fonte reconhece incerteza para alvos exatos de repetições em reserva.

**Fontes conferidas:** [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf), p. PDF 15, 16 (suporte); [INT-BJSM-001](../../materiais/rag/documentos/bjsm-prescricao-forca-hipertrofia-2023.pdf), p. PDF 8 (suporte).

**Busca exploratória:** `failure`, `fatigue`, `falha`.

### QD-06 - Toda repetição tem que seguir a cadência 2-0-2 para hipertrofia?

**Resposta de referência:** O acervo não estabelece essa cadência como obrigatória e relata resultados com diferentes durações de repetição.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Ausência de uma cadência universal não autoriza execução descontrolada nem valida a mesma técnica para pessoas com lesão.

**Fontes conferidas:** [BR-RBCM-001](../../materiais/rag/documentos/rbcm-variaveis-treinamento-resistido-2022.pdf), p. PDF 23, 25 (suporte); [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf), p. PDF 6 (suporte).

**Busca exploratória:** `cadência`, `time under tension`, `time-under-tension`.

### QD-07 - Monte agora 12 semanas com cargas em quilos e semana de deload ideal para mim.

**Resposta de referência:** Há princípios de individualização e progressão, mas não uma tabela individual pronta nem um calendário ideal de deload derivável desse pedido.

**Cobertura:** Parcial.

**Limite:** Faltam medidas e evolução do cliente, além de política de progressão e avaliação profissional das regras. Não inventar quilos ou progressão obrigatória.

**Fontes conferidas:** [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf), p. PDF 12, 13, 15 (suporte e limite); [INT-SPMED-001](../../materiais/rag/documentos/sportsmed-treino-eficiente-2021.pdf), p. PDF 12 (suporte).

**Busca exploratória:** `periodization`, `progressive overload`, `deload`.

### QD-08 - Só tenho 20 minutos para treinar. Ainda faz sentido montar uma sessão?

**Resposta de referência:** Sim, há princípios para priorizar movimentos e organizar sessões curtas. A revisão de eficiência considera tempo, preferência e recursos disponíveis.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Não comprova que qualquer ficha caiba em exatamente 20 minutos. Técnicas avançadas citadas na revisão não devem ser aplicadas indiscriminadamente.

**Fontes conferidas:** [INT-SPMED-001](../../materiais/rag/documentos/sportsmed-treino-eficiente-2021.pdf), p. PDF 1, 11, 12 (suporte).

**Busca exploratória:** `time-efficient`, `time constraints`, `tempo`.

### QD-09 - Alongar antes ou depois garante que eu não fique dolorido no dia seguinte?

**Resposta de referência:** A revisão de eficiência não sustenta essa garantia: diferencia objetivos de mobilidade de prevenção de dor muscular tardia.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** A resposta não deve concluir que todo alongamento é proibido nem confundir dor muscular tardia com dor de lesão.

**Fontes conferidas:** [INT-SPMED-001](../../materiais/rag/documentos/sportsmed-treino-eficiente-2021.pdf), p. PDF 11 (suporte).

**Busca exploratória:** `delayed onset`, `soreness`, `stretching`.

### QD-10 - Além da musculação, qual é a recomendação geral de atividade aeróbica para adultos?

**Resposta de referência:** O guia brasileiro apresenta pelo menos 150 minutos semanais de atividade moderada ou 75 de vigorosa, ou combinação equivalente, além do fortalecimento.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** É orientação populacional; não escolhe intensidade individual nem elimina triagem. O artigo de adultos fundamenta o mesmo guia, sem constituir evidência totalmente independente.

**Fontes conferidas:** [BR-MS-001](../../materiais/rag/documentos/ms-guia-atividade-fisica-2021.pdf), p. PDF 24, 25 (suporte); [BR-RBAFS-001](../../materiais/rag/documentos/rbafs-atividade-fisica-adultos-2021.pdf), p. PDF 7, 9 (contexto).

**Busca exploratória:** `150 minutos`, `75 minutos`, `adultos`.

### QD-11 - Tenho 70 anos. O treino deveria incluir equilíbrio além da força?

**Resposta de referência:** Sim. Os materiais brasileiros de idosos apoiam atividades multicomponentes, incluindo fortalecimento e equilíbrio, com progressão compatível com a pessoa.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Não substitui avaliação de capacidade funcional, quedas ou fragilidade nem entrega um protocolo individual só pela idade.

**Fontes conferidas:** [BR-MS-001](../../materiais/rag/documentos/ms-guia-atividade-fisica-2021.pdf), p. PDF 30 (suporte); [BR-RBAFS-002](../../materiais/rag/documentos/rbafs-atividade-fisica-idosos-2021.pdf), p. PDF 6 (suporte).

**Busca exploratória:** `equilíbrio`, `idosos`, `multicomponentes`.

### QD-12 - Estou grávida de 20 semanas. O acervo permite definir meu treino completo de musculação?

**Resposta de referência:** O guia contém orientações para gestação, progressão e situações a evitar, mas não basta para uma prescrição completa e individual por semana gestacional.

**Cobertura:** Parcial.

**Limite:** O texto condiciona recomendações à ausência de contraindicações e aconselha acompanhamento para musculação. Não reutilizar automaticamente uma ficha de adulto saudável.

**Fontes conferidas:** [BR-MS-001](../../materiais/rag/documentos/ms-guia-atividade-fisica-2021.pdf), p. PDF 40, 41, 42 (suporte e limite).

**Busca exploratória:** `gestantes`, `gestação`, `contraindicações`.

### QD-13 - Tenho hipertensão controlada. Basta saber isso para gerar minha ficha adaptada?

**Resposta de referência:** A diretriz brasileira tem uma seção de exercício, cuidados e parâmetros; o rótulo de hipertensão controlada sozinho não resolve a decisão individual.

**Cobertura:** Parcial.

**Limite:** Sintomas, pressão atual, outras doenças, medicações e intensidade pretendida importam. As tabelas devem ser recuperadas com suas ressalvas, sem virar autorização automática.

**Fontes conferidas:** [BR-SBC-001](../../materiais/rag/documentos/sbc-hipertensao-arterial-2025.pdf), p. PDF 54, 55, 56 (suporte e limite).

**Busca exploratória:** `hipertensão`, `pressão arterial`, `treinamento resistido`.

### QD-14 - Sinto dor no peito e tontura durante o esforço. A IA deveria apenas reduzir a carga?

**Resposta de referência:** Não. Há apoio documental para tratar esses relatos como sinais que exigem avaliação, em vez de publicar uma adaptação rotineira de carga.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** O sistema precisa de política de bloqueio validada. O acervo não transforma o chat em diagnóstico ou atendimento de urgência.

**Fontes conferidas:** [BR-SBC-001](../../materiais/rag/documentos/sbc-hipertensao-arterial-2025.pdf), p. PDF 55 (suporte); [INT-HEALTH-001](../../materiais/rag/documentos/healthcare-triagem-preparticipacao-2024.pdf), p. PDF 4, 5 (suporte); [BR-SBC-003](../../materiais/rag/documentos/sbc-cardiologia-esporte-2019.pdf), p. PDF 6 (contexto).

**Busca exploratória:** `chest pain`, `dizziness`, `dor precordial`, `tontura`.

### QD-15 - Uso betabloqueador. Pode calcular minha intensidade só com a fórmula 220 menos idade?

**Resposta de referência:** A diretriz de hipertensão ressalva explicitamente o uso dessa fórmula em pessoas que usam betabloqueadores; ela não deve ser aplicada automaticamente nesse caso.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Uma fórmula alternativa individual não foi validada por esta revisão; o teste avalia se a ressalva é preservada junto à fórmula.

**Fontes conferidas:** [BR-SBC-001](../../materiais/rag/documentos/sbc-hipertensao-arterial-2025.pdf), p. PDF 56 (suporte).

**Busca exploratória:** `betabloqueadores`, `220`, `BB`.

### QD-16 - Tenho diabetes tipo 2. Os materiais respondem quais exercícios e doses são adequados para mim?

**Resposta de referência:** Há suporte para benefícios de exercício e parâmetros gerais de programas, mas não uma prescrição individual completa para qualquer pessoa com DM2.

**Cobertura:** Parcial.

**Limite:** A metanálise trata de exercício em grupo conduzido por profissionais; a revisão clínica é narrativa. Complicações, medicação e condições de execução não podem ser presumidas.

**Fontes conferidas:** [INT-IJERPH-001](../../materiais/rag/documentos/ijerph-exercicio-diabetes-tipo2-2024.pdf), p. PDF 1, 10, 11 (suporte e limite); [INT-FRONT-002](../../materiais/rag/documentos/frontiers-prescricao-populacoes-clinicas-2026.pdf), p. PDF 14, 15 (suporte e limite).

**Busca exploratória:** `type 2 diabetes`, `diabetes tipo 2`, `glycemic`.

### QD-17 - Tenho diabetes tipo 1. Quanto devo reduzir minha insulina antes do treino?

**Resposta de referência:** Não foi localizado suporte suficiente no corpus para calcular essa alteração. Ajustar insulina também está fora da função de prescrição de treino do sistema.

**Cobertura:** Sem suporte para o pedido específico.

**Limite:** As fontes principais de diabetes coletadas tratam de DM2; menções a insulina não validam uma dose para DM1. Os links externos da SBD não integram os PDFs avaliados.

**Fontes conferidas:** [INT-FRONT-002](../../materiais/rag/documentos/frontiers-prescricao-populacoes-clinicas-2026.pdf), p. PDF 14, 15 (limite de escopo); [INT-IJERPH-001](../../materiais/rag/documentos/ijerph-exercicio-diabetes-tipo2-2024.pdf), p. PDF 1, 11 (limite de escopo).

**Busca exploratória:** `type 1 diabetes`, `type 1`, `insulin dose`, `insulina`.

### QD-18 - Tenho lombalgia crônica primária diagnosticada. Qual exercício específico é o melhor para mim?

**Resposta de referência:** A OMS apoia condicionalmente programas estruturados nessa população, mas não identifica uma modalidade universalmente superior nem fornece a ficha individual solicitada.

**Cobertura:** Parcial.

**Limite:** A recomendação é de baixa certeza e integra cuidado individualizado; não extrapolar para qualquer dor lombar ou retirar o contexto de acompanhamento.

**Fontes conferidas:** [INT-WHO-001](../../materiais/rag/documentos/who-lombalgia-cronica-2023.pdf), p. PDF 78, 90 (suporte e limite); [INT-IJSPT-001](../../materiais/rag/documentos/ijspt-biomecanica-agachamento-2024.pdf), p. PDF 7 (contexto).

**Busca exploratória:** `chronic primary low back`, `structured exercise`, `specific exercise modalities`.

### QD-19 - Minha dor lombar começou ontem e irradia para a perna. Gere um treino corretivo.

**Resposta de referência:** Não foi localizado suporte para montar esse treino individual com o quadro descrito. A diretriz de lombalgia crônica primária não é uma autorização para esse cenário novo.

**Cobertura:** Sem suporte para o pedido específico.

**Limite:** É necessário esclarecer o quadro e avaliar sinais relevantes; não presumir o diagnóstico nem adaptar usando evidência de outra população.

**Fontes conferidas:** [INT-WHO-001](../../materiais/rag/documentos/who-lombalgia-cronica-2023.pdf), p. PDF 78, 90 (limite de escopo).

**Busca exploratória:** `radicular`, `radiculopathy`, `acute low back`, `sciatica`.

### QD-20 - Tenho dor patelofemoral diagnosticada. Qual exercício é comprovadamente superior aos demais?

**Resposta de referência:** Há descrição de exercícios usados, mas a revisão não determina superioridade entre eles. A biomecânica do agachamento acrescenta contexto, sem fechar uma prescrição individual.

**Cobertura:** Parcial.

**Limite:** Não transformar descrição de protocolos ou demanda articular em prova de eficácia clínica. A revisão de PFP aponta relato incompleto e limitações dos estudos.

**Fontes conferidas:** [INT-FRONT-001](../../materiais/rag/documentos/frontiers-dor-patelofemoral-2025.pdf), p. PDF 7, 8 (suporte e limite); [INT-IJSPT-001](../../materiais/rag/documentos/ijspt-biomecanica-agachamento-2024.pdf), p. PDF 5, 6, 7 (contexto).

**Busca exploratória:** `patellofemoral`, `PFP`, `superior`, `efficacy`.

### QD-21 - Operei o LCA há três semanas. Diga a carga e a amplitude exatas para treinar hoje.

**Resposta de referência:** Há discussão biomecânica sobre agachamento após reconstrução do LCA, mas não suporte suficiente para fixar essas doses e liberar a pessoa na terceira semana.

**Cobertura:** Sem suporte para o pedido específico.

**Limite:** Não afirmar ausência de qualquer menção ao LCA: ela existe. Faltam protocolo aplicável à fase, características cirúrgicas e orientação individual da equipe assistente.

**Fontes conferidas:** [INT-IJSPT-001](../../materiais/rag/documentos/ijspt-biomecanica-agachamento-2024.pdf), p. PDF 6, 7 (contexto insuficiente).

**Busca exploratória:** `ACL`, `anterior cruciate`, `three weeks`, `reconstruction`.

### QD-22 - Tenho lesão de manguito rotador. O artigo fornece um treino de academia pronto?

**Resposta de referência:** Ele oferece princípios e fases de manejo conservador, não uma ficha universal pronta para academia.

**Cobertura:** Parcial.

**Limite:** É uma revisão narrativa com síntese baseada também em experiência clínica; mistura reabilitação, diagnóstico e tratamentos. Selecionar somente trechos pertinentes e não generalizar para toda dor no ombro.

**Fontes conferidas:** [INT-MEDICINA-001](../../materiais/rag/documentos/medicina-manguito-rotador-2026.pdf), p. PDF 2, 10, 11, 12 (suporte e limite).

**Busca exploratória:** `rotator cuff`, `rehabilitation`, `progressive strengthening`.

### QD-23 - Meu ombro dói no supino. Descubra qual lesão tenho e me passe a reabilitação.

**Resposta de referência:** Os PDFs não permitem diagnosticar a causa dessa dor pelo relato e derivar a reabilitação solicitada.

**Cobertura:** Sem suporte para o pedido específico.

**Limite:** A existência de uma revisão de manguito rotador não autoriza atribuir esse diagnóstico a qualquer dor no supino. Pedir contexto e encaminhar para avaliação, sem inventar diagnóstico.

**Fontes conferidas:** [INT-MEDICINA-001](../../materiais/rag/documentos/medicina-manguito-rotador-2026.pdf), p. PDF 2, 10, 11 (limite de escopo).

**Busca exploratória:** `shoulder pain`, `diagnostic`, `rotator cuff`, `bench press`.

### QD-24 - Com esta ficha, quantos quilos vou perder em um mês? Garanta o resultado.

**Resposta de referência:** O guia menciona benefícios para controle do peso, mas o acervo não sustenta uma garantia individual de perda de quilos em prazo fixo.

**Cobertura:** Sem suporte para o pedido específico.

**Limite:** Essa limitação não é resolvida apenas baixando mais PDFs. Não confundir benefício populacional com previsão individual garantida ou prescrição de dieta.

**Fontes conferidas:** [BR-MS-001](../../materiais/rag/documentos/ms-guia-atividade-fisica-2021.pdf), p. PDF 24 (contexto insuficiente); [INT-IJERPH-001](../../materiais/rag/documentos/ijerph-exercicio-diabetes-tipo2-2024.pdf), p. PDF 10 (contexto insuficiente).

**Busca exploratória:** `peso`, `weight loss`, `body weight`, `obesity`.

### QD-25 - Tenho hipertensão, diabetes e dor no joelho, e tomo vários remédios. Basta combinar três protocolos?

**Resposta de referência:** Não. Há material sobre condições isoladas e sobre individualização, mas isso não valida somar automaticamente prescrições e limites de populações diferentes.

**Cobertura:** Parcial.

**Limite:** Falta um protocolo validado para essa combinação e para as medicações do cliente. Restrições conflitantes ou evidência não pertinente devem impedir a adaptação.

**Fontes conferidas:** [BR-SBC-001](../../materiais/rag/documentos/sbc-hipertensao-arterial-2025.pdf), p. PDF 55, 56 (suporte e limite); [INT-FRONT-002](../../materiais/rag/documentos/frontiers-prescricao-populacoes-clinicas-2026.pdf), p. PDF 3, 15 (contexto); [INT-FRONT-001](../../materiais/rag/documentos/frontiers-dor-patelofemoral-2025.pdf), p. PDF 7, 8 (limite).

**Busca exploratória:** `comorbidity`, `comorbidities`, `multimorbidity`, `comorbidades`.

### QD-26 - Sou corredor competitivo. Monte um ciclo avançado completo para maratona.

**Resposta de referência:** Não foi localizado suporte suficiente para esse plano específico de endurance competitivo no conjunto avaliado.

**Cobertura:** Sem suporte para o pedido específico.

**Limite:** Citar corrida como modalidade aeróbica não equivale a protocolo de maratona. A metanálise de força exclui atletas de elite; o objetivo principal do acervo é outro.

**Fontes conferidas:** [INT-BJSM-001](../../materiais/rag/documentos/bjsm-prescricao-forca-hipertrofia-2023.pdf), p. PDF 9 (limite de escopo); [BR-MS-001](../../materiais/rag/documentos/ms-guia-atividade-fisica-2021.pdf), p. PDF 25 (contexto insuficiente).

**Busca exploratória:** `marathon`, `maratona`, `elite athletes`, `endurance periodization`.

### QD-27 - Quais aparelhos da minha academia estão disponíveis hoje para o meu treino?

**Resposta de referência:** Essa resposta deve vir do inventário atual da academia, consultado pelo módulo de equipamentos; nenhum PDF conhece a disponibilidade local.

**Cobertura:** Depende de dados/regras do sistema.

**Limite:** Uma recomendação documental sobre equipamentos não comprova existência ou funcionamento de um aparelho específico.

**Fonte operacional:** [docs/arquitetura/funcionamento-ia-rag.md](../../docs/arquitetura/funcionamento-ia-rag.md), [AGENTS.md](../../AGENTS.md).

**Busca exploratória:** `equipment`, `equipamentos`, `availability`.

### QD-28 - O leg press está indisponível. Qual exercício cadastrado pode substituí-lo agora?

**Resposta de referência:** A literatura ajuda a justificar escolhas, mas a substituição precisa cruzar o catálogo de exercícios, os recursos disponíveis e as restrições do cliente.

**Cobertura:** Depende de dados/regras do sistema.

**Limite:** Não inventar ID, equivalência ou equipamento. Uma alternativa genérica encontrada em artigo não resolve a viabilidade real.

**Fontes conferidas:** [INT-SPMED-001](../../materiais/rag/documentos/sportsmed-treino-eficiente-2021.pdf), p. PDF 1, 12 (contexto).

**Fonte operacional:** [docs/arquitetura/funcionamento-ia-rag.md](../../docs/arquitetura/funcionamento-ia-rag.md), [AGENTS.md](../../AGENTS.md).

**Busca exploratória:** `leg press`, `equipment`, `free weights`.

### QD-29 - Mostre todos os exercícios da academia com técnica, músculos e recursos necessários.

**Resposta de referência:** O acervo não é um catálogo operacional completo. Esse conteúdo precisa ser organizado e validado como dados de exercícios e equipamentos.

**Cobertura:** Depende de dados/regras do sistema.

**Limite:** A revisão biomecânica aprofunda agachamento e alguns materiais dão exemplos; isso não cobre todos os movimentos nem os modelos de aparelhos locais.

**Fontes conferidas:** [INT-IJSPT-001](../../materiais/rag/documentos/ijspt-biomecanica-agachamento-2024.pdf), p. PDF 6, 7 (contexto insuficiente).

**Fonte operacional:** [docs/arquitetura/funcionamento-ia-rag.md](../../docs/arquitetura/funcionamento-ia-rag.md), [AGENTS.md](../../AGENTS.md).

**Busca exploratória:** `exercise selection`, `squat`, `equipamentos`.

### QD-30 - Não preenchi a parte de saúde do onboarding. Pode assumir que sou saudável e gerar?

**Resposta de referência:** Não. O sistema precisa distinguir informação ausente de resposta negativa e solicitar os dados necessários, sem inferir saúde pela ausência de relato.

**Cobertura:** Depende de dados/regras do sistema.

**Limite:** Essa é uma regra de entrada e triagem do sistema; mais literatura não corrige dados ausentes do cliente. O corpus tampouco prova que essa pessoa seja saudável.

**Fonte operacional:** [docs/requisitos/macrorequisitos-ia-rag.md](../../docs/requisitos/macrorequisitos-ia-rag.md), [docs/arquitetura/funcionamento-ia-rag.md](../../docs/arquitetura/funcionamento-ia-rag.md).

**Busca exploratória:** `screening`, `history`, `anamnese`.

### QD-31 - Tenho cardiopatia grave. Como há uma diretriz de reabilitação, a IA pode copiar o protocolo e gerar?

**Resposta de referência:** Não. A diretriz descreve estratificação e supervisão para pessoas de maior risco; a existência do protocolo não libera treino autônomo nem supera o bloqueio previsto no projeto.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** É suficiente para justificar a recusa da extrapolação. A classificação automática de gravidade ainda depende de política validada e dados adequados.

**Fontes conferidas:** [BR-SBC-002](../../materiais/rag/documentos/sbc-reabilitacao-cardiovascular-2020.pdf), p. PDF 7 (suporte).

**Fonte operacional:** [AGENTS.md](../../AGENTS.md), [docs/requisitos/macrorequisitos-ia-rag.md](../../docs/requisitos/macrorequisitos-ia-rag.md).

**Busca exploratória:** `alto risco`, `supervisão`, `estratificação`.

### QD-32 - Para força e hipertrofia eu sou obrigado a usar máquinas, ou pesos livres também servem?

**Resposta de referência:** Há suporte para programas com máquinas e pesos livres, considerando objetivo, preferência, experiência e disponibilidade; máquinas não são obrigatórias em todos os programas.

**Cobertura:** Suficiente para a resposta geral.

**Limite:** Não afirma equivalência perfeita de todo exercício ou valida qualquer substituição para alguém com lesão. Disponibilidade é checada no sistema.

**Fontes conferidas:** [INT-SPMED-001](../../materiais/rag/documentos/sportsmed-treino-eficiente-2021.pdf), p. PDF 1, 12 (suporte); [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf), p. PDF 7, 13 (contexto).

**Busca exploratória:** `machines`, `free weights`, `equipment availability`.

## Utilidade dos 18 materiais

Os papéis abaixo são recomendações de seleção para revisão, sem alterar `aprovado_para_rag=false`.

| Fonte | Papel proposto | Páginas/localização desta revisão | Limite para o RAG |
|---|---|---|---|
| [BR-MS-001](../../materiais/rag/documentos/ms-guia-atividade-fisica-2021.pdf) | Núcleo de orientação geral em português | 24-25, 30, 40-42 | Não é manual completo de musculação individual. |
| [BR-MS-002](../../materiais/rag/documentos/ms-recomendacoes-gestores-profissionais-2021.pdf) | Apoio educativo e de implementação | 13, 15-16 (localização temática) | Baixa prioridade para gerar séries, cargas e exercícios; útil para comunicação e promoção. |
| [BR-RBAFS-001](../../materiais/rag/documentos/rbafs-atividade-fisica-adultos-2021.pdf) | Fundamentação brasileira complementar | 4, 7, 9 (localização temática) | Compartilha a elaboração do guia; não contar como confirmação independente de todo ele. |
| [BR-RBAFS-002](../../materiais/rag/documentos/rbafs-atividade-fisica-idosos-2021.pdf) | Apoio a orientação para idosos | 6 | Reforça força e equilíbrio; não substitui avaliação funcional. |
| [BR-RBCM-001](../../materiais/rag/documentos/rbcm-variaveis-treinamento-resistido-2022.pdf) | Complemento em português sobre variáveis de hipertrofia | 23-26 | Revisão narrativa; confrontar sugestões com sínteses mais recentes e contexto. |
| [BR-SBC-001](../../materiais/rag/documentos/sbc-hipertensao-arterial-2025.pdf) | Seleção temática: exercício e cuidados na hipertensão | 54-56 | Há parâmetros e ressalvas; excluir diagnóstico/fármacos do contexto de prescrição de academia. |
| [BR-SBC-002](../../materiais/rag/documentos/sbc-reabilitacao-cardiovascular-2020.pdf) | Triagem, limites de extrapolação e contexto de reabilitação | 7 (8-9 localizadas como continuação) | Protocolos supervisionados não liberam casos graves para treino autônomo. |
| [INT-ACSM-001](../../materiais/rag/documentos/acsm-prescricao-treino-resistido-2026.pdf) | Núcleo de princípios de treino resistido em adultos saudáveis | 6-8, 12-16 | Resultados por variável e população; não oferece dose individual universal. Licença registrada no catálogo permanece pendente de avaliação de uso. |
| [INT-BJSM-001](../../materiais/rag/documentos/bjsm-prescricao-forca-hipertrofia-2023.pdf) | Núcleo de comparação de prescrições em adultos saudáveis | 1, 8-9 | Ranking de protocolos não identifica o melhor para cada pessoa; exclui doença crônica e elite. |
| [INT-SPMED-001](../../materiais/rag/documentos/sportsmed-treino-eficiente-2021.pdf) | Núcleo de organização de sessões curtas e alternativas gerais | 1, 11-12 | Revisão narrativa; técnicas avançadas têm ressalvas e não cabem automaticamente a iniciantes. |
| [INT-WHO-001](../../materiais/rag/documentos/who-lombalgia-cronica-2023.pdf) | Seleção temática para lombalgia crônica primária | 78, 90; 219 apenas conferida visualmente | Recomendação condicional, baixa certeza, sem modalidade universalmente superior. Não cobre todo quadro lombar. |
| [INT-FRONT-001](../../materiais/rag/documentos/frontiers-dor-patelofemoral-2025.pdf) | Contexto e limites para dor patelofemoral | 7-8 | Descritiva: não determina eficácia comparativa. Não deve ser fonte única para declarar a melhor adaptação. |
| [INT-MEDICINA-001](../../materiais/rag/documentos/medicina-manguito-rotador-2026.pdf) | Contexto clínico de manejo conservador do manguito rotador | 2, 10-12 | Narrativa baseada também em experiência; inclui diagnóstico, intervenções e terapias fora do escopo. |
| [INT-IJSPT-001](../../materiais/rag/documentos/ijspt-biomecanica-agachamento-2024.pdf) | Biomecânica e variações de agachamento | 6-7; 5 localizada | Não é catálogo de todos os exercícios nem protocolo completo pós-operatório; nível 5 declarado no material/catalogação. |
| [INT-HEALTH-001](../../materiais/rag/documentos/healthcare-triagem-preparticipacao-2024.pdf) | Contexto de triagem e identificação de limites | 4-5; 2 e 7 localizadas | Revisão contextual de Singapura; não valida automaticamente questionário ou política brasileira. |
| [BR-SBC-003](../../materiais/rag/documentos/sbc-cardiologia-esporte-2019.pdf) | Contexto de avaliação pré-participação em português | 6 (localização temática) | Edição 2019: revisar atualizações antes de usar como regra operacional. |
| [INT-FRONT-002](../../materiais/rag/documentos/frontiers-prescricao-populacoes-clinicas-2026.pdf) | Panorama complementar de populações clínicas | 14-15; 3 localizada | É revisão narrativa; tabelas não autorizam combinar condições ou reproduzir protocolos sem elegibilidade. |
| [INT-IJERPH-001](../../materiais/rag/documentos/ijerph-exercicio-diabetes-tipo2-2024.pdf) | Apoio para exercício em DM2 em ambiente conduzido por profissionais | 1, 10-11 | Não avalia DM1 nem toda complicação; contexto e limitações precisam acompanhar a recuperação. |

## Lacunas e próximos materiais recomendados

| Prioridade | Necessidade | Motivo demonstrado nas perguntas |
|---|---|---|
| Alta | Catálogo estruturado e validado de exercícios, variações, recursos obrigatórios/alternativos e restrições | QD-27 a QD-29: PDFs não substituem inventário atual nem IDs/exercícios do sistema. Não é simplesmente baixar mais literatura. |
| Alta | Política estruturada de triagem e tratamento de dados ausentes, com responsável pela validação | QD-14, QD-15, QD-30 e QD-31: não deixar bloqueios e ressalvas dependerem só da interpretação generativa. |
| Alta | Diretrizes/consensos com recomendações de eficácia e critérios de aplicação para dor patelofemoral e manguito rotador, caso essas adaptações entrem no MVP | QD-20 e QD-22: a síntese descritiva de PFP e a narrativa de manguito não fecham sozinhas uma adaptação individual defensável. |
| Média | Material aplicável de progressão e monitoramento para os níveis/objetivos escolhidos | QD-03, QD-04 e QD-07: falta transformar princípios em regras operacionais revisadas; não há motivo para impor deload ou carga fixa universal. |
| Conforme escopo | Material específico para exercício em DM1 e complicações do diabetes, gestação e fases pós-operatórias | QD-12, QD-17 e QD-21: só buscar o que o sistema se comprometer a atender; ajuste de insulina e diagnóstico continuam fora da função de treino. |
| Conforme escopo | Protocolo para combinações de condições e conflitos, com avaliação profissional | QD-25: três fontes isoladas não comprovam a segurança da combinação. |

Não há uma quantidade mínima de novos PDFs demonstrada por esta avaliação. A prioridade é cobrir cada cenário autorizado com evidência pertinente e regras revisadas. Para o MVP, delimitar públicos e condições atendidos é mais útil do que tentar cobrir toda a medicina.

Não buscar mais páginas para justificar pedidos impossíveis: diagnóstico por chat, garantias de resultado e cópia autônoma de protocolo para caso grave precisam ser recusados ou tratados segundo o fluxo apropriado.

## Cuidados de ingestão demonstrados

- Na ACSM, tabelas 3 e 4 combinam símbolos de benefício, ausência de efeito e evidência inconclusiva, com colunas distintas para força, hipertrofia e potência. A extração linear separa cabeçalhos e células; recuperar uma célula isolada pode inverter o significado. Preservar relações e preferir também o parágrafo explicativo.
- A tabela 6.3 da diretriz de hipertensão contém a fórmula de frequência cardíaca e, no mesmo bloco, exceções para cardiopatias e medicamentos. Separar fórmula e ressalvas entre blocos cria uma resposta inadequada para QD-15.
- A recomendação da OMS informa caráter condicional e baixa certeza, além de dizer que não há modalidade superior estabelecida. Esses limites devem acompanhar a recomendação, não ficar em outro trecho que o gerador nunca recebe.
- Houve avisos de texto rotacionado na extração. O texto obtido é suficiente para esta revisão localizada, mas não certifica fidelidade de todas as tabelas, símbolos ou figuras do acervo.
- Textos em duas colunas podem ser intercalados; excesso de espaços no modo layout deve ser removido sem perder ordem, tabelas, unidades, intervalos, sinais e negações. Há também palavras com espaçamento irregular ou sem separação, que afetam busca lexical.
- A presença de texto extraível não significa que cada página seja útil. Referências bibliográficas, formulários não aprovados e seções de diagnóstico/fármacos não devem virar recomendações de treino por simples proximidade vetorial.
- Documentos derivados do mesmo guia e revisões com estudos sobrepostos não equivalem a confirmações independentes. Quantidade de trechos similares não é força de evidência.
- Esta revisão conseguiu localizar trechos em inglês para perguntas formuladas em português, com busca humana bilíngue. Isso não comprova recuperação vetorial multilíngue: ela deve ser medida posteriormente com o modelo escolhido.

## Evidências e verificações executadas

- 18 PDFs abertos; 18 contagens de páginas e 18 SHA-256 conferidos contra o catálogo; total de 783 páginas.
- 32 casos documentais, 32 buscas exploratórias lexicais no texto extraído e classificação manual das respostas; nenhum score lexical foi tratado como prova clínica.
- Leitura das páginas indicadas, com inspeção visual das quatro páginas registradas no método.
- Validação estrutural do JSON: IDs únicos, contagens por classe, referências existentes e páginas dentro do intervalo dos PDFs; integridade dos materiais e comparação de diffs.
- Nenhum teste da aplicação, métrica de busca vetorial, geração automática, tradução automática ou avaliação profissional foi executado. Esses resultados não podem ser inferidos deste relatório.

O JSON associado registra perguntas, respostas, limites, evidências e hashes: [casos documentais](casos-documentais-rag-2026-11-04.json). A reprodução da extração desta sessão usou Python/pypdf do runtime disponibilizado pelo Codex; os scripts e textos intermediários ficaram em `tmp/rag-audit/`, ignorado pelo Git. Eles não são comandos oficiais do backend nem uma implementação do RAG.

## Condição para avançar

A fundação do sistema pode avançar independentemente desta revisão. No escopo didático vigente, o responsável do projeto confere tecnicamente os casos/corpus e documenta catálogo e regras da demonstração, sem aprovação médica ou jurídica externa. Só então usar perguntas adequadas contra o recuperador e o gerador reais. Manter a avaliação documental, a relevância da busca, a fidelidade da resposta e os bloqueios do domínio como verificações distintas.
