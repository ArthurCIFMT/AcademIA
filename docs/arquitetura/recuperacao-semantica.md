# Recuperação semântica — RAG-05

MOD-05 recupera evidências para dúvidas, triagem e geração. MRF02/MRF11/MRF12/MRF15,
RN-29/RN-39 e RNF-13 governam esta entrega. O serviço não chama LLM, cria ficha
ou decide elegibilidade. O adaptador LLM e a orquestração permanecem AI-01–AI-06.

## Contratos e fronteiras

Request JSON estrito identifica contexto_id, finalidade, consulta minimizada,
top_k (padrão 5, máximo 8) e escopo_saude opcional. O contexto é resolvido pelo
backend autenticado quando integrado ao MOD-06; não expor essa CLI como endpoint
anônimo. Não receber onboarding inteiro ou um cliente escolhido livremente pelo
modelo. A consulta tem até 1000 caracteres e precisa caber em 512 tokens E5 com
query:. A porta QueryEncoder fornece queries; SearchIndex estende a porta vetorial
com search. Objetos internos são tipados, sem serialização JSON artificial.

Os [schemas de entrada/saída](../requisitos/schemas/recuperacao-v1.schema.json)
e de [anotação de escopo](../requisitos/schemas/escopo-evidencia-v1.schema.json)
integram a SPEC. QdrantStore implementa search com tipos SDK privados. A extensão
em vector/ e o ajuste do tipo do singleton são necessários à porta prevista pelo
cartão; não existe rota REST ou migration nova. Tabelas de 0012/0013 são reutilizadas.
Arquivos __init__ dos testes permitem reutilizar fixtures sem duplicar módulos no mypy.

## Filtros, proveniência e entrega

1. Conferir coleção/revisão/espaço; consultar no PG somente ingestões CONCLUIDA de
   literatura APROVADO na revisão atual. Sem ingestão, não chamar embeddings.
2. Gerar vetor query: normalizado, 384 dimensões, com o E5 fixado; modelo/coleção
   diferentes não são misturados. Sem busca livre na internet ou tradução do corpus.
3. Buscar por cosseno até 40 candidatos, com filtros Qdrant obrigatórios de ingestão,
   finalidade e fingerprint. Os IDs permitidos vêm do backend, não da pergunta.
4. Reconsultar aprovação no PG depois da busca; revalidar fragmento/checkpoint,
   versão, revisão, configuração, hash, metadados e coordenadas. A finalidade
   também precisa constar dos metadados aprovados e da seleção imutável do PG,
   mesmo se o payload for adulterado com checksum recalculado. Payload e checksum
   incompatíveis geram falha técnica; não entregar fonte possivelmente adulterada.
5. Aplicar limiar inicial 0,80, ordenar por score e ID para desempate, deduplicar por
   versão/hash e retornar até top_k. Evidências são candidatas: similaridade não é
   probabilidade clínica nem prova de que uma prescrição tem suporte.

Cada evidência identifica fragmento/ingestão/versão e aprovação, título, URL real,
idioma documental, página PDF ou linhas TXT, seção, texto/hash e score. Não inventar
página ou URL. Em publicações multilíngues, a seção pode indicar Abstract (en) mesmo
quando o idioma predominante do documento é pt-BR; esse é o caso do ensaio atual.
Trechos que contêm instruções continuam dados: não podem mudar identidade,
permissão ou fluxo. SC-05 exercita a porta real sem chave/provedor LLM configurado.

## Saúde: pertinência e conflito

Escopo_saude possui condição, população e intervenção estruturadas. Suporte só é
classificado PERTINENTE quando uma Annotation técnica do backend liga exatamente
esse escopo ao SHA-256 do arquivo e do texto recuperado, com posição SUPORTE.
A anotação é configuração de curadoria confiável e versionada; nunca aceitá-la do
cliente/LLM como declaração de autorização. O ensaio de domínio usa rótulos
sintéticos explícitos, sem declarar adequação clínica real.

Sem anotação pertinente ou apenas com contraindicação, retornar insuficiência;
com suporte e contraindicação conflitantes, retornar CONFLITO e os trechos para
análise, impedindo tratar o resultado como suporte de adaptação. Não inferir
pertinência apenas por ocorrência de palavra ou score alto. Anotação de outra
versão/hash não vale. Esta entrega não cria uma taxonomia clínica universal nem
aprovação médica. Políticas de triagem, dados insuficientes, caso grave e publicação
continuam nos módulos responsáveis. PERTINENTE identifica relação curada da evidência,
não aptidão do cliente nem validação universal da dose.

