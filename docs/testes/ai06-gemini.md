# AI-06 — Integração e ensaio separado da Gemini API

## Estado atual

**Integração entregue; modelo ainda não qualificado.** Principal continua Groq/
GPT-OSS 120B. A chave fornecida pelo responsável foi aceita pela API oficial e
salva somente em .env ignorado pelo Git; o arquivo temporário foi removido.
Não criar nem contratar faturamento, serviços pagos ou fallback automático.

A [ADR-009](../arquitetura/decisoes/ADR-009-gemini-api.md) define o candidato
fixo gemini-3.5-flash-lite e o perfil reserva-gemini. Listagem de modelos e teste
mínimo retornaram HTTP 200/JSON válido; isso demonstra acesso, não qualidade de
fichas. Foi observado o ID exato do modelo, sem alias latest ou roteador.
Uma chamada mínima adicional ao 3.1 Flash-Lite terminou em ReadTimeout (20 s);
não foi criado perfil do 3.1, nem usado seu resultado como parte do ensaio.

## Resultados reais e limites

[Ensaio unido](ai06-gemini/ensaio-real.json), [resumo](ai06-gemini/resumo.json),
[revisão vinculada](ai06-gemini/revisao-tecnica.json),
[consolidação](ai06-gemini/consolidacao.json),
[códigos HTTP](ai06-gemini/limites.json) e [diagnósticos](ai06-gemini/diagnosticos.json).

- Três execuções consistentes encerraram por HTTP 503/UNAVAILABLE, não por chave
  inválida ou quota 429. Cada uma fez uma tentativa por etapa e encerrou o lote.
- Cinco casos foram exercitados; três dúvidas (L01–L03) produziram o resultado
  esperado, com português e multiplicações/definições conferidos em RBCM p.5/6.
  L04 e a geração L13 falharam por provedor. Os 22 demais casos ficam pendentes.
- Chat válido: n=3, mediana 1,414 s, p95 5,197 s, apenas tempo do serviço.
  Não estimar tempo de geração/adaptação a partir de falhas ou abstenções.
- Não houve ficha publicada neste ensaio Gemini. Triagem elegível de L13 não é
  qualidade de ficha. Adaptações e ataques SC-01/02 não foram concluídos no
  modelo real; testes determinísticos continuam sendo evidência distinta.
- As partes registram sete chamadas físicas, 6.365 tokens conhecidos e consumo
  desconhecido em três recusas HTTP. Não inferir custo monetário/fatura zero.
- Uma rodada exploratória anterior teve duas dúvidas concluídas e foi interrompida
  para fixar o código/hashes antes do aceite. Ela não é unida às partes finais,
  nem utilizada para substituir respostas desfavoráveis. Seu consumo é separado.

As partes originais ficam nos subdiretórios real-02-final, real-03-retomada e
real-04-fichas-seguranca, com relatorio.json em cada um. A união preserva as
recusas anteriores e não troca resposta concluída/falha de qualidade. A revisão
não inventa avaliação de saída inexistente. Modelos/configurações diferentes
não se unem; partes pré-Gemini da Groq permanecem históricas.

**AI-06/TST-01 permanecem EM_EXECUCAO; PG-01 ABERTO.** Teste mínimo, JSON válido,
boa latência de três dúvidas ou mocks não aprovam o LLM real. Não foi afrouxado
nenhum limiar, bloqueio de saúde, restrição de recursos ou permissão.

## Verificação local

Regressão unitária: 322 testes aprovados; 167 fora dos marcadores selecionados.
Verificações específicas: 64 aprovados na preparação, incluindo integração real
PostgreSQL/Qdrant, publicação PENDENTE e replay sem outra chamada. Outra execução
sob perfil Gemini verificou 94 testes de contrato/orquestração/retomada.
A [avaliação determinística Gemini](ai06-gemini/deterministico.json) aprovou
125 testes backend, 20 de interface e os 30 cenários SV/SC com estados esperados.
Inclui o contrato nativo Gemini; os testes específicos Groq conservam seu próprio
perfil. Fixtures de domínio suportam as duas representações HTTP para exercitar
a configuração selecionada. Esses testes não enviam dados a LLM real.
[Regressão E2E controlada](ai06-gemini/e2e-controlado.json): oito jornadas
aprovadas em navegador/API/PostgreSQL/SMTP locais, sem chamada de provedor;
rollback confirmado. Não substitui o ensaio real nem encerra TST-01.
Ruff/formato e mypy (224 fontes) aprovados. Sem dependência nova ou migration.

## Reprodução

Com banco academia_test dedicado, E5 local e .env com chave separada, em backend/:

~~~powershell
$env:ACADEMIA_LLM_PROFILE = 'reserva-gemini'
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode deterministic --output ./data/avaliacao/gemini-det-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode real --output ./data/avaliacao/gemini-real-N
uv run --locked --env-file ../.env pytest -o addopts='' tests/ai/test_gemini.py tests/ai/test_gemini_integration.py
# Retornar explicitamente ao padrão após o ensaio:
$env:ACADEMIA_LLM_PROFILE = 'principal'
~~~

Pasta nova em cada execução. Uma retomada explícita pode usar --cases com IDs
não concluídos, seguida de merge de partes da mesma configuração/código.
Não repetir resposta de qualidade falha para escolher outra mais favorável.
O serviço não faz retry; uma nova execução tem nova chave idempotente.
Consolidar somente com amostra completa, revisão vinculada e ensaio determinístico.

O adaptador REST nativo recebe as mesmas mensagens e contextos minimizados,
com saída JSON, sem ferramentas/pesquisa/código/SQL. Timeout, chave ausente, quota,
truncamento, envelope inválido, modelo divergente e ferramentas inesperadas têm
erros controlados, sem publicação. Os tokens de pensamento são contabilizados,
mas pensamentos não são salvos como conteúdo. Ambas as chaves são removidas dos
relatórios e dos processos de teste do navegador/frontend.

A identidade passou a incluir configuração, adaptadores, fábrica e composição de
geração. A consolidação principal anterior agora identifica incompatibilidade com
os hashes atuais, mantendo evidências antigas sem aprovar código novo. Para
concluir AI-06 na implementação atual, executar um conjunto completo consistente
do perfil escolhido, sem juntar os três chats Gemini às fichas antigas da Groq.
