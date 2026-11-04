# Registro de normalização dos requisitos

Este documento torna explícitas as mudanças de redação feitas durante a
consolidação. O propósito é preservar a origem sem carregar ambiguidades para os
prompts de implementação.

| Item | Normalização | Motivo |
|---|---|---|
| RF-03/CA-03.4 | “Cliente habilitado” passou a “elegível à biometria”. | Conta, matrícula, biometria e autorização são estados distintos. |
| RF-05 | “Perfil” passou a papéis acumuláveis. | Uma identidade pode ser cliente, administrador, atendente e/ou instrutor. |
| RF-06/CA-06.4 | SMTP em Docker saiu do critério funcional. | Containerização é requisito não funcional tardio. |
| RF-15/RF-16/RF-17/RF-19/RF-35 | Publicação tecnicamente validada independe do aceite posterior do instrutor. | Correção explícita do responsável: cliente vê treino e usa chat antes do parecer. |
| RF-21/CA-21.4 | Limiar inicial de correspondência de 95%, separado da detecção/qualidade. | Não equivale à acurácia de 95%; a métrica é mapeada pelo adapter facial. |
| RF-24/RF-25 | Mantidos separados. | Cálculo de domínio e exibição são capacidades testáveis distintas. |
| RF-28/RF-29 | “Lucro” passou a faturamento/receita. | Sem despesas não existe cálculo de lucro. |
| RF-31 | Atendente matricula/renova sem exigir pagamento confirmado, comprovante ou módulo financeiro. | Correção explícita do responsável para o projeto acadêmico; substitui a exigência anterior. |
| RF-34/RF-35 | Designação preservada; avaliação profissional agora posterior e independente. | Solicitações posteriores do responsável; rejeição permanece identificada sem ocultar treino/chat. |
| RF-36/RF-37 | Acrescentados reconhecimento facial real e API de catraca fictícia. | Solicitação explícita: referência após matrícula, captura nova, decisão e passagem simulada. |
| MRF01 | Remoção genérica de caracteres virou preservação semântica. | Símbolos e unidades podem ser relevantes para o conteúdo. |
| MRF02 | Mantida similaridade de cosseno e acrescentada abstenção. | Preserva requisito original e trata recuperação insuficiente. |
| MRF04 | Triagem foi colocada antes dos agentes geradores. | Casos bloqueados não devem chegar à geração. |
| MRF05 | Limites também passaram a regras estruturadas. | Banco vetorial/LLM não garante invariantes matemáticas. |
| MRF06 | Rejeições também são persistidas. | Auditoria registra tentativas sem confundi-las com conteúdo validado/publicado. |
| MRF08–MRF15 | Marcados como derivados e pendentes. | Foram propostos na análise, não fornecidos inicialmente como tabela aprovada. |

O texto original permanece recuperável no histórico da conversa e no material
fonte. Antes de FND-01 ser concluído, o responsável deve aceitar as normalizações
ou solicitar ajustes.

## Adições expressamente autorizadas em 2026-11-04

| Item | Alteração | Origem |
|---|---|---|
| RF-35, RF-17, RN-18/RN-33, MRF07/MRF10/MRF14 | A rejeitada continua visível; outra ficha posterior rejeitada exclui o conteúdo da rejeitada anterior, preservando auditoria e treinos executados. | Decisão do responsável sobre substituição de fichas rejeitadas. |
| RF-15/RF-19, RN-15, MRF05/MRF09/MRF11/MRF14 | Adaptação por saúde depende de evidência pertinente recuperada do corpus aprovado; ausência de suporte impede gerar/publicar adaptação. | Confirmação do responsável sobre evidência obrigatória. |
| RF-21/RF-36 e prompts de acesso | CompreFace confirmado; similarity normalizada 0–1, inicialmente 0,95. | Escolha explícita do responsável; hospedagem e ensaio continuam pendentes. |

Os demais pontos da análise e MRF08–MRF15 não foram aprovados automaticamente.
O MER original em imagem permanece inalterado; prompts de modelagem devem refletir
as decisões acima quando produzirem o modelo lógico.

