# Revisão didática e de consistência

Data: 2026-11-04. Base: af1685b. Revisão documental; aplicação ainda não implementada.

## Solicitação vigente

O projeto é um trabalho didático acadêmico. Não exigir aprovação médica profissional,
laudo, atestado, assinatura de médico ou validação jurídica externa para gerar,
implementar ou demonstrar o MVP. Esses processos não entram nos gates.
Manter o comportamento pedido: dúvidas com RAG semântico, análise de onboarding
resumido, geração de fichas pelo LLM, casos graves bloqueados, dados ausentes
explícitos, recursos disponíveis e parecer posterior do instrutor.

## Achados e correções

| Achado | Correção | Fontes afetadas |
|---|---|---|
| Estado de liberação profissional sugeria fluxo médico obrigatório | Três estados: DADOS_INSUFICIENTES, BLOQUEADO_POR_SEGURANCA, ELEGIVEL_PARA_GERACAO; sem laudo/desbloqueio por documento; erro/timeout é técnico | AGENTS.md, MRF08, RF-15, módulos, arquitetura e AI-01 |
| Revisão do corpus/casos podia ser interpretada como aprovação externa | Conferência técnica e regras da demonstração pelo responsável/curador; manter proveniência e metadados | GATE-04, mestre, contrato, requisitos, testes e relatório bibliográfico |
| AI-03 publicava antes da entrega do serviço completo TRN-03 | Dependência direta de TRN-03; usar o contrato proprietário | AI-03 e manifesto |
| AI-04 podia publicar/avisar novamente após AI-03 | Acompanhar versão e evento existentes, sem duplicar publicação, pendência ou aviso | AI-04 e cenários |
| Chat mencionava snapshot completo apesar de contexto curto | Dúvida usa pergunta/janela/trechos; só adaptação explícita consulta contexto resumido | AI-05 |
| Novo relato exigia versionamento sem contrato claro de confirmação | CA-11.4, serviço ONB-02 e formulário ONB-03; AI-05 aguarda confirmação sem escrever MOD-03; novo snapshot invalida análise antiga | RF-11, ONB-02/03, AI-05 e modelo de dados |
| Retry de transporte podia contradizer teto de chamadas LLM | Uma tentativa por etapa LLM, sem retry automático; replay idempotente reusa execução; novo pedido explícito tem outro ID; busca/ingestão têm orçamento próprio | MRF04, RNF-18, orquestrador e AI-02 |
| Escopo de AI-02 não incluía portas/adaptadores do provedor | Caminhos explicitados sem ampliar acesso a outros módulos | AI-02 |
| Testes/rastreabilidade não refletiam refinamentos | 24 cenários planejados, metadados/matrizes e E2E atualizados | AI-06, TST-01, estratégia e matrizes |

ONB-04 é dependência de entrega de consultas/permissões, não aprovação prévia do
instrutor para cada geração. Parecer posterior da academia continua funcional,
separado de avaliação médica formal. Acesso manual à catraca continua auditado;
a dispensa de laudo não altera regras de matrícula, biometria ou autorização.

## Preservação e limites

Não foram removidas regras de casos graves, evidências para adaptação, isolamento,
catálogo, disponibilidade de equipamentos, limite de 15 versões ou substituição
da rejeitada anterior. CompreFace, matrícula sem pagamento obrigatório e Docker
tardio permanecem. MER original, PDFs, metadados e JSON dos 32 casos preservados.
Observações científicas/limitações do relatório bibliográfico continuam sendo
evidências; não se transformam em requisito de aprovação externa.

A revisão não escolhe modelo/provedor, livro/corpus ativo, campos/unidades ou
valores de regras da demonstração. Essas escolhas técnicas/casos esperados continuam
com o responsável do projeto. Não foram criados serviços, migrations ou testes reais.

## Verificação

Executar auditor documental e git diff --check; conferir também sentido dos
contratos, contexto curto, estados e dependências. Conjunto de testes especificado
não significa integração LLM/biometria ou desempenho já comprovados.
Ver [checklist vigente](../testes/revisao-dos-prompts.md),
[arquitetura](../arquitetura/rag-semantico.md) e
[macrorequisitos](../requisitos/macrorequisitos-ia-rag.md).
