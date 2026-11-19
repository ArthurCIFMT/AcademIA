# Revisão após o primeiro uso manual — 2026-11-19

Escopo autorizado: esclarecer convites locais, eliminar a duplicidade entre cargo
livre e papéis selecionados e acrescentar equipamentos/exercícios de demonstração.
Não altera prompts operacionais, módulos de IA/RAG ou migrations aplicadas.
RF-07/RF-08, contratos afetados e SPEC acompanham as mudanças.

## Constatações no ambiente

- Desenvolvimento conservava quatro identidades: três funcionários e um cliente.
- Havia um equipamento e um exercício cadastrados manualmente.
- Cinco envios estavam registrados como aceitos pelo SMTP local.
- Mailpit não entrega no Gmail/Outlook; sem persistência, fechar sua janela pode
  perder as mensagens capturadas. O estado durável do envio não restaura o token.
- O cadastro exigia cargo livre além dos papéis, duplicando o preenchimento.
- Não havia documentos, versões documentais ou ingestões em desenvolvimento.
  Essa carga é preparação pendente para revisar a IA com evidências reais.

Contagens representam o início da manutenção e não dados de teste adicionados
depois. Foi gerado backup local do banco antes da carga; não é versionado.
Não se publicam nomes, e-mails, senhas, tokens ou cópias do banco neste relatório.

## Correções e uso

Há apenas seleção dos cargos permitidos, preservando papéis acumuláveis e o
perfil cliente independente. O backend deriva a descrição em novas gravações;
o campo legado de entrada é opcional e depreciado. Não há atualização em massa
de históricos nem mudança de schema.

Funcionários, clientes e recuperação explicam o destino local e mostram a caixa
configurada em `VITE_TEST_MAILBOX_URL`. Para abrir uma conta convidada, com os
serviços ativos, use **Reenviar convite** e o link novo no Mailpit. Links expirados
ou já consumidos continuam recusados; senhas não são redefinidas pelo operador.

A [carga versionada de demonstração](../../database/seeds/README.md) fornece
16 equipamentos e 30 exercícios, com recursos obrigatórios/alternativos e
dispensa explícita. Não cria pessoas, fichas ou evidências de saúde e não
apaga/inativa os cadastros manuais existentes.

No ambiente local, a aplicação da carga resultou em 17 equipamentos e 31
exercícios; uma segunda execução criou zero registros. As linhas anteriores
de equipamentos, exercícios e perfis foram comparadas e preservadas.
Dois convites pendentes foram reemitidos para o Mailpit. Um instrutor atingiu
o limite vigente de três emissões em 24 horas; esse limite foi preservado.
Foi criado separadamente o funcionário sintético **Instrutor de demonstração**
(`instrutor.demo@example.test`), somente com papel de instrutor e convite local.
Sua senha deve ser definida pelo responsável no link; não há senha padrão.
Depois da ativação, designe o cliente a esse instrutor para testar a ficha manual.

## Verificações

- 41 testes de backend/contrato/integração aprovados: pessoas, notificações,
  equipamentos e a carga de catálogo; PostgreSQL real e Mailpit local.
- 14 testes de frontend aprovados: funcionários, clientes, recuperação e aviso.
- Oito cenários E2E aprovados no Edge, sem skips/retries: Vite, HTTP, PostgreSQL,
  SMTP e Qdrant locais; IA controlada. Incluem primeiro acesso e ficha manual.
- Regressão específica: endereço com domínio Gmail recebe convite na caixa local,
  define senha e autentica; nenhum e-mail externo é enviado.
- Carga repetida preserva revisões/edições, disponibilidade, contagens e auditoria;
  não administrador é recusado. Recursos inválidos impedem a carga.
- Ruff/formato, mypy, lint/types/build do frontend e documentação verificados.

A primeira rodada revelou configuração de Mailpit sem supressão de Message-ID
duplicado e acesso negado ao diretório temporário padrão. Repetição com a opção
documentada e pasta temporária própria aprovou os 41 testes. Um erro de tipo no
teste de frontend e um nome de variável no seed foram corrigidos antes do aceite.

O E2E registra `testes_locais_aprovados=true` e não constitui novo aceite de LLM
real. Não houve chamadas externas nem consumo de quota. Ensaios AI-06/TST-01
anteriores permanecem como histórico; esta correção não reaprova o modelo.

O [resumo estruturado](revisao-manual-20261119.json) conserva os resultados
sem incluir fixtures privadas, credenciais ou dados pessoais do desenvolvimento.
