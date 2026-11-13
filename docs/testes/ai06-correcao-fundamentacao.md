# Correção de idioma e fundamentação — AI-06

Registro histórico da amostra v2. A [avaliação vigente v4](ai06-enxuto.md)
e o [aceite do MVP](tst01-consolidacao.json) estão aprovados; os resultados
e falhas desta etapa anterior permanecem preservados.

O LLM continua gerando a estrutura da ficha: dias, exercícios existentes,
séries, repetições, carga quando conhecida, cadência, pausas e observações.
O backend valida e publica; o instrutor mantém parecer posterior e alternativa manual.
A correção não troca esse fluxo por uma ficha pronta ou por montagem manual.

## Problemas encontrados
A preparação anterior não indexava o livro escolhido: recuperava definições,
que não sustentavam várias justificativas quantitativas.
O primeiro ensaio com o livro melhorou seleção/doses e idioma, mas o texto livre
ainda apresentava remissões imprecisas e uma comparação inválida entre séries
e sessões em L18. Esse ensaio ficou no [histórico](historico/ai06-2026-11-12-livro-v2/README.md)
e não aprovou AI-06.

## Correções
- Livro Nahas em português incorporado ao catálogo com original/hash/direitos.
- fontTools permite ler suas fontes CFF; política v2 declara as páginas físicas
  83,85,132,133, revisadas visualmente. Sumário da página 8 continua pendente na
  extração integral, sem suprimir erro ou chamar essa extração de completa.
- Duas buscas fixas cobrem prescrição e descanso; contexto final tem até cinco
  trechos, sem agente pesquisador ou novas chamadas LLM.
- Prompt academia-ia-v3 exige português, quantitativos pertinentes e não inventar
  dados de carga/semanas. O texto completo dos trechos é preservado; metadados
  desnecessários ao modelo ficam no backend.
- Após validar plano/diferença de adaptação, o backend apresenta títulos Dia N
  para gerações novas e resumo factual contado a partir dos campos validados.
  Carga null permanece a definir; zero explícito continua zero.
  Explicação livre do modelo não é propagada à ficha/API pública.
- Fontes consultadas, hashes e IDs efetivamente enviados ao modelo permanecem
  rastreáveis. Resumo público não afirma eficácia ou dose comprovada pela fonte.
- Consolidação usa a meta de fundamentação de 0,9 já aprovada, em vez de adicionar
  exigência de 100%. Idioma/unidades/segurança e falhas críticas continuam rígidos.
  Amostra incompleta ou revisão sem vínculo nunca aprova.

Ver [ADR-007](../arquitetura/decisoes/ADR-007-livro-e-fundamentacao.md).
Essas mudanças não dispensam a revisão do artefato publicado, nem aprovam a
saída bruta incorreta do LLM. Chat continua sendo resposta do modelo,
avaliada diretamente contra o contexto de evidências.

## Triagem sem exigências novas
O prompt v3 explicita a política acadêmica já vigente: negativa explícita é
resposta válida; não exige exames, GAQ ou certeza médica absoluta fora do esquema.
Texto novo com sintoma relevante ou contradição continua exigindo atualização
e bloqueio conforme as regras. Ausência ou NAO_SEI nunca vira saudável.
A versão anterior recusou dois perfis completos; seu ensaio permanece no histórico,
sem reaproveitar respostas como avaliação da nova versão.

## Reprodução da indexação do livro
Após importar o catálogo com curador autorizado, obtenha os UUIDs do curador e
da versão BR-NAHAS-001 aprovada. Em backend/, com ambiente/banco/E5 configurados:

~~~powershell
uv sync --locked
uv run --locked --env-file ../.env python -m app.modules.knowledge.ingestion --actor "$curadorId" --version "$versaoLivroId" --selection ../materiais/rag/selecoes/nahas-forca-v1.json --policy ../materiais/rag/politica-livro-v2.json
~~~

A CLI revalida aprovação atual, hash do original, escopo da política e offsets.
A [seleção operacional](../../materiais/rag/selecoes/nahas-forca-v1.json)
coincide com os trechos do [ensaio](ai06-corpus-v2.json).
Somente GERACAO_GERAL é indexada no ensaio; não amplia automaticamente chat/saúde.

## Verificações
Testes cobrem seleção de páginas inválida/ordenada, preservação de número físico,
página ilegível ainda bloqueada, novos fingerprints, consultas fixas, contexto
limitado, ausência de chamadas LLM extras e descarte de justificativa livre.
O ensaio real é uma nova execução explícita, sem replay apresentado como chamada real.
Revisão de chat usa resposta do modelo e fontes; revisão de ficha usa os itens,
resumo e fontes da ficha efetivamente publicada. Saídas brutas ficam em recibos
privados de teste e suas limitações são registradas separadamente.
Não exigir avaliação médica externa para o cenário acadêmico.
Resultados e limitações estão em [comandos](comandos.md), [resumo](historico/ai06-2026-11-12-pre-academico/ai06-resumo.json),
[revisão](historico/ai06-2026-11-12-pre-academico/ai06-revisao-tecnica.json) e [consolidação](historico/ai06-2026-11-12-pre-academico/ai06-consolidacao.json).

## Retomada quando o provedor interrompe o lote
Cada nova rodada é explícita. --cases executa somente IDs solicitados e conhecidos,
em pasta nova. Ela não aprova a amostra inteira por ter menos casos.
--mode merge reúne partes da mesma configuração/código/ambiente e mantém a
tentativa anterior de provedor. Recusa substituir resposta concluída/falha de
qualidade, misturar versões, repetir IDs ou omitir os casos previstos.
Não usa cache de resposta como se fosse chamada real e não faz retry automático.

Exemplo, com o restante determinado pelo relatório interrompido:
~~~powershell
uv run --locked --env-file ../.env python -m tests.ai.evaluation --mode real --cases L14,L15,L16,L17,L18,L19,L20,L21,L22,L23,L24,L25,L26,L27 --output ./data/avaliacao/retomada-N
uv run --locked python -m tests.ai.evaluation --mode merge --part ./data/avaliacao/real-N/relatorio.json --part ./data/avaliacao/retomada-N/relatorio.json --output ./data/avaliacao/unido-N
~~~

O relatório unido permanece sem aceite até consolidar com teste determinístico e
revisão vinculada. Registra consumo de todas as partes, inclusive tentativa
interrompida/consumo desconhecido, separadamente das métricas dos casos concluídos.
Pausas de amostragem não entram na latência do pedido; geração usa 60 s entre
casos no lote para respeitar a janela gratuita, sem alterar o tempo da aplicação.
