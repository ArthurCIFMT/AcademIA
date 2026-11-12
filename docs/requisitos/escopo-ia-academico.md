# Escopo acadêmico das demonstrações de IA

Aprovado pelo responsável em 2026-11-12: exemplos mais simples, menos séries,
campos não essenciais a definir e menos retrabalho na avaliação.

## O que simplificar

A amostra de demonstração usa fichas curtas, com até dois exercícios por dia e
uma ou duas séries por exercício nos casos positivos de geração. Os dias não
excedem a disponibilidade declarada. É um recorte de teste, não uma dose clínica
universal, nem uma mudança dos limites do produto ou das fichas manuais.
O catálogo sintético continua reduzido; não afirmar que a ficha reproduz o
programa completo do livro ou garante hipertrofia/força/desempenho individual.

Carga individual e cadência podem ficar explicitamente null/a definir. Não
inventar esses dados para preencher o formulário. Observações opcionais podem
ficar vazias. Isso já é permitido pelo contrato JSON vigente; não remover campos
obrigatórios do schema, IDs de exercício, recursos, séries, repetições ou pausas.

As adaptações demonstram apenas aumentar de uma para duas séries, reduzir de
duas para uma e ajustar descanso de 60 para 90 segundos, preservando os demais
campos/dias. A faixa inicial de uma/duas séries é compatível com os trechos
selecionados do livro Nahas; conferir também a população e finalidade reais da
fonte na revisão. Não exigir progressão para quatro séries de um iniciante
sem suporte específico. Alteração por doença/lesão continua exigindo evidência
pertinente; sem suporte, abster-se em vez de inventar adaptação clínica.

## O que continua obrigatório

Autenticação, autorização, isolamento entre clientes, bloqueio de casos graves,
tratamento de ausências/incerteza de saúde, português e evidências verdadeiras.
Ausência não significa saudável, zero ou média. Permanecem a validação de
catálogo/equipamentos, versionamento/retenção, parecer posterior, fluxo manual,
limites de chamadas, resistência a instruções indevidas e testes de contratos.
Não exigir laudo ou aprovação médica externa para a demonstração.

## Avaliação e retrabalho

A [amostra v3](../testes/ai06-casos-v3.json) conserva 27 casos e os 30 cenários
SV/SC. Reduz o tamanho das fichas e corrige a progressão de L18; não elimina
segurança nem converte falha antiga em aprovação. V2 e relatórios anteriores
continuam históricos. Metas de qualidade/latência e tolerância zero de segurança
não foram reduzidas. Ficha publicada fora do pedido reduzido não conta como válida.

Usar primeiro o perfil principal GPT-OSS 120B, já escolhido; não adicionar outro
provedor nesta entrega. Finalizar testes locais e fixar código/configuração/casos
antes da chamada real. Relatórios guardam hashes dos insumos e do avaliador.
Retomar somente falhas de provedor/itens não exercitados na mesma versão, sem
repetir resposta concluída para escolher outra melhor e sem retry automático.
Não executar novamente interface/instalação ou mudar prompts de produção quando
somente a amostra de avaliação mudou. Reexecutar o necessário se surgir defeito.

A simplificação não garante quota/disponibilidade, nem aprova automaticamente
AI-06. Referências: [AI-06](../prompts/05-ia-rag/AI-06.md),
[configuração](configuracao-ia-rag.md) e [avaliação didática](../testes/ai06-academico.md).
