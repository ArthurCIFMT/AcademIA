# AI-06 — Cinco cenários reais e até quatro exercícios por dia

[ADR-011](../arquitetura/decisoes/ADR-011-amostra-real-minima.md),
[escopo aprovado](../requisitos/escopo-ia-academico.md) e [amostra v4](ai06-casos-v4.json).
Quatro refere-se aos exercícios de uma ficha/dia, não ao número de dias.

| Caso real | Finalidade | Limite de chamadas LLM |
|---|---|---|
| L09 | Dúvida em português com resumo em inglês | 1 |
| L13 | Gerar ficha: até quatro exercícios/dia, preferir quatro viáveis, 1–2 séries | 2 (triagem + geração) |
| L18 | Adaptar somente o dia 1 de uma para duas séries | 2 (triagem + adaptação) |
| L23 | Tentar instrução indevida na mensagem do chat | 1 |
| L24 | Recuperar documento sintético com instrução indevida | 1 |

Total: cinco cenários, até sete chamadas. Os 30 cenários locais SV/SC e oito
perfis continuam; testes unitários/integração usam modelos controlados e não
gastam quota LLM. E5 e Qdrant são locais. Segurança, saúde ausente, equipamentos,
15 versões, isolamento e fluxo manual não foram removidos. Fontes PT/EN e
conteúdo efetivamente enviado continuam sujeitos a revisão, não só schema JSON.

Geração prefere quatro exercícios por dia quando viáveis, com ou sem equipamento
conforme o catálogo. Carga/cadência podem ficar a definir. Os dias vêm da
disponibilidade do onboarding. Ficha-base de adaptação mantém dois dias/um
exercício cada para verificar preservação; é uma fixture manual, não um programa
completo do LLM. Editor manual e limites gerais do produto não foram alterados.

As [evidências v3](historico/ai06-2026-11-12-amostra-v3/README.md), inclusive as
extrapolações L03/L04, permanecem históricas; a redução não as corrige. Não juntar
casos de versões/modelos distintos. Um ensaio pequeno não comprova cobertura
clínica ampla ou benchmark robusto. Registrar n e percentis descritivos.

## Reprodução

Em backend/, PostgreSQL academia_test dedicado, pesos E5 e .env local:

~~~powershell
$env:ACADEMIA_LLM_PROFILE = 'principal'
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode deterministic --output ./data/avaliacao/enxuto-det-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode real --output ./data/avaliacao/enxuto-real-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode consolidate --deterministic-report ./data/avaliacao/enxuto-det-N/relatorio.json --real-report ./data/avaliacao/enxuto-real-N/relatorio.json --review ./data/avaliacao/revisao-enxuto-N.json --output ./data/avaliacao/enxuto-aceite-N
~~~

Revisar as cinco saídas e fontes antes do último comando; vincular a revisão
ao hash canônico do relatório real. Saída/recibo privado não entra no Git. Não
repetir caso concluído para escolher resposta melhor. Quota/indisponibilidade
interrompe o lote; uma retomada explícita pode selecionar apenas IDs pendentes
ou com falha de provedor. Nunca executar os 27 casos antigos para a versão v4.

## Troca automática de LLM

É tecnicamente possível usar uma cadeia gratuita Groq→Gemini por recusa de quota,
com uma troca no máximo, registro de modelo/consumo e validações iguais. Não
trocar por bloqueio de saúde, ausência de evidência ou JSON inválido. Quota de
outra API também pode acabar; falta de reserva encerra com erro controlado.
As chaves já configuradas não garantem disponibilidade ou qualidade equivalente.

A implementação atual ainda escolhe um perfil explicitamente; esta entrega não
ativa fallback. Tal mudança precisa alterar o contrato de tentativas e a
persistência/idempotência antes de ser usada. Cada candidato é avaliado em seu
próprio lote v4, sem completar a avaliação de um modelo com saídas de outro.
Não contratar faturamento nem acrescentar provedores automaticamente.

## Resultados de 2026-11-12

[Determinístico](ai06-deterministico.json), [ensaio real](ai06-ensaio-real.json),
[resumo](ai06-resumo.json), [revisão parcial](ai06-revisao-tecnica.json) e
[consolidação](ai06-consolidacao.json).

- 117 testes backend/API/integração e 20 frontend passaram no runner local, com
  os 30 cenários esperados. Seleção relacionada: 29 testes aprovados; verificação
  adicional PostgreSQL/Qdrant/E5 sem LLM aprovada. Seleções se sobrepõem.
- O primeiro teste novo confundiu idioma primário do PDF (pt-BR) com idioma do
  resumo em inglês. A conferência passou a usar hash/texto do resumo selecionado;
  fonte, índice, limiar e implementação da busca não foram alterados.
- L09 respondeu em português com o resumo EN efetivamente enviado, em 1,667 s.
- L13 publicou dois dias com quatro exercícios por dia, uma série de 10–12,
  pausas 60 s, carga/cadência null; recursos de peso corporal e equipamentos
  disponíveis. Tempo de serviço 5,813 s; revisão confirma faixas gerais do
  livro/contexto enviado, catálogo e limite acadêmico sem prometer programa completo.
- L18 foi recusado por QUOTA_EXCEDIDA na triagem, sem adaptação publicada;
  L23/L24 não foram executados. Reduzir a amostra não repõe a quota já consumida.
- Foram quatro chamadas físicas, 8.437 tokens conhecidos (6.317 entrada/2.120
  saída) e uma chamada com consumo desconhecido. Nenhum retry ou fallback.
  Busca n=5, p95 0,099 s. Sem fatura medida ou contratação de plano pago.
- São duas saídas válidas revisadas. Falha de provedor fica com campos de
  revisão null; não é qualidade aprovada. Nenhuma falha crítica observada nesta
  parte; ataques reais continuam pendentes.

A consolidação retorna PENDENTE_OU_REPROVADO: identidade/revisão vinculadas, mas
sem amostra completa, adaptação/ataques reais e medições correspondentes. AI-06
e TST-01 EM_EXECUCAO; PG-01 ABERTO. Não misturar esses resultados com v3/Gemini.

Quando houver quota suficiente, retomar somente L18,L23,L24 em pasta nova.
São até quatro chamadas novas; L09/L13 não são refeitos. Em backend/:

~~~powershell
$env:ACADEMIA_LLM_PROFILE = 'principal'
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode real --cases L18,L23,L24 --output ./data/avaliacao/enxuto-retomada-N
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode merge --part ../docs/testes/ai06-ensaio-real.json --part ./data/avaliacao/enxuto-retomada-N/relatorio.json --output ./data/avaliacao/enxuto-unido-N
~~~

Revisar somente as saídas novas, mantendo as justificativas de L09/L13, e gerar
revisão completa vinculada ao relatório unido antes da consolidação. A falha
de quota permanece nas tentativas; união recusa sobrescrever resposta concluída.
Não repetir o lote inteiro ou testar novos provedores automaticamente.
