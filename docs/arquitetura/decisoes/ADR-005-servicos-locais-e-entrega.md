# ADR-005 — Serviços locais e entrega incremental

Status: ACEITA
Data: 2026-11-04
Origem: responsável delegou a seleção de frameworks, campos e regras técnicas;
academia única foi escolhida expressamente. Escolhas registradas sem exigir nova aprovação.

Decisão: execução inicial sem Docker. PostgreSQL 17 nativo no Windows, host
127.0.0.1:5432, bancos separados academia_dev e academia_test; usuário da aplicação
não-superusuário e configuração por ambiente. FND-05 cria/aplica migrations e
verifica banco real; não substituir integração por SQLite.
FastAPI/Uvicorn em 127.0.0.1:8000, um worker. Vite em 127.0.0.1:5173, proxy /api.
Qdrant local persistente só é aberto pelo backend (comandos de ingestão offline
exigem backend parado ou exclusão mútua). Banco de teste em diretório temporário.
Mailpit binário nativo Windows: SMTP 127.0.0.1:1025 e interface 127.0.0.1:8025,
sem relay externo. Fornecedor de e-mail real pode ser adaptado depois.
Cargas/pesos, fotos e uploads são privados, via armazenamento local protegido;
imagens públicas de equipamentos são expostas por rota controlada, sem caminho livre.

Instalar/configurar esses recursos pertence aos prompts de implementação, não foi
feito por estes ADRs. FND-04/FND-05 registram comandos reais e versões travadas.
GATE-06 fechado documentalmente significa estratégia local definida, não serviços
já instalados ou testes aprovados. Ausência de recurso impede só seu ensaio dependente.

CompreFace e catraca são pós-MVP: manter API selecionada; hospedagem/versão e
ensaio real continuam em GATE-08, sem bloquear scaffold. Reservas de aulas ficam
dispensadas no MVP e pendentes de escopo futuro (GATE-07). Pagamentos automáticos
continuam tardios (GATE-09). Não antecipar Docker da aplicação.

Fontes: [PostgreSQL Windows](https://www.postgresql.org/download/windows/),
[Mailpit nativo](https://mailpit.axllent.org/docs/install/).

## Conveniência para revisão manual — 2026-11-20

O [iniciador Windows](../../instalacao/iniciar-com-dois-cliques.md) reúne os
comandos existentes num painel de dois cliques, com configuração local privada.
Não antecipa Docker, muda a arquitetura ou aplica migrations/seeds. Inicia
serviços de forma controlada, espera healthchecks e encerra apenas o que criou;
PostgreSQL já ligado é preservado. Chaves ficam no backend e o Mailpit não herda
relay externo. As verificações atuais estão no [relatório](../../testes/iniciador-local-20261120.md).

## Manutenção incremental autorizada — 2026-11-20

O responsável autorizou manter o iniciador compatível em cada implementação
que altere a operação local, sem precisar solicitar um reparo separado. Esse
ajuste integra a entrega operacional segundo AGENTS.md/contrato comum e o
[procedimento permanente](../../instalacao/iniciar-com-dois-cliques.md#manutenção-permanente-entre-implementações).
Isso mantém o ciclo de dois cliques, sem antecipar Docker/serviços futuros,
substituir configurações privadas ou executar preparação de dados implicitamente.
