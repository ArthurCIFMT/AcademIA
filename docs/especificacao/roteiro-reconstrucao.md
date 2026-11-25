# Roteiro para reconstrução por prompts

Este roteiro é parte da especificação. Em uma reconstrução nova, use a sequência
funcional e as dependências aqui incorporadas; os estados CONCLUIDO do projeto
de origem não significam que a outra implementação já possui essas entregas.
Para continuar o repositório atual, preserve as entregas existentes e consulte
o estado corrente no manifesto.

## Preparar a nova execução

- Definir o objetivo: reproduzir o estágio manual já entregue ou executar todo
  o MVP/escopo final especificado.
- Criar AGENTS.md com as regras de trabalho incorporadas neste SPEC, estabelecer
  repositório e ambiente e registrar decisões/pendências antes do módulo afetado.
- Reutilizar RF/RN/RNF/MRF e IDs de etapas. Não transformar recomendações antigas
  do MER em regras que contrariem decisões posteriores aprovadas.
- Usar uma entrega pequena por prompt. Cada entrega tem dados, serviço, API,
  tela quando prevista, testes proporcionais e documentação.
- Consultar visão geral/invariantes e os capítulos específicos do cartão.
  O arquivo é completo para transporte; não é necessário colocar todos os
  capítulos na janela de contexto de cada tarefa.
- Ao recriar a partir de um único SPEC, criar os documentos especializados
  necessários a partir dos capítulos incluídos, preservando conteúdo/IDs,
  antes de criar referências para arquivos ainda inexistentes.
- Separar corpus e dados sintéticos de teste. Download de literatura e pesos,
  credenciais de serviços e serviços locais devem ser provisionados no ambiente.

## Modelo de prompt mestre de planejamento

```text
Tarefa: elaborar o plano de desenvolvimento do AcademIA a partir do SPEC anexado.
Não implementar código nesta execução.
Meta: [reproduzir estágio atual / construir MVP / implementar fase explicitada].
Leia a visão geral, fontes/precedência, módulos, fluxos e decisões técnicas.
Identifique requisitos e critérios, dependências, contratos, dados e pendências.
Mantenha backend Python, frontend React/TypeScript, PostgreSQL e fronteiras JSON.
Respeite o escopo acadêmico e as regras de IA, equipamentos, retenção e matrícula.
Saída: arquitetura, módulos, sequência de prompts pequenos com IDs estáveis,
dependências/gates, aceite e testes por etapa, dúvidas materiais e próxima etapa.
```

## Modelo de prompt operacional

```text
Tarefa: implementar [ID — capacidade].
Contexto: SPEC [capítulos] e requisitos [IDs], ADRs e contratos pertinentes.
Dependências concluídas: [IDs e evidências].
Escopo permitido: [arquivos/pastas ou equivalentes justificados].
Fora de escopo: [capacidades/áreas que não pertencem à entrega].
Entregáveis: [dados/migration, serviço, API/JSON, tela, testes, documentação].
Critérios de aceite: [cenários observáveis derivados dos critérios aprovados].
Testes: [comandos reais do ambiente e cenários de sucesso, falha e autorização].
Se houver falha, corrigir no escopo; registrar impedimento externo objetivamente.
Não inventar requisito, fonte RAG, resultado de teste ou credencial.
Atualizar especificação afetada/rastreabilidade e registrar evidências.
Git: seguir autorização do responsável para commit/publicação.
Resposta: resultado, arquivos, testes/resultados, pendências e próximo passo.
```

O prompt operacional remete à especificação. A nova IA deve propor refinamento
quando faltar informação material, distinguindo proposta, decisão aceita e teste
executado. A redução de uma tarefa por contexto não elimina seus critérios.

## Decisões e pré-condições do escopo posterior

