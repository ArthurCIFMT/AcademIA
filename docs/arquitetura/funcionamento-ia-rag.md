# Funcionamento previsto da IA/RAG

Atualização de 2026-11-04: especificação de equipamentos no MVP, retenção e idioma.
Este documento descreve o sistema a implementar; não representa código executado.

A [tabela completa dos 15 macrorequisitos](../requisitos/macrorequisitos-ia-rag.md)
é a fonte canônica de descrição, atores, módulos e 75 critérios identificados.
MRF08–MRF15 continuam derivados nos pontos sem aprovação formal; políticas clínicas,
formulário definitivo, responsáveis e provedores permanecem em GATE-04.

## Percurso de uma solicitação

1. Administrador mantém os equipamentos cadastrados, ativos e operacionais.
2. Backend autentica/autoriza cliente e obtém snapshot do onboarding/ficha vigente.
3. Validar dados e executar triagem conforme política revisada; dado ausente não
   significa saudável nem valor médio. Formulário concluído não dispensa triagem.
4. Recuperar evidências aprovadas para condição/objetivo e filtrar catálogo pelos
   recursos disponíveis. Falta de suporte para adaptação por saúde exige abstenção.
5. Biomecânica seleciona candidatos viáveis, periodização organiza sessões e
   prescrições, regras por código e revisor verificam a proposta.
6. Revalidar contexto, versão-base e disponibilidade antes de publicar; backend
   publica com parecer PENDENTE, aplica retenção de 15 e registra evidências.
7. Cliente consulta/conversa em português antes do aceite. Instrutor designado
   recebe aviso/fila e avalia depois, sem contornar bloqueio ou falta de evidência.

Inventário vem do PostgreSQL/MOD-10; literatura vem do banco vetorial/MOD-05.
Combinação exige todos os recursos e alternativa deve estar completa; peso
corporal exige dispensa explícita. Dados de exemplo ficam para a implementação.

## Retenção e fichas rejeitadas

| Evento | Efeito confirmado |
|---|---|
| A vigente é rejeitada | A continua consultável com motivo e chat enquanto retida. |
| B posterior é publicada | B começa PENDENTE e é a vigente; A pode permanecer no histórico dentro do limite. |
| B é rejeitada | Excluir conteúdo/itens da rejeitada anterior A; B permanece consultável enquanto retida. |
| Publicar a 16ª versão completa | Excluir conteúdo mais antigo até restarem 15, incluindo vigente, independentemente do parecer. |
| Versão antiga aceita/rejeitada ultrapassa limite | Pode expirar por RF-17 sem esperar novo parecer ou nova rejeição. |
| Falha, replay ou publicações concorrentes | Não eliminar vigente, duplicar exclusão, ultrapassar limite ou reutilizar número de versão. |

Contam-se versões publicadas completas, manuais ou geradas/adaptadas por IA;
rascunhos e tentativas não publicadas não contam. A regra específica de rejeitadas
pode deixar menos de 15. Guardar metadados de identificação, autor, parecer,
datas e motivo da exclusão e preservar registros/snapshots de treinos executados
existentes, sem reexpor conteúdo como ficha consultável. Isso não exige criar
agora um módulo de execução de treino nem promete limitar todo o banco a 15 registros.

Conteúdo excluído não retorna em API/exportação ou contexto ativo/cache do chat.
Conversa passada não é reescrita, mas não restaura automaticamente uma prescrição
excluída. Publicação/limpeza são atômicas/idempotentes e a numeração é crescente.

## Idioma

Preferir português na curadoria; fontes estrangeiras podem ser recuperadas.
Prescrições, chat e explicações ao usuário são em português, com evidência original
identificada. Avaliar recuperação PT/EN, sentido, unidades e negações; tradução
não é aprovação clínica automática. Não houve tradução/regravação dos PDFs nesta entrega.

## Biometria e infraestrutura

CompreFace é integração separada da IA de treino e do corpus vetorial. Matrícula
pelo atendente não exige pagamento. Hospedagem/versão e execução do CompreFace
antes da fase final de Docker ainda precisam de GATE-06/GATE-08.

## Referências e verificação

- [RFs](../requisitos/requisitos-funcionais.md) e [RNs](../requisitos/regras-de-negocio.md).
- [Módulos](modulos.md), [decisões](decisoes-iniciais.md) e [fluxos](fluxos-atualizados.md).
- [Manifesto](../prompts/README.md) e [testes](../testes/estrategia.md).
- [Acervo bibliográfico](../../materiais/rag/README.md).

Esta entrega é documental. Conferir IDs/links, consistência de dependências/aceites,
integridade do MER e materiais, e whitespace. Testes de aplicação só serão
executados quando os módulos forem implementados; novos cenários estão nos cartões.
