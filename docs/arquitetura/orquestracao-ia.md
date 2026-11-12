# Orquestração fixa da IA — AI-02

## Entrega e fronteira

MOD-06 fornece schemas JSON/Pydantic, prompts internos academia-ia-v1, orquestrador,
adaptador HTTP Groq e pontes para a triagem, catálogo e recuperação existentes.
[Contrato JSON](../requisitos/schemas/execucao-ia-v1.schema.json),
[configuração](../requisitos/configuracao-ia-rag.md) e
[triagem](triagem-academica.md) integram esta entrega.

AI-02 não publica fichas, não cria migrations e não ativa uma rota pública de
execução com estado volátil. O construtor Orchestrator exige explicitamente quatro
portas: ContextPort, EvidencePort, LLMPort e StatePort. Não há store de produção
em memória. [AI-03 implementa](geracao-persistente.md) estado/consumo durável, recuperação segura de
execuções interrompidas e publicação pelo serviço de MOD-04. AI-04/AI-05 entregarão
as interfaces de geração e chat/adaptação. A rota GET de preparação permanece
somente leitura, sem chamar LLM ou gastar cota.

## Fluxo determinístico

| Finalidade | Sequência | Chamadas físicas LLM máximas |
|---|---|---|
| DUVIDA | contexto próprio → busca DUVIDAS → resposta → validação | 1 CHAT |
| GERACAO | preparação → busca TRIAGEM → análise → busca GERACAO_GERAL → geração → validação | 1 TRIAGEM + 1 GERACAO |
| ADAPTACAO | mesma sequência da geração, com versão-base autorizada e pedido explícito | 1 TRIAGEM + 1 GERACAO |

Bloqueio determinístico ou dados insuficientes terminam antes de buscar/chamar o
modelo. Casos desconhecidos não se tornam saudáveis por ausência de dados. O
analista LLM pode acrescentar alerta/lacuna; nunca remover a regra acadêmica.
Relato novo relevante sinaliza atualização confirmada do onboarding, sem alterar
cadastro pelo chat. Adaptação exige leitor autorizado da versão-base; sem ele,
encerra por insuficiência. A integração/publicação de adaptações fica em AI-05.

A ponte PostgresContext usa serviços públicos de autorização, triagem e catálogo,
com sessões curtas. Papéis vigentes e designação são conferidos; instrutor
designado pode preparar geração, mas não ler o chat privado do cliente. O resumo
e os candidatos vêm do backend, não de IDs ou sinais fornecidos pelo usuário.
Antes/depois de cada etapa, revalidar permissão, snapshot, regras e recursos.
Mudança relevante interrompe a execução e exige nova solicitação.

RagEvidence chama Retriever de RAG-05, separando as finalidades. Revalida ingestões
concluídas, espaço vetorial e versão/revisão documental ainda aprovada por serviços
públicos de MOD-05. Cache não dispensa revalidação. Para condição de saúde declarada,
exigir escopo condição/população/intervenção resolvido pelo backend para o conjunto
completo de restrições (não selecionar somente uma condição favorável) e suporte
PERTINENTE de RAG-05; sem mapeamento/evidência ou com conflito, abster-se.
Similaridade alta isolada não prova suporte. Não há planner, navegação, ferramentas
escolhidas pelo modelo, revisor LLM ou busca iterativa.

## Prompts e validação

Prompts em app/modules/ai/prompts/v1.py separam instruções de sistema e um objeto
dados_nao_confiaveis contendo pergunta, histórico limitado, resumo minimizado,
candidatos e trechos aprovados. Não enviar IDs de cliente/snapshot, livros inteiros,
anamnese fora do resumo ou chats de terceiros. Não registrar corpo, chave ou
raciocínio interno nos logs. Hashes, versões e consumo são metadados de execução;
conteúdo interno deve ficar sob autorização/retenção de AI-03, não log técnico.

Cada chamada recebe JSON Schema específico. JSON Object Mode do provedor não
garante schema: backend rejeita JSON malformado, chaves repetidas, NaN/Infinity,
campos extras, idioma declarado diferente de pt-BR, tipos e faixas inválidas.
Não há remoção de cercas de Markdown, reparo ou segunda chamada para corrigir.
Ficha tem 1–6 dias, até seis itens/dia, ordem sequencial, IDs reais, combinação
completa de equipamentos disponível, séries/repetições/carga/intervalos validados.
Fontes citadas devem estar no pacote recuperado. Recurso ausente, exercício
proibido/inexistente ou evidência inventada impedem resultado pronto.

RESPOSTA_PRONTA é resposta de dúvida; PRONTA_PARA_PUBLICACAO é proposta interna
validada, não ficha publicada nem aceite profissional. Somente AI-03/MOD-04
publicará com parecer PENDENTE, independente do aceite posterior do instrutor.
Nenhum schema permite SQL, ferramentas, autor administrativo ou parecer humano.
FALHA, JSON_INVALIDO, SCHEMA_INVALIDO, TIMEOUT, CANCELADA, INTERROMPIDA,
DADOS_INSUFICIENTES, BLOQUEADA, ABSTENCAO e CONFLITO são resultados distintos.

## Orçamentos e contrato de StatePort

