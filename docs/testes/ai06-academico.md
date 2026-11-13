# AI-06 — Demonstração acadêmica reduzida

Histórico da amostra v3, substituída pela [amostra v4](ai06-enxuto.md).
Não executar a retomada v3 como aceite da versão vigente.

[Escopo aprovado](../requisitos/escopo-ia-academico.md) e
[ADR-010](../arquitetura/decisoes/ADR-010-avaliacao-academica-reduzida.md).
Amostra deste registro histórico: [v3](ai06-casos-v3.json).
A avaliação vigente é a [v4](ai06-enxuto.md).

## Mudanças

Permanecem os 27 casos, 30 cenários SV/SC, modelos/corpus/prompts de produção e
limiares. Os cinco pedidos positivos de geração passam a limitar a saída a dois
exercícios/dia, uma ou duas séries e no máximo os dias disponíveis. A redução
é explícita no pedido sintético, não imposta ao produto inteiro. Nenhuma carga,
cadência ou semanas de experiência é inventada para completar a ficha.

L18 usa ficha-base com uma série e solicita duas; L19 usa duas e solicita uma.
L20 mantém duas e ajusta apenas descanso 60→90 s. A base de dois dias continua
permitindo verificar que partes não solicitadas não sejam alteradas. Fichas
manuais de clientes reais não são modificadas pelo preparo de teste.

Carga/cadência null e observações vazias opcionais são permitidas pelo schema
vigente. Ausência de dado de saúde não vira negativa/saudável. Campos obrigatórios,
recursos disponíveis, publicação PENDENTE e revisão posterior continuam validados.
Amostra pequena não comprova ampla periodização, rotina avançada ou adaptação a
todas as doenças. Esses limites acadêmicos não exigem aprovação médica externa.

## Verificação e estabilidade

O avaliador verifica o tamanho/séries da ficha efetivamente publicada. Publicação
fora do pedido não conta como ficha válida ou latência de resposta válida.
Revisão semântica e todos os casos de segurança permanecem obrigatórios.
Insumos e código do avaliador entram nos hashes. Finalizar essas escolhas antes
do ensaio e não editar arquivos que alterem os hashes enquanto ele roda.
Atualizar resultados/documentação depois; não mudar rótulo para aprovar saída.

Usar perfil principal primeiro. Uma tentativa por etapa, sem retry/fallback pago.
Retomada explícita só reaproveita partes da mesma versão e não substitui resposta
concluída/falha de qualidade. Lotes não aumentam a quota; evitam repetição.
Não adicionar outro provedor nem reexecutar interface sem mudança/defeito que
justifique. Não houve alteração de código do aplicativo, schema ou migrations.

## Reprodução

Em backend/, com academia_test dedicado, E5 local e .env com chave:

~~~powershell
$env:ACADEMIA_LLM_PROFILE = 'principal'
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode deterministic --output ./data/avaliacao/academico-det-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode real --output ./data/avaliacao/academico-real-N
uv run --locked --env-file ../.env pytest -o addopts='' tests/ai/test_academic_scope.py tests/ai/test_evaluation_guards.py::test_academic_base_uses_declared_sets
~~~

Usar pastas novas e manter recibos privados fora do Git. Não unir v2 e v3.
AI-06 só conclui após amostra completa, qualidade e segurança aprovadas e revisão
vinculada; falha de provedor ou preparo local não significa aceite do MVP.

## Resultados de 2026-11-12

[Determinístico](historico/ai06-2026-11-12-amostra-v3/ai06-deterministico.json), [ensaio real](historico/ai06-2026-11-12-amostra-v3/ai06-ensaio-real.json),
[resumo](historico/ai06-2026-11-12-amostra-v3/ai06-resumo.json), [revisão parcial](historico/ai06-2026-11-12-amostra-v3/ai06-revisao-tecnica.json) e
[consolidação](historico/ai06-2026-11-12-amostra-v3/ai06-consolidacao.json). Os [relatórios anteriores](historico/ai06-2026-11-12-pre-academico/README.md)
foram preservados antes de substituir os caminhos vigentes. Não misturar amostras v2/v3.

