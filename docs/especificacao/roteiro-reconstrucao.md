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

## Decisões ainda abertas no escopo posterior

| Tema | Definido | Falta fechar antes da capacidade dependente |
|---|---|---|
| Reserva de aulas | Agenda básica; capacidade só se reservas forem oferecidas | GATE-07: escopo opcional e regras de reserva/exceção |
| Biometria | CompreFace e reconhecimento por captura real; similaridade inicial 0,95 não é acurácia de 95% | GATE-08: instância/versão, hospedagem, contrato e ensaio real |
| Matrícula/acesso | Atendente matricula sem pagamento obrigatório; conta/matrícula/modalidade/limites são validados | GATE-08: parâmetros da janela e limites do plano, alternativa manual e integração concreta |
| Catraca | API externa fictícia; comando aceito não é passagem | GATE-08: autenticação, contrato final de comando/retorno e demonstração integrada |
| Pagamentos automáticos | Fase tardia e independente da matrícula acadêmica | GATE-09: provedor/sandbox, callbacks e regras específicas |
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
