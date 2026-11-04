# Compatibilidade do Agentic RAG com o AcademIA

Data: 2026-11-04. Base anterior: `77535cf13b36d70f7d0f00d9b141d848bee55fb3`.
Origem: autorização do responsável para atualizar documentos/prompts de RAG e IA
segundo a proposta de 19 macrorequisitos, preservando prompts de outros escopos.

## Resultado da análise

O Agentic RAG é compatível com a arquitetura prevista: o LLM escolhe ações de
pesquisa, MOD-06 executa o workflow autorizado e MOD-05 fornece ferramentas de
conhecimento. Não exige microserviços, outro banco operacional ou um framework
adicional. A compatibilidade é de especificação e depende dos contratos, modelo
lógico e testes futuros; não comprova funcionamento, segurança clínica ou ganho
de qualidade em execução.

No checkout há planejamento e materiais, sem backend/frontend executáveis,
schema físico ou migrations implementadas. Portanto não seria correto afirmar
que a solução já foi integrada a um banco existente ou testada com um LLM real.

## Compatibilidade por fronteira

| Área/contrato existente | Avaliação | Adequação dentro de RAG/IA |
|---|---|---|
| Monólito Python e fronteiras tipadas | Compatível | Papéis de agentes ficam em MOD-06; chamadas internas usam interfaces, mensagens/REST usam JSON versionado. Sem acesso direto a tabelas alheias. |
| Identidade e autorização (IAM-03) | Compatível sob contrato | Backend injeta identidade/escopo; executor valida cada ferramenta. Argumento gerado não escolhe outro cliente. |
| Designação (PES-03) | Compatível | Revisão segue instrutor autorizado; pesquisa não muda designação ou permissão. |
| Onboarding (ONB-02/04) | Compatível | Snapshot versionado alimenta triagem/plano; dado ausente continua distinto de resposta negativa. Pedido de complemento não altera formulário por ferramenta. |
| Catálogo (TRN-01) | Compatível | Já prevê candidatos elegíveis; AI-02/03 adaptam a interface como ferramenta de leitura. Não criar catálogo paralelo. |
| Equipamentos (EQP-01) | Compatível | Disponibilidade vem de MOD-10, não da literatura. Revalidação de revisão deve ser consistente na publicação. |
| Ficha/versionamento (TRN-02) | Compatível sob contrato | Serviço do backend publica validada uma vez, aplica retenção e mantém referência da execução; modelo não chama escrita diretamente. |
| Parecer (TRN-03) e consulta (TRN-04) | Compatível | Publicação com parecer PENDENTE, consulta/chat antes do aceite e rejeição visível permanecem. Pesquisa não substitui parecer nem cria aprovação humana. |
| Auditoria/notificações (FND-08/NTF-01) | Compatível | Ações/resultados minimizados e aviso no workflow existente; evitar logs clínicos e segunda fila de revisão. |
| PostgreSQL | Compatível com extensão lógica necessária | Guardar execução, etapas, avaliações e vínculos de evidência. Integridade/idempotência/orçamento exigem schema e migrations futuros de RAG/IA. |
| Banco vetorial especializado | Compatível | Mesma literatura/embeddings: várias chamadas autorizadas ao recuperador. Modelo/dimensão/filtros continuam controlados. Qdrant ainda recomendado. |
| React/TypeScript/REST | Compatível | AI-04/05 mostram estados compreensíveis e retornos estruturados. Não exigem streaming, novas telas de outros módulos ou exposição do executor. |
| Biometria/catraca | Independente | CompreFace e vetores faciais não compõem corpus de treino nem ferramentas do agente. Nenhum prompt de acesso foi modificado. |
| Matrícula/financeiro | Independente | Atendente continua matriculando sem pagamento; agente de treino não oferece ferramentas financeiras. |
| Docker/infraestrutura | Compatível com decisões abertas | Desenvolvimento local e serviços disponíveis antes da containerização; não antecipar Compose ou escolher hospedagem nesta entrega. |

## Dados necessários e limites

A [extensão lógica](../arquitetura/modelo-de-dados/extensao-agentic-rag.md)
representa o que INTERACAO_IA isolada no MER não cobre: execução, plano/revisões,
chamadas, consumo, evidências e avaliações. Vetores ficam especializados; estado
privado de execução fica operacional e autorizado. O PNG/XML original permanece
igual; não há migration aplicada a alterar.

Não guardar prescrições completas em trilha/cache para contornar a exclusão de
RF-17/RF-35. Retenção operacional e tamanho das trilhas precisam de política própria;
o limite de 15 fichas não limita todo o volume do banco. A política deve ser fechada
antes do aceite do armazenamento da execução, sem inventar prazo nesta atualização.

Chamadas externas não mantêm transação SQL longa. Reserva de orçamento e
publicação precisam de controle concorrente. A validação final de aprovação de
fontes e disponibilidade usa serviços proprietários com controle de revisão,
consistente com a transação final. Referência a snapshot não substitui essa garantia.

## Prompts externos congelados e divergências registradas