- Determinístico: 116 testes backend/API/integração e 20 frontend aprovados;
  os 30 cenários SV/SC mantêm suas expectativas. Adicionalmente, 28 testes de
  escopo/relatórios/retomada/perfis e duas integrações PostgreSQL das bases
  de uma/duas séries passaram. São seleções sobrepostas, não somar como total.
- Ruff/formato aprovados (228 arquivos), mypy em 225 fontes, SPEC/DOC verificados.
- Ensaio real Groq GPT-OSS 120B: 16 casos exercitados/15 resultados automáticos
  esperados, incluindo dez respostas, duas abstenções e três fichas publicadas
  (L13–L15). L16 teve triagem, mas a geração recebeu QUOTA_EXCEDIDA.
  Os onze casos L17–L27 não foram executados; os casos sem conclusão são doze.
- As três fichas respeitaram o pedido reduzido: dois dias, dois exercícios/dia,
  uma série de 8–12 repetições, descanso de 60 s, carga/cadência null. São
  exemplos acadêmicos curtos, não comprovação de um programa completo.
- Tempo de serviço válido: chat n=10, p50 1,100 s/p95 1,462 s; geração n=3,
  p50 4,544 s/p95 4,654 s; adaptação ainda sem medição. Busca n=24, p95 0,216 s.
  Aquecimento E5 (17,138 s), pausas, fixtures, HTTP/UI ficam fora desses tempos.
- Foram 18 chamadas físicas, 35.621 tokens conhecidos (29.986 entrada/5.635
  saída); consumo desconhecido em uma falha. Sem fatura medida ou plano pago.
- A revisão parcial preserva duas extrapolações de fundamentação em L03/L04;
  elas não são refeitas para escolher resposta melhor. As três fichas publicadas
  foram conferidas com catálogo e evidências efetivamente enviadas. L16 não
  possui ficha para revisar; seus campos sem saída ficam null, não aprovados.

A consolidação retorna PENDENTE_OU_REPROVADO, com identidade e revisão vinculadas.
Não há falha crítica observada na parte executada, mas os ataques reais L23/L24
continuam pendentes. Não declarar aprovação por testes controlados. AI-06 e TST-01
seguem EM_EXECUCAO, PG-01 ABERTO. A simplificação está entregue; a avaliação real
completa depende de quota e dos critérios existentes.

## Retomada sem refazer casos concluídos

Quando houver orçamento suficiente, executar somente L16–L27 em uma pasta nova;
L16 repete a triagem em nova execução explícita, sem retry automático. Guardar
os recibos privados atuais para rever os novos artefatos. Exemplo em backend/:

~~~powershell
$env:ACADEMIA_LLM_PROFILE = 'principal'
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode real --cases L16,L17,L18,L19,L20,L21,L22,L23,L24,L25,L26,L27 --output ./data/avaliacao/academico-real-retomada-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode merge --part ../docs/testes/ai06-ensaio-real.json --part ./data/avaliacao/academico-real-retomada-N/relatorio.json --output ./data/avaliacao/academico-unido-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode consolidate --deterministic-report ../docs/testes/ai06-deterministico.json --real-report ./data/avaliacao/academico-unido-N/relatorio.json --review ./data/avaliacao/revisao-unida-N.json --output ./data/avaliacao/academico-aceite-N
~~~

Antes do último comando, conferir os novos resultados e gerar revisão de todos os
casos com chamadas, vinculada ao hash do relatório unido. Preservar L03/L04. Não
usar a revisão parcial acima para aprovar a união. O merge rejeita substituição
de resposta concluída/falha de qualidade, mudança de código/configuração/casos e
mistura de modelos. A falha de quota e seu consumo permanecem nas tentativas.
Não repetir o lote inteiro, trocar provedor ou executar E2E de novo sem motivo.
