# Partes originais da avaliação AI-06 v4

- [Base](base/relatorio.json): L09 e L13 concluídos; L18 recusado por quota
  na triagem; L23/L24 não executados. Quatro chamadas, 8.437 tokens conhecidos.
- [Retomada 01](retomada-01/relatorio.json): somente L18,L23,L24; triagem de
  L18 concluída, geração recusada por quota; ataques não executados. Duas chamadas,
  1.795 tokens conhecidos; uma falha com consumo desconhecido.

Mesma configuração/código/corpus/modelo. Não se refez L09/L13 nem se substituiu
resposta concluída. A [união atual](../ai06-ensaio-real.json) conserva a falha
anterior, proveniência e consumo de todas as partes. Revisão vinculada à união
não aprova ausência de saída. Não são evidências de modelos v2/v3/Gemini.

Uma retomada posterior usa estes dois relatórios originais mais a nova parte.
O relatório unido é saída de consolidação e não deve entrar como parte original
no modo merge. [Guia e comando](../ai06-enxuto.md).
