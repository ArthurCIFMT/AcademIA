# Extração documental — RAG-03

MOD-05 extrai PDF e TXT offline, com origem e qualidade explícitas.
Atende a etapa de extração de MRF01, MRF11 e MRF15; indexação/embeddings e
recuperação são RAG-04/05. Não chama LLM, não implementa OCR nem altera originais.

## Contrato e uso interno

Extractor.extract recebe ApprovedReference da [curadoria](corpus.md), uma função
obrigatória approval_check(version_id, revision) e retry_failed opcional.
A função de aprovação deve consultar is_approved em transação curta e atual;
não manter uma transação PostgreSQL aberta enquanto o PDF é processado.

O resultado tipado ExtractionResult contém UUID estável, versão documental,
revisão da aprovação, hash do arquivo original, formato, snapshot bibliográfico,
política/fingerprint, horário UTC, tentativa e resultado com páginas e motivos.
Metadados bibliográficos preservam título, URL real, licença, autores, idioma,
finalidades e limites aprovados. Não inferir autor, seção ou saúde de cliente.

Cada Page guarda texto e SHA-256 textual, número físico PDF começando em 1,
situação e seções disponíveis. Marcadores reais do PDF são associados à página
de destino; seção declarada é identificada como tal, sem afirmar inferência.
Não inventar capítulos de páginas sem marcador. TXT não recebe página fictícia:
registra linhas 1..N e cabeçalhos Markdown com a linha de origem.

Aprovação é conferida antes do trabalho e novamente antes de gravar/entregar,
inclusive no replay. Versão pendente, revogada ou TESTE não passa pela checagem
is_approved de literatura. Se for revogada durante o processamento, o resultado
não é entregue nem gravado como nova extração válida. Os artefatos anteriores
permanecem históricos e não contornam a consulta fresca da aprovação.

## Parsing e preservação

Dependência de execução: pypdf 7.0.1, travada no lockfile. PDF usa modo layout,
incluindo texto girado. Preserva negações, >=, <=, ≥, ≤, %, unidades, acentos,
linhas e espaçamentos extraídos. Não aplica remoção genérica de caracteres,
tradução, reescrita por IA, junção silenciosa de colunas ou exclusão de rodapés.
TXT exige UTF-8; só remove o BOM de transporte, preservando as quebras originais.

A extração mecânica não garante ordem semântica perfeita de tabelas/colunas.
Avisos de texto/layout ou caracteres ilegíveis tornam o documento pendente de
revisão. O único aviso tolerado explicitamente é a correção de numeração da
tabela XREF pelo pypdf: fica contabilizado como aviso estrutural, não é apagado.
Nenhuma alteração dessa correção em memória é salva no PDF original.
Outros avisos permanecem bloqueantes e seus conteúdos brutos não vão a logs.