A CLI técnica não fornece anotações de saúde e se abstém desses pedidos sem
suporte configurado. Um chamador que omitir escopo recebe candidatos gerais,
com suporte_saude=NAO_SOLICITADO; não pode usar esse estado para afirmar adaptação
por condição. AI-01/AI-03 devem exigir os contratos e bloqueios de saúde previstos.

## Estados e falhas

| Estado | Significado |
|---|---|
| EVIDENCIAS_ENCONTRADAS | Trechos candidatos dentro dos filtros; suporte de saúde é campo separado |
| SEM_EVIDENCIAS | Sem ingestão aprovada ou sem resultado vigente para a finalidade |
| EVIDENCIA_INSUFICIENTE | Score abaixo do limiar ou falta de suporte curado para o escopo |
| CONFLITO | Evidências de posições divergentes para o mesmo escopo |
| SERVICO_INDISPONIVEL | Falha de SQL, embeddings/Qdrant, proveniência inválida, espaço incompatível ou orçamento excedido |

Falha não vira ausência de evidência, diagnóstico ou elegibilidade. Há uma tentativa
por operação de busca nesta implementação (abaixo do teto de três de transporte),
sem fallback ou reparo LLM. Orçamento padrão 60 s; retorno depois do orçamento é
recusado. Isso não é uma promessa de que toda operação bloqueante termina em 60 s.
Embeddings têm encerramento de worker conforme RAG-04. PG usa transações curtas,
sem segurar conexão enquanto roda o modelo ou Qdrant. Falha não impede ficha manual.

## Cache e minimização

Cache local guarda apenas vetores de consulta por até 300 s, máximo 128 entradas,
com lock. Chave combina contexto autorizado, finalidade, espaço e hash da pergunta;
não guarda texto de pergunta, onboarding, conversa ou resposta. Contextos diferentes
não reutilizam a entrada. Não há cache de fontes nem de aprovação: toda consulta,
mesmo com vetor em cache, repete filtros e revalidação PG. Reiniciar/clear_cache
remove o cache. Revogação prevalece enquanto vetores físicos continuam no Qdrant.
Não registrar a consulta ou dados privados em logs; resultado informa motivo,
busca_ms e total_ms para instrumentação pelo orquestrador.

## Execução local e avaliação

Com a API parada e .env configurado, em backend/:

~~~powershell
uv run --locked --env-file ../.env python -m app.modules.knowledge.retrieval --request CAMINHO_JSON
~~~

O arquivo segue Request. É manutenção local com as credenciais do operador, não
uma interface pública. Não concorrer com a API pelo mesmo diretório Qdrant. Não
imprimir perguntas em logs. Uma coleção vazia retorna SEM_EVIDENCIAS, sem simulação.

O [conjunto rotulado](../testes/rag05-consultas-v1.json) fixa antes do ensaio
24 perguntas positivas (18 PT e seis que buscam o resumo original EN) e quatro
fora de escopo. São sete trechos integrais selecionados de BR-RBCM-001, com página,
offsets e hash. Os outros PDFs e seus estados não foram promovidos pelo ensaio.
Metas prévias: recall@5 e recall por idioma >=0,80; abstenção fora de escopo=1;
p95 da busca <=2 s. [Relatório real](../testes/rag05-avaliacao.json) registra
numeradores por casos, modelo, ambiente, volume, inicialização e tempos.

Amostra pequena e concentrada em uma publicação introdutória: não comprova
cobertura do corpus amplo, qualidade de fichas, suporte clínico ou tempo do LLM.
E5 é aquecido antes das consultas e a carga inicial é informada separadamente;
a primeira requisição de um processo sem aquecimento pode demorar mais.
A medição usa perf_counter de alta resolução, importante no Windows. Testes
sintéticos verificam segurança/estados, não são literatura validada.
Comandos reproduzíveis e resultados estão no [registro](../testes/comandos.md#recuperação-semântica-e-avaliação-rag).

## Livro de apoio e pendências

Por delegação do responsável, a referência inicial em português é o livro de
Markus V. Nahas, Atividade Física, Saúde e Qualidade de Vida, 7ª ed. (2017).
[Referência/hash e pendências](../../materiais/rag/livro-de-apoio.json) registram
capítulos 4 e 6, fonte oficial gratuita e limites. O livro apoia conceitos e
planejamento geral, sem substituir catálogo/equipamentos ou literatura pertinente
à saúde. Avisos de fontes na extração impedem ativá-lo automaticamente. Sua escolha
não altera os sete documentos selecionados ou a evidência do ensaio.
Os quatro PDFs pendentes do RAG-03 seguem fora da recuperação ativa; o responsável
aceitou tratar essas revisões após o MVP, condicionado à cobertura do aceite.
