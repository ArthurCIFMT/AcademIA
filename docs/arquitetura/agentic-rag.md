# Arquitetura do Agentic RAG do AcademIA

Especificação autorizada em 2026-11-04. Descreve comportamento futuro, não código
implementado. [MRF01–MRF19](../requisitos/macrorequisitos-ia-rag.md) são a fonte
funcional; provedores, políticas clínicas e parâmetros continuam em GATE-04.

## Divisão de responsabilidades

- MOD-06 contém planejador/pesquisador, avaliador de evidências, máquina de estados,
  executor de ferramentas e agentes de biomecânica/periodização/revisão.
- MOD-05 contém corpus, aprovação, extração, embeddings e ferramentas de busca e
  contexto documental. Recuperação individual não depende de LLM/orquestrador.
- MOD-03 fornece snapshot autorizado do onboarding por contrato; MOD-02/MOD-01
  validam vínculo e autorização. O modelo não escolhe a identidade do cliente.
- MOD-04 fornece exercícios elegíveis e publica versões por contrato; MOD-10 é
  proprietário da disponibilidade. MOD-12 recebe eventos/auditoria minimizados.

Permanece o monólito modular Python, PostgreSQL operacional, banco vetorial
especializado e React/TypeScript. Papéis de agentes podem compartilhar provedor
e processo; não exigem microserviços, um modelo por papel, broker ou novo framework.
Qdrant continua recomendado, sem se tornar decisão de fornecedor nesta mudança.

## O que torna a recuperação agentiva

O LLM escolhe a próxima ação de pesquisa em função da solicitação e dos resultados
das ferramentas. Um script que apenas executa duas buscas fixas não comprova esse
comportamento. A sequência clínica/publicação permanece condicionada por código.

```text
Contexto autorizado -> validação de entrada/triagem
  bloqueado/insuficiente -> resposta controlada, sem nova ficha
  elegível -> planejar -> propor ação -> executor valida -> ferramenta de leitura
                ^                                      |
                |                                      v
                +--- nova pesquisa/replanejamento <- avaliar evidências
                                                          |
                           pedir dados / abster-se / falhar / suporte suficiente
                                                                   |
                      candidatos elegíveis -> biomecânica -> periodização -> revisor
                            ^                                               |
                            +----- lacuna documental dentro do orçamento ---+
                      proposta válida -> revalidações -> publicação por MOD-04
```

O plano operacional enumera perguntas, restrições referenciadas e lacunas; não
contém raciocínio interno. Decompor a pesquisa e escolher ações não permite
diagnosticar, remover bloqueio, aprovar corpus ou declarar aceite profissional.

## Contratos de ações e ferramentas

Contratos externos e mensagens de ferramentas usam JSON versionado; interfaces
internas usam tipos Python equivalentes, sem serialização artificial. AI-02
implementará os JSON Schemas concretos e seus contratos de erro no scaffold aceito.

| Ação proposta pelo LLM | Conteúdo mínimo | Validação pelo backend |
|---|---|---|
| Planejar/replanejar | Questões identificáveis, objetivo, versão do plano, referências das restrições e campos faltantes | Schema, contexto autorizado e invariantes preservadas; não aceitar diagnóstico inventado |
| Chamar ferramenta | Nome/versão, argumentos e questão investigada | Lista de ferramentas permitidas, autorização, schema, limite de tamanho e orçamento |
| Pedir dados | Códigos/campos necessários e mensagem em português | Campos previstos no formulário/política; não solicitar informações arbitrárias ou dados de terceiros |
| Avaliar/encerrar pesquisa | Decisão, evidências por questão, lacunas/conflitos e motivo resumido | Referências retornadas de fato, fonte vigente, cobertura pertinente e estado válido |

| Ferramenta de leitura | Proprietário | Entrada/retorno e limites |
|---|---|---|
| `buscar_evidencias` | MOD-05, via RAG-05 | Consulta minimizada, top-K limitado e filtros opcionais de tema/população. Backend impõe corpus, aprovação, versão e limites; retorna IDs, texto, localização, idioma e score. |
| `ler_contexto_documental` | MOD-05, via RAG-05 | ID de trecho/documento previamente obtido; retorna página/seção ou vizinhança limitada com ressalvas e proveniência. Não aceita caminho/URL livre. |
| `consultar_exercicios_elegiveis` | MOD-04, adaptada em AI-02/03 | Consulta candidatos por contrato de catálogo, já filtrados por restrições e recursos; retorna IDs existentes e requisitos de recursos. Não oferece acesso ao repositório/tabela. |
| `consultar_recursos_disponiveis` | MOD-10, adaptada em AI-02/03 | Consulta o inventário cadastral/operacional permitido e sua revisão; não exige medir ocupação em tempo real nem autoriza escrita. |

Cada chamada retorna `OK`, `VAZIO`, `ARGUMENTO_INVALIDO`, `NAO_AUTORIZADO`,
`INDISPONIVEL` ou erro técnico equivalente definido no contrato. Vazio não é
indisponibilidade. Referências não aprovadas/revogadas não podem ser lidas por
IDs obtidos em chamada anterior. Tool call é proposta do modelo, nunca execução
direta; o executor fecha schemas/argumentos e valida a autorização em cada chamada.

