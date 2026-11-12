# ADR-007 — Livro em português, escopo de extração e fundamentação

Status: ACEITA
Data: 2026-11-12
Origem: responsável solicitou corrigir idioma e fundamentação e concluir AI-06;
seleção técnica e decisões de implementação já delegadas.

O LLM continua criando fichas/adaptações, com catálogo e inventário do backend.
A avaliação anterior não ativava o livro escolhido e recuperava definições
insuficientes para justificar a dose proposta. Instruir português não basta para
comprovar que o modelo respeitou idioma ou evidências; o ensaio real permanece obrigatório.

## Livro e extração
Adicionar fontTools 4.68.0 (lockfile), dependência utilizada pelo pypdf para
interpretar a codificação CFF/Type1. Não suprimir avisos nem substituir símbolos.
O original integral do livro Nahas foi incorporado ao catálogo com seu hash e
direitos originais. Não atribuir licença Creative Commons.

A política v2 identifica parser e fontTools no fingerprint. selected_pages é
opcional: ausente significa arquivo integral; presente exige números físicos
únicos, ordenados, positivos e dentro dos limites. O livro usa [83,85,132,133],
conferidas visualmente. CONCLUIDA vale somente para esse escopo explícito,
registrado no envelope/fingerprint, nunca para todo o livro.
A extração integral ainda exige revisão da página 8 (sumário ilegível).
Selecionar essa página mantém a pendência; não há exclusão automática de páginas
problemáticas ou autorização para omitir ressalvas de um trecho.
Política v1 continua legível e não aceita seleção de páginas.
Política distinta produz nova identidade de extração; não reutiliza sucesso anterior.
Sem seleção, regras de páginas sem texto/avisos continuam as anteriores.

CLI de indexação recebe --policy explícito para essa fonte; exige versão
bibliográfica aprovada e revalida aprovação, hashes e trechos como antes.
A [seleção operacional](../../../materiais/rag/selecoes/nahas-forca-v1.json)
e a [política](../../../materiais/rag/politica-livro-v2.json) permitem reproduzir.
Não alterar migrations ou o original do MER.

## Recuperação e idioma
Geração realiza duas consultas semânticas predeterminadas: prescrição
(séries/repetições/frequência/objetivo/disponibilidade) e intervalo/recuperação.
Cada busca continua com top-K 5, mínimo 0,8 e filtros de aprovação/saúde.
Contexto do modelo combina até três trechos da primeira e dois da segunda,
deduplicando IDs; vagas podem ser preenchidas com os demais da primeira.
Não é top-K global de uma consulta única nem pesquisa escolhida pelo modelo.
Chat permanece com uma consulta; triagem mantém sua consulta própria.
Adaptação clínica ainda exige escopo/evidências pertinentes; livro geral não as substitui.

Prompt academia-ia-v3 pede português em todo texto novo, títulos simples Dia N,
quantidades sustentadas pelos trechos e explicação consistente com os itens.
Adaptação preserva partes manuais não relacionadas. Não inventar semanas de
experiência, cargas a partir de exemplos, cobertura muscular completa ou uma
recomendação onde a fonte apenas define um conceito.
Catálogo reduzido/tempo devem ser declarados como limitações quando necessário.
O livro traz orientações gerais; o LLM aplica ao contexto sem prometer adequação
universal ou resultados que o trecho não apresenta.

Modelo recebe ID, título, idioma, página/seção e texto completo de cada trecho.
Proveniência completa, hashes, revisão e score permanecem no backend; não são
reenviados desnecessariamente. Consumo e IDs efetivamente enviados são registrados.
Preservar negações, unidades e ressalvas.

## Avaliação
Nenhum limiar, rótulo esperado ou bloqueio foi relaxado.
Permanecem até uma triagem e uma geração LLM, sem retry automático, reparo por
segunda geração, plano pago ou aceite humano atribuído pelo modelo.
Relatórios vinculam política, prompts, consulta, código e dependências; fontes JSON
usam hash canônico para não depender de CRLF/LF. Consolidação exige revisão
semântica vinculada e aprovada, além dos testes técnicos e metas de latência.
Falha dos serviços de IA continua permitindo montagem manual.

A consolidação aplica a fração supported_answers_fraction=0,9 já aprovada na
configuração v2; o código anterior exigia 100% apesar dessa meta. Idioma,
unidades/negações e segurança permanecem exigidos em todos os casos revisados.
Amostra incompleta, revisão sem vínculo ou qualquer falha crítica continuam
impedindo aceite, mesmo com fração suficiente. Não altera o limiar aprovado.

## Apresentação factual da ficha
O ensaio com o livro mostrou que texto explicativo livre ainda podia confundir
séries com sessões mesmo quando os campos do plano estavam corretos.
Após validar o plano e a diferença de adaptação, o backend monta o resumo público
a partir dos campos: dias, itens e cargas ainda não definidas. Os títulos das
gerações novas são Dia N. Adaptação preserva títulos/itens não relacionados.
O texto não atribui eficácia, cobertura completa, validação clínica ou recomendações
numéricas à literatura. Não confundir carga null com carga explicitamente zero.
O LLM continua escolhendo dias, exercícios, séries, repetições, pausas e observações
com o resumo, catálogo e trechos. A explicação livre não é propagada à ficha/API
pública; referências recuperadas/citadas e proveniência continuam registradas.
Os testes auditam o artefato entregue pela aplicação e registram limitações da
saída bruta separadamente. Isso não transforma uma saída bruta incorreta em
resposta aprovada: ela fica fora do conteúdo publicado por contrato verificável.
Chat de dúvidas continua sendo resposta LLM com avaliação de fundamentação.
Não acrescenta chamada LLM, retry ou alteração de critério de saúde.

A mesma correção aplica eligible_valid_plan_fraction=0,8, já aprovada, às
gerações elegíveis. Bloqueios, isolamento, ataques e demais casos obrigatórios
exigem todos os resultados esperados; uma recusa conservadora de caso elegível
fica registrada como falha de capacidade e entra no denominador, sem repetir
até obter resposta favorável. Não muda nem omite o rótulo esperado.

## Escopo da triagem
O prompt v3 distingue lacunas do esquema e relato clínico ambíguo de exigências
externas não previstas. Negativas explícitas são respostas válidas; limitações
do estudo recuperado não tornam todo cliente incompleto. Não exigir exames,
GAQ ou laudo. Texto contraditório com sintomas relevantes ainda deve sinalizar
alerta e atualização. Ausente/NAO_SEI continuam insuficientes no backend.
A mudança não remove decisão determinística nem transforma a triagem em diagnóstico.