## Decisões posteriores: limite, recursos e idioma

| Item | Alteração confirmada | Efeito |
|---|---|---|
| RF-17/RN-38 | Até 15 versões publicadas completas por cliente, incluindo vigente | Publicar excedente exclui conteúdo mais antigo; preserva auditoria/execuções existentes e numeração crescente. |
| RF-35 | Última rejeitada também está sujeita ao limite global | Substituição por nova rejeição continua; limite pode expirar antiga aceita/rejeitada independentemente do parecer. |
| RF-15/RF-19/RF-32/RN-37 | Equipamentos e relação com exercícios no MVP | Inventário mantido por administrador restringe geração e publicação; EQP-01 é antecipado. |
| RN-39/MRF02/MRF05/MRF11/MRF14 | Produto em português com fontes estrangeiras permitidas | Avaliar recuperação/tradução; originais preservados, sem traduzir todo o acervo nesta fase. |
| MRF01–MRF15 | Tabela completa com atores, módulos e 75 critérios identificados | Completar especificação não fecha GATE-04 nem aprova critérios clínicos ainda indefinidos. |

Não foram criados dados de exemplo, código de aplicação ou mudanças no MER em imagem.
Esses dados serão tratados nos prompts de implementação quando solicitados.

## Atualização autorizada: Agentic RAG em 2026-11-04

O responsável solicitou incorporar a proposta de 19 macrorequisitos aos documentos
e somente aos prompts de RAG/IA. Os estados de pendência dos MRFs nos registros
anteriores são históricos; escolhas técnicas, clínicas e parâmetros não resolvidos
continuam pendentes em GATE-04, sem aprovação automática de corpus ou políticas.

| Item | Alteração atual | Rastreabilidade |
|---|---|---|
| MRF01–MRF15 | Preservados os 75 identificadores, com adequações agentivas e 15 critérios adicionais | MRF04.1 passa a incluir pesquisa dinâmica; orçamento/revisor/privacidade permanecem controlados. |
| MRF16–MRF19 | Planejamento, ferramentas, pesquisa iterativa e suficiência | 20 critérios novos; total canônico de 110. |
| MOD-05/MOD-06 | Ferramentas de conhecimento separadas da decisão/orquestração | Mesmos módulos e monólito; sem framework novo escolhido. |
| Dados | Especificação de execução, etapas, evidências e avaliações em PostgreSQL | Modelo lógico/migrations ainda futuros; MER original intacto. |
| Prompts | Somente 12 cartões em 05-ia-rag atualizados, sem mudar dependências | 55 arquivos de prompts fora do diretório preservados, inclusive mestre/manifesto/fundação/treinos. |

Naquela entrega, referências antigas fora de RAG/IA foram preservadas por limite
de escopo. A revisão geral seguinte as corrige sem fechar gates técnicos.

## Revisão geral antes da implementação

- Mestre, fundação, manifesto e VAL-01 passam a apontar MRF01–MRF19; origem
  derivada não significa que a aprovação funcional atual precise ser pedida novamente.
- RF-20 mantém seu ID e passa a nomear identificação facial, distinguindo-a da
  passagem de RF-37. Não é exigido webhook inexistente do provedor.
- RF-31 mantém seu ID e nomeia matrícula/vínculo com plano, refletindo a decisão
  anterior de matrícula manual independente de pagamento.
- REC-007 é alinhada a DEC-008/RF-34, que já exigem responsável principal vigente.
- O alcance de inativação de conta/perfil continua pendente; nenhuma opção foi
  escolhida nesta revisão. Esquema de onboarding também exige campos/unidades e
  obrigatoriedade aprovados antes de ONB-02, sem fechar todo GATE-04 por inferência.
- Pré-condições de FND-03, comandos de AI-01/INF-01 e escopos de manutenção DOC
  foram alinhados para eliminar dependências implícitas impossíveis de satisfazer.

Ver [revisão vigente e checklist](../testes/revisao-dos-prompts.md). O histórico
detalhado de versões anteriores permanece no Git; contagens antigas não são a
especificação atual. Nenhum ID funcional ou critério identificado foi removido.
