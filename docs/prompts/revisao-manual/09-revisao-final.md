# 09 — Revisão final antes do VAL-02

## Tarefa

Conferir as correções entregues e produzir evidência suficiente para a regressão final do escopo vigente.

## Escopo e contexto

- Revisão de código, contratos e resultados, com execução de testes isolados. Alterações de aplicação cabem somente no cartão responsável. Consulte VAL-01/02, manifesto, matriz de rastreabilidade e README local.
- Use `docs/testes/comandos.md`, `docs/testes/estrategia.md`, o guia visual e a documentação de CompreFace. Regressões encontradas retornam ao cartão de origem.
- O VAL-02 mantém sua própria execução. Registre para VAL-02 a asserção legada que espera a revisão 0026 apesar de o head anterior às novas mudanças ser 0027.

## Matriz mínima de revisão

1. Confira destino direto, celular, retorno, recarga, links antigos, seção ativa e teclado nos quatro papéis e em conta acumulada.
2. Confira dados próprios, endereço opcional para cadastros antigos, persistência da edição e permissão exclusiva do titular.
3. Confira seleção e confirmação da foto, preservação da referência em falha, miniatura privada, substituição e reconhecimento com CompreFace real. Identifique os ensaios que usaram dublês.
4. Confira continuidade da seleção do cliente, matrícula com ou sem pagamento, biometria pendente, contingência auditada e frequência após passagem simulada.
5. Confira idade derivada e snapshot histórico, dúvida complementar, dúvida essencial, bloqueio grave, preservação de chat/ficha e erro técnico controlado.

## Critérios de aceite

- Cada cenário indica requisito, ambiente, teste ou evidência manual, resultado e pendência.
- A revisão verifica links, SPEC, diff, migrations e compatibilidade do iniciador proporcionais ao impacto. Nenhum resultado controlado conta como evidência de provedor real.
- Registre o que está pronto para VAL-02 e o que ainda precisa de correção. Somente uma execução do VAL-02 pode registrar seu aceite.

## Testes e entrega

Executar seleções BE, INT, API, FE e E2E dos cartões afetados, além de DOC/SPEC e `git diff --check`. Para mudanças de banco, conferir migration com dados sintéticos preexistentes. Para biometria, rodar o cenário real em coleção de teste autorizada. Não repetir chamadas ao LLM sem necessidade de verificar o contrato afetado. Reportar resultado consolidado e próximo passo.