Fontes técnicas: [extração pypdf](https://pypdf.readthedocs.io/en/7.0.1/user/extract-text.html),
[limites de parsing](https://pypdf.readthedocs.io/en/7.0.1/modules/configuration.html)
e [distribuição travada](https://pypi.org/project/pypdf/7.0.1/).

## Estados e falhas

| Estado | Significado e consequência |
|---|---|
| CONCLUIDA | Existe texto, páginas coerentes e nenhuma pendência de extração; ainda requer curadoria de trechos/indexação e autorização vigente |
| OCR_NECESSARIO | Uma página contém imagem e não tem camada textual; documento misto também fica pendente |
| REVISAO_NECESSARIA | Texto/grafismos não classificados, caracteres ilegíveis ou aviso de extração/layout; não usar como extração completa |
| FALHA | Arquivo ausente/alterado, tipo/tamanho/UTF-8 inválido, PDF corrompido/protegido, vazio, limite ou timeout; motivo persistido |

Página realmente vazia é preservada como EM_BRANCO, sem deslocar as seguintes.
Página sem texto com grafismos não é presumida vazia. PDF totalmente sem conteúdo
textual útil não é CONCLUIDA. PDF protegido é recusado sem tentar senhas.
OCR não foi previsto no corpus aceito e não foi instalado; escaneados não recebem
texto inventado. Fonte estrangeira mantém o original para a recuperação multilíngue.

Motivos são códigos estáveis em português; mensagens/avisos brutos do parser,
bytes e caminhos privados não são registrados em logs técnicos. O resultado
privado guarda somente a literatura que foi autorizada para esta etapa.
Armazenamento inacessível, lock ocupado ou artefato inconsistente geram
ExtractionError explícito, sem fingir que um registro foi persistido.

## Limites e processo isolado

A política inicial tem versão 1, identifica pypdf/7.0.1 e participa do fingerprint:
25 MiB por arquivo (limite comum do corpus), 1000 páginas, 100 mil caracteres por
página PDF, 8 milhões por documento e 16 MiB por stream. Decodificação acumulada
é limitada a quatro vezes esse tamanho. A árvore do PDF tem tetos próprios para
nós e campos, distintos da contagem de páginas; a contagem física também é validada.
Alterar algoritmo/parser ou limites exige versionar a política/configuração.

O processo pai usa um subprocesso Python com timeout de 60 segundos por arquivo,
encerrado pelo mecanismo de subprocess.run em caso de timeout. Comunicação por
JSON UTF-8/base64; o worker não lê caminhos fornecidos pelo usuário nem busca URLs.
A saída é validada por Pydantic, com limite de 64 MiB. Limites atingidos não truncam
o conteúdo para declarar sucesso. Não há retry automático nem propagação da
exceção bruta do subprocesso. Esses controles não são uma promessa de isolamento
comercial completo de memória/CPU para qualquer PDF malicioso.

## Persistência e idempotência

ACADEMIA_EXTRACTION_DIR define armazenamento privado (padrão data/extracoes,
relativo ao processo, em backend/ no guia de execução). Padrões ficam fora do Git;
configure caminho absoluto se a inicialização variar. Não confundir esses
artefatos derivados com o banco vetorial ou a tabela de ingestão futura.

UUIDv5 combina versão documental, SHA do original e fingerprint da política.
Cada ID possui um JSON com envelope/hash, resultado e até três tentativas.
Escrita atômica por temporário/substituição e lock exclusivo por ID impedem
extrações duplicadas em chamadas concorrentes. portalocker 4.4.2 é dependência
direta porque o extrator usa o lock entre processos; a versão já vinha no Qdrant.
A instalação acrescenta somente pypdf; versões existentes não foram atualizadas.

Replay válido devolve o resultado persistido sem chamar parser. OCR/revisão e
falhas também são registrados. retry_failed=true permite ação explícita para
FALHA, até três tentativas por ID, preservando resumos de estado/motivo/horário
anteriores. Sucesso, OCR e revisão não são reprocessados implicitamente.
Nova versão documental ou configuração tem identidade própria. Recuperar um
artefato exige conferir envelope e identidade/proveniência; corrupção gera erro,
sem reprocessamento silencioso. Esses hashes detectam inconsistência e não
substituem as permissões do diretório privado.

Não há nova migration, tabela, tela ou API REST neste cartão. A tabela relacional
INGESTAO e fragmentos pertencem a RAG-04; artefatos de extração são derivados locais
versionados por configuração, prontos para ser consumidos pela etapa seguinte.
A extração não abre Qdrant e falhas não interferem no treino manual.

## Ensaio real e pendências identificadas

Foram processados os sete documentos selecionados em corpus-inicial.json,
conferindo SHA-256 e páginas físicas. Os 11 documentos de reserva permaneceram
fora da extração de ingestão. [Relatório JSON](../testes/extracao-corpus-rag03.json)
registra contagens e estados, sem textos integrais ou vetores.

| Documento | Resultado observado | Pendência técnica |
|---|---|---|
| BR-RBAFS-001 | CONCLUIDA, 11 páginas | Apenas aviso estrutural XREF contabilizado |
| BR-RBCM-001 | CONCLUIDA, 36 páginas | Nenhuma pendência automática de extração |
| BR-SBC-002 | CONCLUIDA, 45 páginas | Apenas aviso estrutural XREF contabilizado |
| BR-MS-001 | REVISAO_NECESSARIA, 52 páginas | Página 52 sem camada textual; renderização confirmou contracapa institucional com grafismos/texto visual |
| INT-BJSM-001 | REVISAO_NECESSARIA, 12 páginas | Aviso de layout ao incluir texto girado |
| INT-SPMED-001 | REVISAO_NECESSARIA, 17 páginas | Aviso de layout ao incluir texto girado |
| BR-SBC-001 | REVISAO_NECESSARIA, 154 páginas | Avisos de layout ao incluir texto girado |

Os quatro documentos pendentes não devem entrar como extração pronta no RAG-04
até revisão técnica/tratamento explícito de páginas/layout. Revisão é do projeto,
sem novo gate médico/jurídico. Não alterar originais, desabilitar avisos ou aceitar
resultado parcial só para ativar todas as fontes. RAG-04 pode avançar nas partes
independentes e nas fontes com extração concluída, respeitando o escopo aprovado.

As [fixtures sintéticas](../../backend/tests/knowledge/fixtures/README.md) foram
renderizadas/conferidas e mantêm expectativas explícitas de texto e símbolos.
Os [comandos](../testes/comandos.md#extração-pdf-e-txt) cobrem parser, subprocesso,
cache, concorrência, hashes e aprovação/revogação reais em PostgreSQL.

As fixtures PDF são declaradas binárias em .gitattributes; isso preserva os bytes
e offsets no Git, inclusive nas amostras ASCII. A verificação de diff continua
valendo para código e documentação, e hashes dos PDFs são conferidos na entrega.
