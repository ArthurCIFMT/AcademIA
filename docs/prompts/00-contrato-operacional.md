# Contrato comum dos prompts operacionais

Cada cartão operacional incorpora este contrato por referência. Ele evita repetir
as mesmas instruções em dezenas de arquivos. Sua leitura é obrigatória.

## Leitura e pré-condições

Leia AGENTS.md, o contexto de execução, o cartão, os requisitos citados, os ADRs
aplicáveis, o modelo lógico aceito e a estratégia de testes. Confirme no manifesto
as dependências concluídas e os gates fechados. Texto escrito não significa tarefa
executada. Estado inicial dos cartões futuros: BLOQUEADO até suas dependências.

## Escopo e entregáveis

Altere apenas os caminhos indicados pelo cartão. Em cada capacidade de domínio,
entregue migration pertinente, contratos REST/JSON, serviço de aplicação, testes e
documentação. Inclua a tela quando indicada; API pronta não comprova tela pronta.
Use as convenções e caminhos definidos no scaffold/ADRs; registre ajuste equivalente
de caminho antes de editar se a estrutura adotada diferir da prevista.

São permitidas também atualizações diretamente afetadas em docs/arquitetura/,
docs/testes/ e no manifesto. Lockfiles, configuração e dependências podem mudar
somente se essenciais à entrega e com justificativa. Não antecipe outro módulo.

## Critérios e testes

Os cenários do cartão são mínimos e complementam os critérios completos dos RF/RN.
Use os códigos de suites de docs/testes/comandos.md, resolvidos em comandos reais
durante os scaffolds. Código de suite não é comando de terminal. Não declare
sucesso se um comando estiver pendente ou se faltou serviço externo necessário.

Acrescente testes aos comportamentos alterados. Execute somente suites pertinentes,
lint/tipos/build afetados e git diff --check. Integração usa PostgreSQL real de teste
quando há persistência; testes unitários de portas usam doubles controlados.
Métricas da IA requerem dados de avaliação rotulados; um JSON válido não comprova
que o treino é adequado. Use dados sintéticos e não publique credenciais.

## Interrupção e decisões

Suspenda apenas a parte dependente de gate aberto, contrato ausente ou conflito
material. Informe a informação exata que falta. Adaptação rotineira já autorizada
não requer novo aceite. Não substitua serviço obrigatório por mock no aceite real.
Não invente regras clínicas, fontes ou parâmetros financeiros para destravar o fluxo.

## Atualização de dados

Respeite ownership entre módulos. Inclua migration para novos invariantes, sem
alterar migrations aplicadas. Atualize também o modelo textual e dicionário quando
o requisito mudar. Não apague o MER original. Histórico aprovado é preservado.

## Git e relatório

Siga GATE-05 e a autorização da conversa vigente. Um prompt não concede permissão
genérica para merge, force-push ou apagar trabalho alheio. Use commit coeso por
entrega e confirme a sincronização local/remota quando autorizada.
Registre ID, arquivos, comandos reais, resultados, pendências e commit/evidência
no manifesto. Não marque CONCLUIDO quando um critério obrigatório não foi testado.
O relatório final segue AGENTS.md.