Valores vêm da configuração vigente (v2, ADR-006): prompt até 24000 bytes UTF-8, resumo até 2400
caracteres, até 40 candidatos e cinco trechos por pacote; pergunta até 1000
caracteres, seis mensagens de histórico/3000 caracteres. Excesso termina sem
truncamento silencioso. Tokens de saída: CHAT 600, TRIAGEM 400 e GERACAO 4096;
respectivamente 20/25/60 segundos, execução até 100 segundos. Bytes não são tokens.
Reservas de saída não comprovam consumo real: registrar usage do provedor quando
disponível; em falha/consumo desconhecido, manter reserva e indicação explícita.
Não há preço presumido ou contratação automática de plano.

StatePort deve garantir atomicamente:
- claim exclusivo por ator/solicitação, vinculando titular, finalidade, entrada,
  snapshot/contexto e versões de configuração/prompts;
- mesma chave/entrada retorna execução em andamento ou resultado, sem retomar
  chamadas; entrada/contexto diferente gera ExecutionConflict;
- reserva única por etapa antes do envio e marca de despacho imediatamente antes
  de cada requisição HTTP física, inclusive 429, erro de rede ou JSON inválido;
- consumo recebido após cancelamento pode ser contabilizado, mas nunca reativar
  execução, liberar resposta ou publicar;
- finish/cancel terminais preservam orçamento; nova tentativa explícita usa novo ID;
- cotas persistentes/atômicas de novas execuções por cliente antes de embeddings/
  busca/LLM, conforme janela aprovada de seis em 60 segundos para chat/adaptação;
- não reiniciar execução/orçamento após queda. O deadline monotônico recebido vale
  no processo atual; AI-03 deve convertê-lo em prazo durável UTC e tratar execuções
  órfãs como interrompidas, nunca repetir chamadas automaticamente.

A implementação MemoryState existe somente em tests/ai/execution_fakes.py para
testar esse protocolo; não fornece persistência, cota pública ou recuperação após
reinício. A API foi ativada pelo adaptador durável de AI-03. Retenção de
90 dias e publicação/limite de 15 fichas não foram antecipados nesta etapa.

## Provedor e falhas

GroqAdapter usa HTTPX síncrono, um slot global por processo, redirects/proxy de
ambiente desativados, timeout e tamanho máximo de resposta. Usa o endpoint aprovado,
modelo vigente openai/gpt-oss-120b (ADR-006), json_object, n=1 e
max_completion_tokens. Uma
tentativa por etapa, sem retry/fallback oculto. HTTP 429 encerra; nova ação explícita
pode abrir outra execução. O tempo em fila consome o orçamento da etapa.
Cancelamento impede despacho ainda pendente e descarta resposta em voo; não promete
interromper instantaneamente um POST síncrono já enviado nem desfazer seu consumo.

GROQ_API_KEY vem do ambiente e é mascarada. Sem chave, falha controlada sem POST.
HTTPX já existia nos testes; foi promovido a dependência de runtime no lockfile,
sem novo SDK, para executar o contrato HTTP. Não há nova versão de dependência.

Referências oficiais consultadas:
[API de chat](https://console.groq.com/docs/api-reference),
[JSON Object Mode](https://console.groq.com/docs/structured-outputs),
[erros](https://console.groq.com/docs/errors) e
[limites](https://console.groq.com/docs/rate-limits).

## Verificação e limites da evidência

[Comandos e resultados](../testes/comandos.md#orquestrador-e-contratos-ai-02).
Testes controlam o texto do modelo; integração usa PostgreSQL/Qdrant reais.
HTTPX MockTransport valida o contrato do adaptador sem enviar dados/credenciais
à Groq. Harness REST de schemas não é rota do produto. Casos de injeção verificam
separação de dados, permissões e campos rejeitados; não provam imunidade semântica.
Qualidade de português, suporte dos textos gerados, resistência semântica,
latência/cota gratuita real e corpus completo serão medidos em AI-06.

Em AI-06, a [ADR-007](decisoes/ADR-007-livro-e-fundamentacao.md) acrescentou
duas consultas fixas de geração (prescrição/descanso), reunindo até cinco trechos.
O prompt academia-ia-v3 exige idioma em todo texto novo e fundamentação explícita;
o modelo recebe texto completo e referências mínimas, com proveniência integral
preservada no backend. Não há nova chamada LLM, planner ou loop de reparo.

A triagem explicita lacunas do esquema sem exigir exames fora do escopo.
Depois de validar a proposta e o diff, a apresentação pública conta dias/itens e
cargas pendentes a partir dos campos; a explicação livre não é publicada.
Os itens continuam gerados pelo LLM e recebem validação do domínio.

## Reserva explicitamente selecionada

A [ADR-008](decisoes/ADR-008-reserva-llm-explicita.md) permite o perfil candidato
reserva-groq20b com a mesma porta/adaptador, endpoint validado e limites. Principal
continua sendo GPT-OSS 120B. A escolha é de ambiente confiável antes da execução;
HTTP 429 nunca muda o perfil ou repete uma etapa. Configuração/modelo ficam no
fingerprint e na evidência; ensaios de modelos diferentes não podem ser unidos.
Estado da qualificação em [avaliação de reserva](../testes/ai06-reserva.md).
