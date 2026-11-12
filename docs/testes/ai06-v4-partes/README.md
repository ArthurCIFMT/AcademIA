# Partes originais da avaliação AI-06 v4

- [Base](base/relatorio.json): L09 e L13 concluídos; L18 recusado por quota
  na triagem; L23/L24 não executados. Quatro chamadas, 8.437 tokens conhecidos.
- [Retomada 01](retomada-01/relatorio.json): somente L18,L23,L24; triagem de
  L18 concluída, geração recusada por quota; ataques não executados. Duas chamadas,
  1.795 tokens conhecidos; uma falha com consumo desconhecido.

- [Retomada 02](retomada-02/relatorio.json): L18,L23,L24 concluídos, quatro
  chamadas/8.705 tokens conhecidos; zero falhas de provedor/consumo desconhecido.
  [Cabeçalhos sanitizados](retomada-02/limites-http.json), sem chamada extra.

Mesma configuração/código/corpus/modelo. Não se refez L09/L13 nem se substituiu
resposta concluída. A [união atual](../ai06-ensaio-real.json) conserva a falha
anterior, proveniência e consumo de todas as partes. Revisão vinculada à união
não aprova ausência de saída. Não são evidências de modelos v2/v3/Gemini.

A união atual contém as três partes e está tecnicamente completa. A revisão
vinculada/consolidação aprovou a amostra acadêmica v4. São sete chamadas nos
resultados selecionados/17.142 tokens conhecidos; dez chamadas/18.937 tokens
conhecidos e dois consumos desconhecidos incluindo as duas recusas antigas.
Não repetir casos concluídos ou unir modelos/versões. Relatório unido não é
parte original de uma futura união. [Guia e limites](../ai06-enxuto.md).
