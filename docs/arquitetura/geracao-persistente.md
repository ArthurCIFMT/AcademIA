# Geração persistente e publicação — AI-03

## Entrega e fronteiras

MOD-06 persiste execucao_ia, triagem, etapa_ia e evidencia_execucao na migration
0014. MOD-04 conserva a propriedade da ficha, seus dias/itens, parecer, retenção,
validação e aviso. Nenhuma dependência nova. O MER original é preservado;
[modelo lógico](modelo-de-dados/modelo-logico.dbml) e dicionário refletem os campos.

Ajustes equivalentes indispensáveis ao cartão: app/main.py registra a API;
training/generated.py implementa o contrato interno de publicação do seu próprio
domínio; knowledge/retrieval/publication.py oferece a verificação SQL com locks
das fontes do seu próprio módulo. MOD-06 não consulta tabelas internas desses
módulos. O campo de explicação pública pertence à versao_ficha, é lido no contrato
de consulta existente e eliminado junto ao conteúdo expurgado.
Desde a [ADR-007](decisoes/ADR-007-livro-e-fundamentacao.md), o LLM gera os itens
e o backend, após validação, apresenta um resumo factual de dias/itens/cargas
pendentes. A justificativa livre não é propagada ao conteúdo publicado.
Referências efetivamente usadas e proveniência permanecem na execução.

[Orquestrador AI-02](orquestracao-ia.md) e seus prompts são reutilizados. A geração
usa até uma análise e uma geração, sem retry/fallback automático. Não há tela
nova: AI-04 implementará solicitação/acompanhamento; chat/adaptação pública segue
em AI-05; ensaio real de qualidade/tempo continua em AI-06.

## API do cliente

| Método/rota | Entrada/resultado |
|---|---|
| POST /api/v1/ia/fichas/execucoes | solicitacao_id UUID; executa geração para o titular e devolve recibo |
| GET /api/v1/ia/fichas/execucoes/{id} | recibo da própria solicitação, inclusive após reinício |
| DELETE /api/v1/ia/fichas/execucoes/{id} | cancela execução ativa; finalizada permanece finalizada |

Sessão ativa e papel cliente, CSRF nas mutações, Cache-Control: no-store.
Não aceitar cliente_id, onboarding arbitrário, ficha, Signals ou parecer no POST.
Sem sessão: 401; permissão recusada: 403; solicitação alheia/inexistente: 404;
chave reutilizada com entrada divergente: 409; validação da entrada: 422.
O recibo inclui estado/motivo estruturados, referência publicada e consumo;
não contém anamnese, resumo, texto bruto do modelo ou prescrição duplicada.
PUBLICADA identifica resultado persistido, não parecer ACEITO.
A rota de consulta do MOD-04 já exibe a ficha própria antes de qualquer parecer.

O serviço interno também permite instrutor designado solicitar geração para seu
cliente; autoria humana de prescrição manual segue o fluxo já existente.
O endpoint público desta etapa resolve exclusivamente o cliente pela sessão.

## Consistência e falhas

Identificador interno é UUID derivado de ator+solicitação. Chave é única por
cliente/ator/solicitação, com hashes de entrada e contexto. Replay é consultado
antes de preparar novo contexto: não refaz análise/busca/LLM nem promove uma ficha
antiga a vigente. Alterar entrada na mesma solicitação conflita. Nova tentativa
exige ID explícito novo, mantendo recibos e consumo anteriores.

Advisory lock por cliente e row locks serializam claim/reserva/despacho/finalização.
Cliente e versão-base são fixados antes da execução. Cada etapa possui reserva
única e marca de chamada física anterior ao HTTP; erro, quota e cancelamento não
zeram a reserva. Guardar tokens reais quando disponíveis, indicação de consumo
desconhecido, bytes/hash do prompt, instante do despacho e duração da resposta.
Não copiar prompts privados ou raciocínio interno em logs técnicos.

Uma execução possui prazo UTC durável e identificador do processo que a iniciou.
Outro processo ou prazo expirado encerra sem retomar chamadas. O MVP roda em um
processo conforme ADR-004; não iniciar workers independentes de geração.
Rede e embeddings ocorrem entre transações curtas; não segurar locks SQL durante
essas chamadas. Cancelamento em voo pode registrar consumo da resposta tardia,
mas não publica nem muda terminal. O orçamento não reinicia no replay.

Após resposta validada, a transação final revalida conta/designação, snapshot e
revisão do onboarding, política, catálogo/recursos, versão-base e fontes aprovadas.
O módulo de conhecimento trava documento, ingestão e fragmento, verificando
revisão/hash/indexação. MOD-04 trava o contexto e revalida equipamentos completos.
O prazo é conferido novamente após a publicação, ainda dentro do savepoint:
se ultrapassado, desfazer ficha/aviso e conservar falha auditável.
Publicação, vínculo à execução, troca de vigente, validação, retenção e aviso
interno são atômicos. Falha não altera a vigente. O aviso interno reutiliza o evento
de TRN-03 e a fila de parecer funciona independentemente do envio SMTP.

Graves/dados insuficientes são barrados pelo mesmo motor de AI-01. Ausente não é
saudável. Para saúde declarada, a porta de contexto exige escopo técnico curado
que cubra as restrições e RAG-05 deve retornar suporte pertinente; fonte genérica
ou pontuação alta não basta. Sem esse mapeamento/evidência, abster-se.
Não inventar mapeamentos clínicos para ativar casos. AI-05 acrescenta o
[mapeamento técnico opcional de cenários](chat-e-adaptacao.md#suporte-técnico-para-cenários-de-saúde);
sem configuração pertinente, a composição padrão mantém essa abstenção.
A composição por portas também admite o mapeamento aprovado do cenário.
Sem embeddings, corpus ou LLM disponível, retornar falha/abstenção controlada.
Treino manual permanece independente. Não exigir laudo ou aprovação médica.

## Retenção e rastreabilidade

A ficha IA começa com parecer funcional PENDENTE e origem IA. Aceitar/rejeitar e
alterar manualmente usam TRN-03; IA não preenche aceite humano. Publicar acima de
quinze versões remove conteúdo antigo. Rejeitadas seguem RF-35. A explicação
publicada é imutável e expurgada com dias/itens. Não armazenar JSON da proposta em
execucao_ia: constraint impede esse campo. Guardar somente referência à versão,
resultado, decisão, evidências bibliográficas/hash e consumo.

Conteúdo privado de execução/triagem expira em 90 dias, independente das quinze
fichas. Em backend/, com banco configurado:
uv run --locked --env-file ../.env python -m app.modules.ai.persistence.maintenance
O expurgo remove resumo/resposta brutos, preservando recibo idempotente, estados,
referências de auditoria e contadores. Não remove ficha publicada nem snapshot
de treino executado. Literatura compartilhada nunca recebe dados de cliente.
Referências históricas a fontes revogadas não autorizam novo uso na geração.

## Evidências

[Comandos e resultados](../testes/comandos.md#geração-persistente-ai-03).
PostgreSQL e Qdrant são reais; embeddings de fixtures são controlados nos testes
novos e o contrato Groq usa HTTPX MockTransport, sem chave pessoal/rede Groq.
Isso comprova integração de código/contratos, não adequação clínica, fidelidade
semântica da resposta real ou desempenho do provedor gratuito. E5/Mailpit reais
continuam na regressão dos módulos anteriores. A extração/revisão pendente de
materiais não foi declarada concluída nem substituída por fontes inventadas.