O contexto do cliente vem da requisição autenticada. Não aceitar `client_id`, SQL,
nome de tabela, endereço externo ou instrução documental como ampliação de acesso.
Não oferecer ferramenta de pagamento, biometria, liberação de catraca, edição de
onboarding/inventário, aprovação de fontes ou publicação de treino.

## Evidências e decisões

| Decisão da pesquisa | Efeito |
|---|---|
| Evidência suficiente | Encaminhar pacote validável à geração; ainda exige triagem e regras de domínio |
| Pesquisar mais | Nova ação permitida dentro do orçamento; sem progresso, encerrar de forma controlada |
| Pedir dados | Terminar a tentativa com campos faltantes; resposta do cliente cria entrada revalidada e execução vinculada, sem manter loop aguardando indefinidamente |
| Evidência insuficiente ou conflito não resolvido | Abster-se da adaptação solicitada; preservar ficha vigente e explicar limites |
| Falha técnica, limite ou cancelamento | Estado operacional próprio; não inferir diagnóstico, ausência de doença ou segurança |

Triagem e pesquisa têm estados distintos. Pesquisa suficiente não transforma
`BLOQUEADO_POR_SEGURANCA` em `ELEGIVEL_PARA_GERACAO` nem substitui liberação clínica
prevista em política. Score de cosseno é dado de recuperação, não confiança clínica.

O pacote liga cada afirmação/adaptação às evidências efetivamente obtidas. Avaliar
condição, população, intervenção, força/limites da evidência e eventuais conflitos.
Uma referência válida pode ser inaplicável ao caso; múltiplos trechos do mesmo
estudo não contam como confirmações independentes. Revisor pode solicitar pesquisa
adicional, mas não deve procurar indefinidamente uma fonte que permita ignorar
restrições. Os critérios clínicos e de suficiência devem ser revisados pelo responsável.

## Orçamento, falhas e retomada

AI-02 implementa um orçamento global por execução: chamadas LLM/ferramentas,
tentativas, tokens, ciclos, duração e custo quando mensurável. Valores são
configuráveis, versionados e fechados antes do aceite; esta especificação não
inventa limites de produção. Reservar a capacidade antes da chamada impede N+1,
inclusive em concorrência. Retry conta conforme a operação e não zera o orçamento.

Reinício/retomada técnica da mesma execução mantém consumo e estado. Timeout,
cancelamento e resposta tardia não provocam publicação. Repetição sem progresso
é detectada por ação/consulta/resultados e lacunas, sem exigir raciocínio interno.
Atualização real de dados pode originar execução filha, novamente autorizada;
não usar execuções filhas como retry automático para contornar orçamento.

Chamadas de rede não mantêm transação SQL aberta. Persistir transições curtas com
controle de concorrência; validar versão-base/contexto antes de produzir efeitos.
Não presumir que uma chamada LLM externa foi executada exatamente uma vez quando
houve falha de rede: registrar tentativa e consumo conservador, com retries limitados.

## Publicação e privacidade

Somente o serviço de aplicação do backend pede publicação a MOD-04 após verificar
JSON, IDs, restrições, fontes e contexto atuais. Pacote favorável do avaliador não
dispensa validações; catálogo/inventário e metadados de aprovação são rechecados por
interfaces dos proprietários. Definir no contrato consistência/controle de revisão
na transação final, sem acesso direto às tabelas de outro módulo.

Publicação usa o mecanismo único de versão de TRN-02/03, retém até 15 versões e
começa com parecer PENDENTE. Cliente consulta/chat antes do aceite; rejeição e
expiração seguem RF-17/RF-35. Trilha de execução não é cópia paralela consultável da
prescrição excluída. Memória operacional, cache e ferramentas filtram conteúdo
retirado e fontes revogadas. Não alterar conversas históricas para fabricar contexto.

Planos/consultas podem conter dados de saúde e exigem controle de acesso no
armazenamento operacional. Logs gerais usam códigos, IDs opacos e contadores,
sem onboarding completo, texto clínico desnecessário ou raciocínio interno.

## Sequência mantida dos prompts

RAG-01–04 preparam corpus e índices; RAG-05 entrega ferramentas de conhecimento
sem depender de AI-02. AI-01 entrega contexto/triagem; AI-02 implementa MRF16–19,
executor e controles; AI-03 persiste o fluxo integrado e publica por contrato;
AI-04 apresenta estados ao usuário e comunica revisão; AI-05 usa o mesmo fluxo no
chat; AI-06 avalia, e TST-01 acrescenta cenários agentivos à aceitação do MVP.
Não é necessário adicionar cartões ou modificar dependências externas.

## Verificação e referências

[Modelo de dados proposto](modelo-de-dados/extensao-agentic-rag.md),
[análise de compatibilidade](../analises/2026-11-04-compatibilidade-agentic-rag.md)
e [conjunto de testes](../testes/agentic-rag.md) detalham a implementação futura.
MRF13 mede qualidade e compara referência fixa/agentiva; a decisão de arquitetura
não é evidência de superioridade. p95 <= 2 s é da chamada vetorial, não de todo o
fluxo com múltiplas chamadas. Provedor real e serviços configurados são necessários
para o aceite de execução; esta atualização não os substitui.
