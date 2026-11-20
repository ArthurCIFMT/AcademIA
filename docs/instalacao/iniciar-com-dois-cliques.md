# Abrir e encerrar o MVP com dois cliques no Windows

Na pasta do projeto, dê dois cliques em **Iniciar AcademIA.cmd**. Não é preciso
digitar comandos nem abrir os PowerShells dos serviços. O pequeno painel inicia
PostgreSQL, Mailpit, API e frontend e abre o site no navegador padrão quando o
proxy e a API respondem corretamente. A primeira inicialização pode demorar.

## Uso diário

1. Abra Iniciar AcademIA.cmd e aguarde “Sistema pronto”.
2. Use o navegador normalmente. O botão **Abrir site** volta à página inicial.
3. Para convites e recuperação, use **Abrir e-mails de teste**. As mensagens ficam
   no Mailpit local, mesmo quando o endereço cadastrado é Gmail ou Outlook.
4. Ao terminar, use **Encerrar sistema**, feche o painel pelo X ou dê dois cliques
   em **Encerrar AcademIA.cmd**. O segundo arquivo também funciona com o painel
   minimizado. Nenhum dado de cadastro, treino, corpus ou e-mail é apagado.
5. **Abrir registros** mostra a pasta privada dos logs quando houver falha.

Os dois arquivos ficam na raiz, junto de README.md. Se o Windows ocultar
extensões, aparecem como “Iniciar AcademIA” e “Encerrar AcademIA”. Para usar pela
Área de Trabalho, crie um atalho para o arquivo original; não mova o arquivo
para fora da pasta do projeto. Não use o Gerenciador de Tarefas para fechar o
painel durante a inicialização: o encerramento normal usa as ações acima.

Antes de implementar mudanças, aplicar migrations ou preparar o RAG offline,
encerre o painel. Depois da manutenção, abra novamente o iniciador.

## O que o painel faz

- Usa o Python do backend e as instalações locais já preparadas; não instala
  pacotes, baixa modelos, aplica migrations, semeia dados ou recria o banco.
- Lê .env do backend e a configuração do frontend. Chaves e senhas não aparecem
  na linha de comando e não são repassadas ao frontend/Mailpit pelo iniciador.
- Exige endereços HTTP de loopback, portas distintas e academia_dev local.
  Não abre a aplicação na rede pública nem altera firewall/configuração do Windows.
- Verifica a revisão do banco antes de iniciar a API. Uma migration pendente
  exige manutenção técnica explícita, não uma alteração automática de dados.
- Mantém um único painel por projeto. Portas ocupadas provocam uma mensagem;
  o iniciador não tenta matar processos encontrados pelo número da porta.
- Se o PostgreSQL já estava ligado, o reutiliza após conferir a conexão e não
  o desliga no encerramento. Os serviços que ele próprio criou são encerrados
  pelos handles guardados; o PID do cluster é conferido antes de pará-lo.
- A API recebe pedido de shutdown e tem tempo de encerramento antes de um
  eventual encerramento forçado apenas de sua árvore. O Qdrant continua local,
  aberto somente pelo único processo da API; não existe servidor Qdrant extra.
- Usa a caixa persistente backend/data/mailpit.db, sem relay para e-mails externos.
  As configurações MP_* de relay do ambiente não são herdadas pelo Mailpit.

O painel é uma conveniência para desenvolvimento/teste local. Não é um instalador
universal nem substitui a containerização futura. A disponibilidade das IAs ainda
depende de corpus/pesos preparados, chaves do perfil e quota do provedor.
Nenhuma chamada ao LLM é feita para abrir ou encerrar o ambiente.

## Preparação técnica em outra máquina

Nesta máquina, os caminhos já estão configurados em iniciador.local.json.
Esse arquivo é privado/ignorado pelo Git, pois os diretórios variam entre PCs.

Em uma instalação nova, preparar primeiro os [serviços](../../database/README.md),
o [backend](../../backend/README.md), o [frontend](../../frontend/README.md) e o
[RAG local](preparar-rag-local.md), conforme os guias existentes. Copiar
iniciador.local.example.json para iniciador.local.json e ajustar os quatro
caminhos absolutos de ferramentas/cluster. O Python é encontrado automaticamente
em backend/.venv/Scripts; precisa incluir Tkinter (verificado nesta instalação).
Não colocar credenciais nesse JSON; elas continuam somente no .env local.

O script versionado é scripts/academia_local.py. Os .cmd usam caminhos relativos
à própria pasta, com aspas para espaços e acentos; o site abre no navegador
padrão. Os caminhos de URLs/portas vêm dos ambientes já documentados.

