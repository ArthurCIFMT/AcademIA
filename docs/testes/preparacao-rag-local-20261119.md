# Preparo do RAG local — 2026-11-19

Escopo: permitir revisão manual com corpus real em desenvolvimento e retirar
curadoria da rotina administrativa. Fontes e operação estão no
[guia reproduzível](../instalacao/preparar-rag-local.md).
Não altera tabelas, migrations, regras de saúde, geração, cotas ou provedores.

## Corpus e evidências

| Item | Resultado |
|---|---|
| Registro bibliográfico | 19 documentos; nove aprovados e dez em quarentena |
| Fontes efetivamente ativas | BR-RBCM-001, BR-NAHAS-001 e INT-HEALTH-001 |
| Seleções ativas | Cinco ingestões completas; 24 fragmentos por finalidade, 17 recortes únicos |
| Livro | Páginas físicas 83, 85, 132 e 133, política v2 e conferência visual |
| Recuperação real | 24/24 consultas positivas com referência esperada no top-5; 4/4 fora de escopo sem evidências |
| Outras finalidades | Consultas de geração geral e triagem retornaram evidências |
| Repetição | Zero novas versões/ingestões/pontos para o mesmo preparo |
| Preservação | Checksums das linhas dos demais domínios permaneceram iguais |

As extrações foram comparadas com os hashes dos recortes revisados antes de
indexar. E5 local, PostgreSQL e Qdrant são reais; essa verificação não simula
embeddings nem usa LLM. Resultado inicial detalhado fica no
[resumo estruturado](preparacao-rag-local-20261119.json).

Uma primeira tentativa de usar os cinco trechos do livro também no chat trouxe
falso positivo para uma pergunta de programação. Esse uso foi retirado do plano:
o livro permanece na geração, conforme o escopo anteriormente avaliado.
A ingestão dessa tentativa fica REVOGADA com auditoria; seus cinco vetores
históricos não participam da busca. Por isso o ambiente tem 29 pontos físicos
e 24 ativos, sem apagar histórico. Perguntas/limiares dos ensaios não foram alterados.

Não foi promovido o restante do acervo nem criada cobertura clínica adicional.
Fonte ausente, dados insuficientes e casos graves continuam com suas regras.
Uma fonte aprovada sem ingestão completa não vira evidência por estar cadastrada.

## Testes da implementação

- 62 testes de backend, contratos e integrações aprovados; dois ensaios opcionais
  de embeddings reais ficaram skipped nessa suite, por sua flag específica.
  E5 real foi exercitado separadamente no preparo e nas 30 consultas acima.
- Sete testes da tela de corpus aprovados, incluindo ausência de menu e bloqueio
  de navegação do administrador comum.
- Regressão completa do frontend: 92 testes aprovados com um worker.
  Uma rodada paralela falhou no teste de foco da sessão; o caso passou isolado
  tanto nesta proposta quanto na versão anterior, e a rodada completa sequencial
  passou. Código e testes de autenticação permaneceram inalterados.
- API de curadoria desligada retorna 404 inclusive para administrador autenticado;
  ativada, preserva autorização, origem e CSRF.
- Repetição, hashes alterados, finalidade não aprovada, travessia de caminho,
  curador inexistente e retirada auditada de seleção antiga foram exercitados.
- Lint, formato, tipos, build, documentação e sincronismo do SPEC verificados.

Os aceites antigos de RAG-05/AI-06/TST-01 permanecem históricos. Este trabalho
prepara o ambiente manual; não amplia a certificação de qualidade do LLM.
Backup, mensagens, respostas privadas, banco e pesos permanecem fora do Git.

## Verificação pequena do provedor real

Uma pergunta sintética sobre volume usou os trechos recuperados do banco local,
o prompt de chat vigente e Groq/openai/gpt-oss-120b. A resposta em português
passou por JSON Schema e validação de referências, com uma citação válida.
Foi uma chamada, 1.631 tokens totais e cerca de 835 ms no provedor.
Isso comprova esse caminho simples; não é nova avaliação ampla de fichas ou
garantia de quota futura. Nenhum dado de cliente foi enviado, e a resposta
completa permanece em artefato privado, fora do Git.
