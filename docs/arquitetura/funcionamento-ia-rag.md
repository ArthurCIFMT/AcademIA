# Funcionamento da IA e do RAG

A IA tem três usos: dúvidas dos clientes, triagem assistida do onboarding resumido
e geração/adaptação de fichas pelo LLM. Instrutor também cria manualmente e avalia
fichas posteriormente. Não restringir IA ao chat nem implementar pesquisa agentiva.

A [tabela completa dos 15 macrorequisitos](../requisitos/macrorequisitos-ia-rag.md)
contém 67 critérios identificados, com atores e módulos. O [orquestrador](rag-semantico.md)
coordena etapas fixas; [MOD-05](modulos.md) recupera conhecimento e MOD-06 usa LLM.
O livro/literatura fornece fundamentação, o catálogo fornece exercícios existentes,
e MOD-10 informa equipamentos atuais. Recuperar poucos trechos reduz contexto
comparado ao livro inteiro; desempenho depende de ensaio, não é garantido pelo RAG.

Chat: pergunta + janela curta + evidências → uma resposta com fontes.
Ficha: snapshot → resumo sem omitir alertas → regras/busca/análise de triagem →
candidatos e conhecimento especializado → uma geração → validações → publicação.
Até uma análise e uma geração no pedido de ficha, sem revisores em cadeia.
Caso bloqueado, incompleto ou adaptação sem evidência não publica; não diagnosticar.
Cliente consulta treino e conversa antes do parecer profissional. Modificações
publicadas geram versão; manter até 15 completas e a regra de rejeitadas.
Falha da IA não impede o instrutor de criar/alterar treino manualmente.

O [modelo de dados](modelo-de-dados/dados-rag-ia.md) é proposta para implementação,
não alteração do MER original. [Testes](../testes/rag-ia-semantico.md) ainda serão
implementados; [acervo](../../materiais/rag/README.md) tem nove documentos selecionados
para ingestão, com extração/indexação e ensaio reais ainda por executar.