| Tema | Definido | Falta fechar antes da capacidade dependente |
|---|---|---|
| Reserva de aulas | Agenda básica; capacidade só se reservas forem oferecidas | GATE-07: escopo opcional e regras de reserva/exceção |
| Biometria | [GATE-08](../arquitetura/preparacao-gate-08.md) fechado com CompreFace 1.2.0 e FaceNet. Limiar inicial de similaridade 0,95 | Integração e ensaio do fluxo completo em ACS-01/02 |
| Matrícula/acesso | Matrícula pelo atendente sem pagamento obrigatório, limite diário, renovação sem sobreposição e identificação manual sob as mesmas regras | MEM-01 implementa os planos e as matrículas. ACS-03/04 implementam autorização e alternativa manual |
| Catraca | API externa fictícia com contrato de comando e passagem definido no GATE-08 | Implementação em ACS-07 e integração em ACS-03/05 |
| Financeiro simulado | GATE-09: simulação local independente da matrícula | Implementar compra simulada e indicadores em FIN-02/03 |
| IA/RAG real | Modelos/configuração/corpus iniciais definidos | Provisionar recursos e executar avaliação de relevância, qualidade e latência nos cartões próprios |

Essas pendências não impedem a reconstrução do fluxo manual nem as etapas
independentes do MVP. Não declarar integração real aprovada só por usar mocks.

## Critério de equivalência da reconstrução

A nova implementação deve satisfazer os mesmos critérios de comportamento,
autorização, integridade, retenção e contratos. Não precisa repetir decisões
incidentais do código linha a linha. A reprodução exata de dependências/código
usa o commit e os lockfiles do projeto original.

Rascunho manual aceita até 7 dias e 30 itens/dia, com séries 1–100; o contrato
inicial de geração por IA é mais restrito, conforme a configuração incorporada:
até 6 dias, 6 itens/dia e séries 1–10. Os dois limites têm finalidades diferentes.
Uma geração válida precisa passar também pelo contrato de publicação; não ampliar
silenciosamente o limite do gerador para o limite de armazenamento/editor.

Use dados sintéticos para testar instalação, cadastro, designação, onboarding,
prescrição manual, publicação PENDENTE, consulta/exportação, parecer/expurgo,
recursos indisponíveis e isolamento. Para o MVP completo, executar também os
cenários de RAG/IA e TST-01 antes de declarar sua conclusão.

## Reformulação visual incremental

Após reproduzir o MVP funcional, executar UX-01–UX-09 conforme o manifesto e os
cartões incorporados. Não tratar CSS/acabamento como consequência automática de
outros prompts. A especificação de experiência traz RNF-19/RNF-20, jornadas,
limites e critérios mensuráveis; UX-01 materializa a referência visual antes da
migração das telas. No repositório atual, UX-09 já concluiu a trilha e o
manifesto indica os próximos cartões elegíveis.

Cada entrega mantém componentes comuns, contratos, autorizações e estados reais.
UX-09 comprova as telas existentes em navegador; telas de módulos posteriores
devem aplicar o mesmo padrão com evidência própria antes da validação final.
Não confundir representação gráfica, implementação e aprovação: reportar quais
foram feitas, com fixtures sintéticas, resultados e limitações. Nenhuma mudança
de MER, banco, políticas clínicas ou fornecedor de IA é exigida pelo redesenho.

## Operação local reproduzível durante a evolução

Reproduzir também o início/encerramento local com dois cliques descrito no
[guia do iniciador](../instalacao/iniciar-com-dois-cliques.md). No Windows,
Iniciar AcademIA.cmd e Encerrar AcademIA.cmd são as entradas públicas; caminhos
privados ficam fora do Git e o setup inicial continua explícito.

Manter a compatibilidade desse caminho em cada implementação que afetar a
execução. AGENTS.md e o contrato comum autorizam os ajustes estritamente
necessários ao iniciador, configurações de exemplo, testes e documentação,
sem exigir novo pedido do responsável. Não antecipar serviços de cartões
futuros nem colocar reset/migration/seed silencioso no ato de abrir o sistema.
Alteração do ciclo exige sua verificação; documentação ou etapa sem impacto
registra essa situação sem reexecutar serviços/LLM desnecessariamente.
