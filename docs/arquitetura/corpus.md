# Corpus documental — RAG-01

MOD-05 mantém literatura e proveniência para o RAG semântico. Esta entrega
implementa curadoria, arquivos e versões; busca, extração, fragmentos e vetores
pertencem a RAG-02–RAG-05. Requisitos: MRF01, MRF11 e MRF15; RN-23 e RN-28.

## Responsável e acesso

O papel ADMINISTRADOR é o curador autorizado inicial, pela política
MANAGE_CORPUS. Instrutor, atendente e cliente não recebem essa permissão
implicitamente. É uma seleção técnica do trabalho acadêmico, sem aprovação
médica ou jurídica externa. A tela fica em **Administração → Gerenciar corpus RAG**.
Todas as rotas exigem sessão; escritas exigem CSRF e origem válida. Arquivos
baixados mantêm essas permissões; respostas privadas usam no-store.

## Registro e versionamento

Um documento agrupa edições por ambiente + identificador de catálogo.
Cada versão tem UUID, número sequencial, SHA-256 dos bytes, formato, tamanho,
idioma, snapshot bibliográfico, criador/data e revisão concorrente.
Metadados incluem título, URL HTTP(S) da fonte, licença, autores (até 100), ano,
finalidades, limites e página/seção declaradas. Título, licença, limites, seção
e cada autor admitem até 500 caracteres. Informações não fornecidas permanecem ausentes.

Os ambientes LITERATURA e TESTE são separados por constraints. Mesmo aprovada,
uma versão TESTE nunca integra as referências de literatura de produção.
O cadastro exige confirmação de que o arquivo é literatura sem dados privados;
não oferece upload de anamneses, biometria ou inventário como literatura.
Essa declaração e a curadoria não são um detector automático de dados pessoais.

Reenvio do mesmo hash no mesmo ambiente retorna a versão original, inclusive
se revogada; não altera seus metadados, nem cria outra aprovação. Conteúdo
alterado com o mesmo identificador cria a próxima edição em quarentena.
Para corrigir metadados sem novos bytes, é necessário um refinamento posterior
com histórico próprio; esta etapa não reescreve referências já registradas.

Transições: PENDENTE → APROVADO → REVOGADO. A versão nasce em quarentena;
aprovar confere novamente a integridade do arquivo e identifica responsável/data.
Revogar exige motivo, autor e data; é terminal para aquela versão. A nova edição
não revoga silenciosamente a anterior. Edições aprovadas podem coexistir e a
curadoria revoga as que não devam continuar em uso.

A revisão impede sobrescrita concorrente (409). Repetição da mesma decisão,
com revisão de origem e mesmo autor/motivo, devolve o resultado sem nova auditoria.
Locks transacionais por hash/documento e constraints impedem duplicação e números
repetidos em conexões independentes. A migration 0012 protege conteúdo,
proveniência, aprovação anterior e histórico contra UPDATE/DELETE indevidos.

## Contratos REST e JSON

Prefixo: /api/v1/corpus; DTOs estritos e OpenAPI gerados pelo backend.

| Método/caminho relativo | Comportamento |
|---|---|
| GET / | Histórico paginado (pagina/limite, até 100), filtro opcional ambiente |
| POST / | Registro JSON: catalogo_id, ambiente, formato, metadados, arquivo_base64 e conteudo_literatura_confirmado=true; retorna versão, 201 inclusive replay |
| POST /importacao-inicial | Confere o acervo local versionado e sua seleção; retorna quantidades, sem baixar conteúdo externo |
| GET /{id} | Snapshot e decisões da versão, sem caminho físico do arquivo |
| POST /{id}/decisao | revisao, estado APROVADO/REVOGADO, motivo obrigatório na revogação |
| GET /{id}/arquivo | Cópia íntegra para curador autenticado, como attachment/nosniff; inclui versões revogadas para histórico |

Erros usam o envelope comum: 401/403 por acesso, 404 por versão inexistente,
409 por conflito/arquivo ausente ou alterado/importação inconsistente,
413 por corpo excessivo, 422 por JSON/campos/formato inválidos. Não retornar
bytes, caminhos privados ou formulário completo em mensagens de validação.

## Arquivos e importação inicial

Configuração: ACADEMIA_CORPUS_DIR (padrão data/corpus relativo ao processo;
no guia de execução a partir de backend, equivale a backend/data/corpus).
Configure caminho absoluto para manter o mesmo armazenamento ao mudar de diretório.
Arquivos e suas cópias de segurança ficam fora do Git. O banco guarda referências
internas por hash; o nome original recebido não determina o caminho salvo.
A escrita usa temporário + criação exclusiva atômica e confere hash em repetição.
Leituras/aprovação conferem o hash; referências não aceitam travessia de diretório.
Falha de transação pode deixar blob sem registro, nunca versão parcialmente publicada;
limpeza desses órfãos não é automática nesta entrega.

Limite: 25 MiB por arquivo, PDF ou TXT UTF-8 não vazio. JSON transporta bytes em
base64 estrito, sem alterar o original. O limite do corpo inclui base64 e metadados.
PDF é conferido pela assinatura inicial; validação de extração/OCR é RAG-03.
Páginas/seções declaradas não são páginas extraídas e não simulam citações prontas.
A URL é apenas metadado: o servidor não busca o endereço informado no cadastro.

A importação lê materiais/rag/catalogo.json e corpus-inicial.json na raiz do
projeto (opcional ACADEMIA_RAG_MATERIALS_DIR). Aceita somente os arquivos locais
em documentos/, verifica os hashes de ambos os manifests e prepara todo o lote
antes de registrar no banco. Mantém os 19 documentos: a seleção técnica existente
de nove documentos é aprovada com o curador que acionou a importação; os outros
10 permanecem em quarentena. Falta/alteração de arquivo aborta o lote relacional.
Não baixa PDFs, inventa fontes ou acrescenta nova seleção. Replay é idempotente
e não reaprova versões revogadas. O cadastro não extrai nem indexa esses PDFs.

## Integração e invalidação

A porta tipada approved_references fornece somente versões LITERATURA/APROVADO
com revisão, hash e metadados. is_approved consulta o estado atual no PostgreSQL
para cada novo uso, inclusive cache. Revogação aumenta a revisão e retorna falso
para a referência antiga sem apagar o arquivo ou fontes históricas.

Os consumidores RAG-04/RAG-05 devem usar essa porta e exigir também extração/indexação completa,
validando antes de entregar trechos. Um vetor ainda existente no Qdrant não torna
a versão autorizada. Nesta etapa não existe busca/cache ativo para invalidar.
Não há LLM, embeddings, contexto de cliente ou acesso direto a outro módulo.
Auditoria usa a interface pública MOD-12, com eventos corpus.registered,
corpus.approved e corpus.revoked, sem copiar o documento em logs.

## Verificação e alcance

Testes do módulo cobrem contratos, autorização/CSRF, quarentena, hash, versões,
aprovação/revogação/replay, isolamento TESTE, concorrência, migration ida/volta,
proteção de histórico, arquivo corrompido e importação dos PDFs reais.
Consulte os [comandos](../testes/comandos.md#corpus-documental).
A tela integra os pontos de composição existentes de rotas, navegação e políticas;
essas alterações equivalentes são necessárias ao escopo funcional do cartão.
Nenhuma dependência nova foi adicionada. A qualidade de extração, busca e respostas
permanece nos cartões posteriores, incluindo o ensaio real de AI-06.
