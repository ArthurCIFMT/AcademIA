# RAG-05 — Recuperação, citações e avaliação vetorial

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: RAG-04.
- Requisitos: MRF02, MRF11, MRF12, MRF15; RN-29, RN-39; RNF-13; MRF17, MRF18, MRF19 (ferramentas de conhecimento).
- Módulos: MOD-05.

## Objetivo e contexto

Entregar recuperação, citações e avaliação vetorial, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.
Consulte o [fluxo agentivo](../../arquitetura/agentic-rag.md), a
[extensão de dados](../../arquitetura/modelo-de-dados/extensao-agentic-rag.md)
e o [conjunto de testes](../../testes/agentic-rag.md). Suíte significa conjunto
organizado de testes; sigla de teste não é comando pronto de terminal.

## Escopo permitido

- `backend/app/modules/knowledge/retrieval/**`
- `backend/tests/knowledge/**`
- `docs/testes/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar top-K por cosseno com filtros de versão/estado e query minimizada.
2. Retornar fonte, página/seção e score; tratar baixa evidência por abstenção.
3. Criar conjunto rotulado de consultas, medir relevância e p95 documentando ambiente e tamanho.

## Critérios de aceite

- Consulta nunca recupera documento não aprovado/revogado.
- Consultas de teste em português recuperam evidências esperadas PT/EN com modelo
  de embeddings compatível; avaliar relevância por idioma, sem traduzir o acervo
  automaticamente ou presumir desempenho só porque o modelo é multilíngue.
- Busca insuficiente retorna ausência explícita, sem citações inventadas.
- Score alto sozinho não prova suporte: verificar condição, população e
  intervenção. Sem evidência pertinente, adaptação por saúde não pode prosseguir.
- p95 vetorial <= 2 segundos no cenário documentado; métricas de relevância têm limiar aceito antes do ensaio.

## Complementos obrigatórios para Agentic RAG

1. Expor `buscar_evidencias` e `ler_contexto_documental` por contratos versionados
   de leitura de MOD-05; este cartão não exige LLM nem implementa o planejador.
2. Backend impõe corpus/versão/aprovação e limites de top-K/páginas/tamanho. Consulta
   pode ser reformulada pelo agente posteriormente; filtros obrigatórios não.
3. Ler contexto somente de ID de documento/trecho previamente obtido e aprovado,
   preservando tabela/ressalva e proveniência. Negar URL/caminho de arquivo livre.
4. Retornar resultados verificáveis e distinguir vazio, argumento inválido,
   não autorizado e falha técnica. Revogação invalida resultado/cache ativo.
5. Testar AR-01/04/14/16/23: contratos das ferramentas, contexto suficiente,
   injeção documental, fonte revogada e PT/EN. Medir p95 por chamada vetorial,
   não duração de toda a pesquisa agentiva.

Critérios adicionais: ferramenta não recupera fora do corpus autorizado, score não
é decisão clínica e IDs de citações correspondem a resultados reais. AI-02
implementa a avaliação de suficiência de MRF19; o backend continua verificando
aplicabilidade e restrições conforme políticas aceitas.

## Testes obrigatórios

RAG; BE; INT; configurar comando RAG e guardar relatório reprodutível.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Confundir similaridade com probabilidade clínica ou tempo completo da geração.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