## Se não abrir

| Mensagem/situação | Orientação |
|---|---|
| Painel já aberto | Use a janela existente; não há um segundo conjunto de serviços. |
| Porta em uso | Encerre a execução anterior pelo painel/comando apropriado. O iniciador preserva processos externos. |
| Falta configuração/caminho | Conferir iniciador.local.json e instalação inicial; não é preciso decorar os comandos diários. |
| Migrations pendentes | Pedir ao responsável técnico a atualização seguindo o guia do banco. |
| IA retorna erro/quota | O ambiente pode estar ligado normalmente; conferir a resposta e o provedor. Não há retry ou fallback automático novo. |
| Links de e-mail expirados | Reenviar convite pela aplicação; não redefinir senha diretamente no banco. |

Logs ficam em backend/data/iniciador e a caixa de e-mail em backend/data; tudo
fora do Git. Compartilhar logs somente após conferir se contêm dados privados.
As [evidências de verificação](../testes/iniciador-local-20261120.md) distinguem
testes funcionais do iniciador e a limitação da inspeção visual automática.

## Manutenção permanente entre implementações

Por solicitação expressa do responsável em 2026-11-20, a operação com dois cliques
é uma capacidade mantida durante a evolução do projeto. O agente responsável
pela implementação deve avaliar e corrigir o iniciador quando a sua entrega o
afetar, sem esperar outro pedido ou novo aceite funcional para esse ajuste.
Não se trata de autoalteração do código durante a abertura do painel: a manutenção
é executada e versionada pelo agente na própria entrega.

1. Antes de editar, verificar se a etapa muda serviços necessários, dependências,
   executáveis, comandos, pastas, variáveis, URLs/portas locais, proxy, healthchecks,
   exclusividade do Qdrant ou a ordem de inicialização/encerramento. Considerar
   somente capacidades aprovadas e efetivamente implementadas.
2. Se houver impacto, ajustar minimamente os dois .cmd, scripts/academia_local.py
   e suportes indispensáveis ao iniciador, iniciador.local.example.json,
   tests/test_iniciador_local.py e os guias/fontes afetados. O contrato comum e
   AGENTS.md autorizam esse escopo transversal mesmo nos cartões antigos que
   não enumeram esses caminhos. Manter os dois nomes de entrada existentes.
3. Preservar iniciador.local.json e .env do usuário. Quando uma chave nova for
   necessária, adicionar somente o que falta, conservando valores já configurados
   e seu backup apropriado. Nunca substituir configurações privadas pelo exemplo,
   imprimir credenciais ou versionar dados locais. Alterações técnicas já delegadas
   não exigem perguntar novamente escolhas já registradas.
4. Para nova dependência/serviço, respeitar instalação, contrato, gate, escopo e
   autorização da etapa. Quando a preparação do ambiente local estiver abrangida
   pela tarefa, realizá-la separadamente com os cuidados pertinentes e deixar o
   iniciador pronto. Migrations aprovadas continuam explícitas e reproduzíveis;
   não introduzir instalação, reset, seed ou upgrade silencioso ao abrir o painel.
   CompreFace/serviços externos e Docker só entram quando seus cartões permitirem.
5. Preservar autenticação, loopback/isolamento, credenciais só no backend,
   Mailpit sem relay e encerramento apenas de processos próprios. Abertura
   repetida não duplica serviços; falha deve ser informada sem encerrar terceiros
   ou apagar bancos, mensagens, corpus e uploads para aparentar funcionamento.
6. Se alterar código/configuração/ciclo de execução do iniciador, rodar seus
   testes focais e lint/tipos pertinentes. Quando mudar como o sistema sobe ou
   é encerrado, verificar o ciclo real de abrir → prontidão das capacidades
   afetadas → encerrar, preservando serviços que já estavam ligados. Não consumir
   quota de LLM somente para testar o iniciador nem confundir healthcheck com
   aceite funcional de um módulo novo. Resultados anteriores não são reexecução.
7. Atualizar fontes, evidências e SPEC no mesmo commit da entrega; relatar
   “iniciador atualizado”, “compatível sem alteração” ou “não afetado”, explicando
   testes/limitações. Uma incompatibilidade conhecida não pode ficar oculta em
   uma entrega declarada pronta. Bloqueios reais são registrados com o motivo.

Mudanças apenas documentais ou sem efeito na execução local não precisam alterar
o código do iniciador nem repetir o ciclo completo. O agente registra essa
avaliação e faz as verificações correspondentes ao escopo. Autorizações funcionais
não dispensam as permissões técnicas exigidas pelo ambiente de trabalho.
