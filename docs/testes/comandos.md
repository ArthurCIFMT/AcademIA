# Registro de comandos de verificação

Nenhuma aplicação foi criada. Portanto os comandos abaixo ainda não existem.
As siglas são referências para os prompts e não devem ser executadas no terminal.
Suíte significa conjunto organizado de testes. IA inclui o fluxo agentivo;
RAG verifica ferramentas/recuperação sem exigir o orquestrador LLM.

| Suite | Estado | Prompt que registra o comando real |
|---|---|---|
| DOC | Parcial: git diff --check + verificações documentais | FND-01 |
| BE | PENDENTE | FND-04 |
| INT | PENDENTE | FND-05/FND-06 |
| API | PENDENTE | FND-06 |
| FE | PENDENTE | FND-07 |
| E2E | PENDENTE | TST-01 |
| DB | PENDENTE | FND-05 |
| RAG | PENDENTE | RAG-05 |
| IA | PENDENTE | AI-06 |
| INF | PENDENTE | INF-04 |

Após cada configuração, substituir PENDENTE por comando exato, diretório de execução
e requisitos de ambiente. Atualizar a seção Comandos de AGENTS.md.
Na execução de um cartão, resolver as siglas primeiro. Se o próprio cartão cria
a suite, configurar e rodar o comando nessa entrega. Caso contrário, ausência do
comando é pendência de dependência, não resultado aprovado.
