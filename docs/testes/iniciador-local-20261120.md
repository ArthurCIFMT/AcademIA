# Iniciador Windows para revisão manual — 2026-11-20

## Entrega

[Guia de dois cliques](../instalacao/iniciar-com-dois-cliques.md), arquivos
Iniciar AcademIA.cmd/Encerrar AcademIA.cmd e scripts/academia_local.py. Painel
Tkinter e serviços existentes, sem dependências novas, instalador, Docker,
modificações de regras, schema, prompts de IA ou dados de negócio. Configuração
local privada dos caminhos já preparada nesta máquina e ignorada no Git.

Abrir inicia serviços, espera healthchecks e abre o navegador padrão; encerrar
usa os handles próprios e um pedido local de shutdown. API recebe encerramento
normal; PostgreSQL que já estava ligado não é desligado. Portas ocupadas não
provocam busca/encerramento indiscriminado de processos. Mailpit mantém a caixa
persistente e não herda relay do ambiente. Chaves não vão para o frontend,
Mailpit ou linha de comando. A configuração de ambiente e os serviços continuam
sendo os da ADR-005; scripts não atualizam schema, corpus ou catálogo.

## Verificações desta versão

- 14 unitários aprovados: loopback, isolamento de credenciais, portas ocupadas,
  preservação de serviço preexistente, falha de startup/limpeza dos próprios,
  shutdown da API, PID de cluster alterado e comando de encerramento/lock.
- Ruff/formato e mypy dos dois fontes novos aprovados. O mypy usa MYPYPATH
  apontando a backend/ para resolver os imports do projeto, sem ignorar erros.
- Ciclo real com PostgreSQL, Mailpit, API e Vite: site e proxy responderam,
  início repetido não duplicou serviços, término restaurou as cinco portas ao
  estado desligado. Apenas healthchecks/leitura de revisão, sem negócio/LLM.
- Painel real Pythonw/Tk abriu, iniciou os serviços e recebeu o mesmo pedido
  de Encerrar do arquivo .cmd. A janela saiu com código0 e as portas próprias
  ficaram livres. O teste final de encerramento não reabriu o navegador.
- Após copiar os fontes para o projeto original, os dois arquivos .cmd reais
  foram executados: Iniciar disponibilizou API, site/proxy e e-mails; Encerrar
  fechou os serviços próprios e restaurou as cinco portas ao estado desligado.
- A abertura automática anterior do site no navegador foi observada pelo
  título da janela do navegador e pelas respostas HTTP do frontend/proxy.

Limitação: a inspeção visual dos botões pelo provedor de controle do Windows
falhou na associação da janela Tkinter a seu aplicativo, apesar de ela constar
no inventário. Não há captura nem aprovação de QA visual por herança. O ciclo
funcional do painel foi confirmado pelo comando local de controle e pelos
processos/serviços, não por cliques inventados. O usuário pode conferir os
botões durante a revisão manual normal.

Falhas intermediárias: primeira rodada unitária teve seis erros de setup por
pasta temporária ausente; depois houve uma falha do double de subprocess.run
que interferia no import de SQLAlchemy. O mock passou a interceptar somente
Node --version. Nenhum bloqueio do código de negócio foi removido. Lint e
resolução do caminho do mypy foram corrigidos antes do resultado final.
Dois ensaios iniciais de GUI foram encerrados por PID/árvore próprios após a
falha do provedor visual; o ensaio final fechou normalmente pelo controle do
painel, com código0. Sem alterar a política de encerramento de programas externos.

Não houve reexecução da regressão completa do MVP ou nova qualificação de IA:
backend de domínio, contratos e frontend funcional não foram alterados. Os
relatórios anteriores conservam sua identidade. O [registro JSON](iniciador-local-20261120.json)
contém contagens/hashes e os recibos dos ciclos; logs brutos ficam privados.

## Reprodução dos testes focais

Na raiz do projeto, com o ambiente Python do backend já preparado:

```powershell
& ./backend/.venv/Scripts/python.exe -m pytest -c backend/pyproject.toml tests/test_iniciador_local.py -o addopts=''
& ./backend/.venv/Scripts/python.exe -m ruff check --config backend/pyproject.toml scripts/academia_local.py tests/test_iniciador_local.py
& ./backend/.venv/Scripts/python.exe -m ruff format --check scripts/academia_local.py tests/test_iniciador_local.py
$env:MYPYPATH = (Resolve-Path ./backend).Path
& ./backend/.venv/Scripts/python.exe -m mypy --config-file backend/pyproject.toml scripts/academia_local.py tests/test_iniciador_local.py
```

O ensaio real requer esta máquina já preparada, portas livres e nenhum processo
real de manutenção/ingestão. Abrir Iniciar AcademIA.cmd, esperar site/API e depois
usar Encerrar AcademIA.cmd. Conferir que a janela fecha e o site deixa de responder;
se PostgreSQL já estava ligado antes do ensaio, ele precisa permanecer ligado.
Não instalar recursos ou aplicar migrations automaticamente para passar no teste.

Referências técnicas: [subprocess e ambiente do processo](https://docs.python.org/3.12/library/subprocess.html),
[opções do Mailpit](https://mailpit.axllent.org/docs/configuration/runtime-options/) e
[identificação de aplicação no Windows](https://learn.microsoft.com/en-us/windows/win32/api/shobjidl_core/nf-shobjidl_core-setcurrentprocessexplicitappusermodelid).
