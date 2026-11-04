# Revisão documental dos prompts

## Objeto da revisão

Pacote de planejamento AcademIA: mestre, contexto, contrato, 61 cartões,
manifesto e estratégia de testes. Esta revisão não executa os cartões nem testa
uma aplicação implementada.

## Verificações da versão anterior

- Mestre de planejamento: 39 linhas e saída limitada a 40 linhas.
- Cartões: 59 arquivos e 59 entradas correspondentes no manifesto.
- Cada cartão possui dependências, módulos/requisitos, aceite e testes.
- IDs/referências de dependência são resolvíveis e não possuem ciclos entre cartões.
- Caminhos Markdown relativos apontam para arquivos existentes.
- Numeração preservada: 35 RFs, 36 RNs, 17 RNFs e 15 MRFs.
- Testes de aplicação continuam pendentes de implementação/configuração.
- Docker depende do aceite do MVP e da maioria dos módulos.
- Diff revisado com git diff --check, incluindo arquivos novos depois do stage.

## Revisão ampliada posterior

O responsável solicitou um mestre completo e análise dos módulos/MER. O limite
didático de 40 linhas foi removido; a contagem anterior é evidência histórica,
não restrição atual. Os 59 cartões foram mantidos.

- Módulos: cobertura suficiente, com refinamentos de ownership e fluxo.
- Mestre: fluxos, estados, fontes, testes, marcos, gates e saída detalhados.
- Cartões afetados: bootstrap/primeiro acesso, atualidade da proposta e
  dependência da interface de notificações.
- MER: análise em relatório separado; o PNG/XML original permanece inalterado.
- Verificações atuais: links, IDs, correspondência manifesto/cartões,
  dependências/ciclos, diff e hash do MER.

## Limitações conhecidas

Os comandos BE/INT/API/FE/E2E/DB/RAG/IA/INF ainda serão configurados pelos prompts
responsáveis. Ferramentas, corpus, fornecedores e políticas clínicas pendentes
impedem executar os módulos afetados; não impedem revisar estes documentos.
MRF08–MRF15 continuam derivados sujeitos a aceite. AUL-02 continua opcional.

O manifesto guarda o estado da execução de cada tarefa, independentemente da
existência deste relatório de revisão.

## Atualização de treino, matrícula e biometria

Pacote atual: 61 cartões, 37 RFs, 36 RNs, 17 RNFs e 15 MRFs.
As contagens anteriores neste relatório são históricas.

- Publicação e parecer profissional separados; consulta/chat antes do aceite.
- Matrícula pelo atendente após confirmação de pagamento, manual inicialmente.
- API facial real proposta, com catraca externa fictícia; aceite facial não usa só mock.
- MEM-00 e ACS-07 acrescentados; manifesto, dependências e rastreabilidade atualizados.
- Verificação executada: 86 documentos, 61 cartões/entradas no manifesto e 455
  links locais válidos; seções obrigatórias e dependências coerentes, sem ciclos.
- IDs únicos confirmados: 37 RFs, 36 RNs, 17 RNFs e 15 MRFs.
- git diff --check passou; hash SHA-256 do PNG original preservado.
- Nenhum teste de aplicação executado: documentação e prompts não implementam módulos.
