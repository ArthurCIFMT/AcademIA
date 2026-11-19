# Preparar o RAG para revisão manual

Esta é uma operação do responsável técnico pelo sistema. O administrador da
academia recebe a base preparada e não precisa gerenciar PDFs ou indexação.
Requer PostgreSQL/migrations, identidade administrativa ativa para autoria,
arquivos de materiais/rag e pesos E5 locais verificados. Nenhum LLM é chamado.

## Execução reproduzível

Pare a API antes de abrir o mesmo diretório Qdrant. Preserve um backup local
do PostgreSQL e do armazenamento privado antes de manutenção de um ambiente
já usado. Não apague bancos, uploads ou índices para repetir a preparação.

Em backend/, usando o UUID do administrador técnico:

```powershell
uv run --locked --env-file ../.env python -m scripts.prepare_knowledge --actor UUID_DO_RESPONSAVEL
```

O comando:

1. Valida o [plano local versionado](../../materiais/rag/preparacao-local-v1.json)
   e os hashes/finalidades da seleção técnica já aprovada.
2. Importa os 19 PDFs locais: nove selecionados aprovados e dez em quarentena.
   Não baixa materiais nem reaprova versões revogadas.
3. Extrai somente fontes escolhidas no plano. Nahas usa a política v2 das páginas
   físicas 83, 85, 132 e 133, sem declarar válida a extração integral.
4. Compara os recortes com hashes, páginas e offsets revisados antes de indexar.
5. Indexa por E5 local/Qdrant, com checkpoints e validação de completude.
6. Repete sem duplicar versões/ingestões/vetores. Seleção antiga gerenciada por
   este preparo e retirada do plano fica REVOGADA, com auditoria e vetores
   históricos preservados. Ingestões externas ao preparo não são alteradas.

O plano usa os JSONs de seleção revisados de RAG-05/AI-06 como dados de curadoria,
sem importar código, pessoas, documentos artificiais ou ataques dos testes.
O texto dos PDFs e a origem bibliográfica permanecem inalterados.

## Conteúdo ativo e limites

| Fonte | Finalidades indexadas | Recortes por finalidade |
|---|---|---|
| BR-RBCM-001 | Dúvidas; geração geral | Sete conceitos em cada finalidade; três recortes adicionais na geração |
| BR-NAHAS-001 | Geração geral | Cinco recortes do livro |
| INT-HEALTH-001 | Triagem | Dois recortes contextuais |

São cinco ingestões, 24 fragmentos ativos por finalidade e 17 recortes únicos.
Documentos aprovados sem seleção/indexação completa continuam fora da busca.
As quatro fontes com extração pendente do RAG-03 não são promovidas.
O livro apoia a geração; o catálogo relacional fornece exercícios/equipamentos.
Este preparo não adiciona cobertura para adaptação clínica por condição.
Ausência de evidência pertinente continua exigindo abstenção.

Depois do término bem-sucedido, reinicie a API com um worker e o frontend pelos
guias existentes. A primeira consulta pode levar mais tempo para carregar E5
em CPU; os pesos não são baixados durante uma pergunta.

## Área técnica opcional

Na execução comum, mantenha `ACADEMIA_CORPUS_HTTP_ENABLED=false` no backend e
`VITE_CORPUS_MAINTENANCE_ENABLED=false` no frontend. Não há menu RAG na rotina
administrativa; a API de curadoria responde 404 e não aparece no OpenAPI.
Essas opções não desabilitam recuperação, chat ou geração.

Somente para manutenção, o desenvolvedor pode ativar ambas e reiniciar os
processos. A tela fica em /tecnico/corpus; ainda exige administrador ativo,
origem e CSRF. O endereço administrativo antigo redireciona para a área técnica.
Não é criado um novo cargo nem concedida curadoria automática a instrutores.
Importar pela tela continua sendo distinto de extrair e indexar offline.

## Roteiro de teste manual

1. Abra a conta do cliente pelo convite do Mailpit e entre com sua senha.
2. No assistente, pergunte sobre volume, frequência, intervalo ou cadência.
   Confira a explicação em português e as fontes/páginas oferecidas.
3. Complete o onboarding e confira que dados ausentes/desconhecidos não viram
   respostas saudáveis automaticamente. Caso grave continua bloqueado.
4. Solicite uma ficha uma única vez; confira equipamentos, persistência e parecer
   pendente. A consulta não depende de aceite prévio do instrutor.
5. Em caso de quota/erro, observe a mensagem e evite reenvios repetidos.
   A criação manual pelo instrutor permanece disponível.

O [registro do preparo local](../testes/preparacao-rag-local-20261119.md)
separa busca real, testes controlados e eventual chamada ao provedor.