Foram preservados os 55 arquivos de `docs/prompts/` fora de `05-ia-rag/`, incluindo
mestre, manifesto, contrato/contexto comuns, fundação, treinos, equipamentos,
acesso, financeiro, infraestrutura e validação final. Os 12 cartões internos
recebem os novos requisitos mantendo IDs, títulos e dependências; o total de
61 cartões não cresce. Os complementos de TST-01 tratam apenas a integração RAG/IA.

| Referência externa que permanece | Diferença atual | Tratamento nesta entrega |
|---|---|---|
| [Mestre](../prompts/00-prompt-mestre.md), seção de fontes | MRF08–MRF15 ainda são descritos como derivados pendentes | Atualização funcional autorizada está registrada na fonte canônica, AGENTS.md e normalização; aprovação funcional não fecha parâmetros clínicos/técnicos. |
| [FND-01](../prompts/01-fundacao/FND-01-fontes-de-verdade.md) | Metadados listam MRF01–MRF15 e texto antigo de validação | Preservado; leitura de todos os requisitos atuais não deve excluir MRF16–MRF19. |
| [FND-02A](../prompts/01-fundacao/FND-02A-propostas-de-adrs.md) e [FND-02B](../prompts/01-fundacao/FND-02B-aprovacao-dos-gates.md) | Checkpoint enumera MRF08–MRF15 | Registrar a decisão funcional já autorizada e continuar fechando escolhas ainda abertas; não inferir que GATE-04 inteiro está aprovado. |
| [FND-03](../prompts/01-fundacao/FND-03-modelo-logico.md) | Faixa de MRFs nos metadados não inclui os novos | Corpo exige todos os requisitos/arquitetura; a extensão de dados orienta a revisão. Não criar schema físico nesta entrega. |
| [Manifesto](../prompts/README.md), GATE-04 | Faixa antiga MRF08–MRF15 e gate ABERTO | Gate técnico/clínico continua aberto. Grafo e IDs não mudam; plano funcional atual é MRF01–MRF19. |
| [VAL-01](../prompts/10-validacao-final/VAL-01.md) | Metadados ainda enumeram MRF01–MRF15 | Aceite agentivo é detalhado em AI-06/TST-01 e na fonte atual; registro histórico não comprova cobertura nem exclui novos critérios. |

São divergências documentais conhecidas, não compatibilidade textual integral.
Uma revisão futura desses arquivos dependerá de escopo autorizado. Nesta entrega,
as instruções atuais do responsável e as fontes de verdade atualizadas orientam
a execução; não alterar prompts externos nem inventar exceção clínica para harmonizá-los.

## Distribuição de implementação sem ciclos novos

- RAG-01: aprovação/revogação e metadados; RAG-02: porta vetorial; RAG-03/04:
  extração/contexto e indexação; RAG-05: ferramentas de conhecimento sem LLM.
- AI-01: contexto/triagem; AI-02: planejamento, executor, pesquisa, avaliação e
  contrato de estado; AI-03: persistência e geração/publicação integradas.
- AI-04: acompanhamento e revisão posterior; AI-05: mesmo fluxo no chat;
  AI-06: conjunto de testes e comparação com referência fixa; TST-01: E2E do MVP.

RAG-05 não depende de AI-02; AI-02 define porta de estado, AI-03 implementa sua
persistência depois. Não adicionar dependência inversa. FND-03 modela a extensão
pelas fontes de verdade; se já houver modelo na implementação, RAG/IA evoluem
somente suas estruturas por migrations novas.

## Verificações desta atualização

O relatório de revisão documental confere: 19 MRFs, 110 critérios únicos, 75 IDs
anteriores preservados, 25 cenários AR, links locais, rastreabilidade dos 12 cartões,
61 cartões no grafo sem ciclos e mesmos metadados de dependência do manifesto.
Hashes confirmam os 55 arquivos externos, o MER/18 PDFs e os dois artefatos
preexistentes da avaliação documental preservados. RFs, RNs e RNFs não foram alterados.

Essas verificações são documentais. BE/INT/API/DB/RAG/IA/E2E não foram executados
como testes de aplicação: projetos, provedores e serviços ainda não estão
configurados. [AR-01–AR-25](../testes/agentic-rag.md) descrevem os ensaios futuros.

## Pendências antes do aceite real

1. Fechar stack/identidade/tenancy e serviços locais nos gates pertinentes.
2. Em GATE-04, escolher provedores/modelos, confirmar banco vetorial, responsáveis
   pelo corpus/casos, política clínica e valores de orçamento/suficiência/progresso.
3. Produzir modelo lógico e migrations, contratos e controles de revisão
   consistentes na publicação, com isolamento, concorrência e retenção operacional.
4. Revisar casos e executar referência fixa/agentiva com provedor e bancos reais,
   medindo qualidade, abstenção, chamadas, custo e duração. Não assumir ganho por
   adotar o nome Agentic RAG.

Não houve download de materiais, aprovação dos PDFs, implementação de módulos ou
alteração de pagamentos, reconhecimento facial, Docker ou do MER original.
