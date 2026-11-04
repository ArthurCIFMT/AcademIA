# Revisão documental dos prompts

## Atualização: equipamentos no MVP, retenção e macrorequisitos completos

Verificação documental de 2026-11-04 após as decisões do responsável:

- 15 MRFs em tabela com descrição, atores, módulos e 75 critérios identificados.
- RF-01–RF-37 preservados; RN-37/RN-38/RN-39 registram recursos, retenção e idioma.
- 61 cartões operacionais; grafo sem ciclos e metadados coerentes com manifesto
  e rastreabilidade. EQP-01 é MVP e precede catálogo/geração/aceite integrado.
- Links locais, whitespace e integridade do MER e dos 18 PDFs conferidos.
- Testes de aplicação não executados: esta entrega é documental e os projetos
  executáveis ainda não estão configurados. Cenários novos estão nos cartões.

Os registros abaixo documentam revisões anteriores e não fecham gates atuais.

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
- Matrícula pelo atendente sem pagamento obrigatório; substitui a pré-condição
  financeira da revisão anterior por correção explícita do responsável.
- API facial real proposta, com catraca externa fictícia; aceite facial não usa só mock.
- MEM-00 é financeiro tardio/opcional e não é dependência de MEM-01; ACS-07 mantém
  catraca fictícia. Manifesto, dependências e rastreabilidade atualizados.
- Verificação executada: 86 documentos, 61 cartões/entradas no manifesto e 455
  links locais válidos; seções obrigatórias e dependências coerentes, sem ciclos.
- IDs únicos confirmados: 37 RFs, 36 RNs, 17 RNFs e 15 MRFs.
- git diff --check passou; hash SHA-256 do PNG original preservado.
- Nenhum teste de aplicação executado: documentação e prompts não implementam módulos.
