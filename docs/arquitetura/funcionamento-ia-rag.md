# Funcionamento previsto da IA/RAG

Atualização de 2026-11-04: decisões do responsável incorporadas à especificação.
Este documento descreve o sistema a implementar; não representa módulo executado.
MRF08–MRF15 continuam derivados; apenas os refinamentos expressamente autorizados
foram incorporados, sem aprovação automática de todos os detalhes pendentes.

## Macrorequisitos e execução

| ID | Capacidade | Como funciona | Resultado/controle |
|---|---|---|---|
| MRF01 | Ingestão documental | Recebe fontes revisadas, extrai texto preservando unidades, divide em blocos e gera embeddings. | Texto/vetor ligados a fonte, versão, página/seção e hash; falha pode ser retomada. |
| MRF02 | Recuperação semântica | Busca no banco vetorial especializado com consulta minimizada, top-K e filtros do corpus aprovado. | Trechos pertinentes e pontuações; busca vetorial p95 ≤ 2 s no ensaio definido. |
| MRF03 | Perfil/anamnese | Valida e versiona os dados declarados pelo cliente no onboarding. | Snapshot identificado em JSON nas fronteiras; não inventa dados ausentes. |
| MRF04 | Orquestração | Coordena triagem → biomecânica → periodização → revisor, com regras intermediárias. | Estado, timeout, tentativas e ciclos limitados; agentes não publicam diretamente. |
| MRF05 | Geração delimitada | Seleciona exercícios do catálogo e propõe volume/intensidade conforme restrições e evidências recuperadas. | JSON estrito; adaptação por saúde sem suporte pertinente não é gerada. |
| MRF06 | Revisão automática | Verifica inconsistências e devolve correções ao orquestrador dentro do limite de ciclos. | Somente conteúdo tecnicamente validado pode ser publicado; não concede aceite do instrutor. |
| MRF07 | Entrega da ficha | API/interface apresenta dias, exercícios, prescrições e parecer separado. | Cliente consulta/exporta a própria ficha antes do aceite; última rejeitada permanece disponível. |
| MRF08 | Triagem de elegibilidade | Analisa informações declaradas e política estruturada de bloqueio. | Grave bloqueado, dados insuficientes ou necessidade de avaliação não gera ficha; não é diagnóstico. |
| MRF09 | Restrições por código | Filtra seleção e valida novamente catálogo, restrições e limites após geração. | Proibição não é revogada por texto da IA, score ou aceite do instrutor. |
| MRF10 | Parecer posterior | Instrutor designado aceita/rejeita a versão; edição cria outra versão. | Responsável/data/motivo; nova rejeitada exclui conteúdo da rejeitada anterior conforme RF-35. |
| MRF11 | Evidência rastreável | Relaciona adaptação à saúde com trecho recuperado aplicável à condição, população e intervenção. | Sem evidência suficiente ou com conflito não resolvido: abstenção obrigatória, sem publicação. |
| MRF12 | Isolamento | Backend autoriza contexto, mensagens, ficha e onboarding de um cliente por execução. | Não mistura clientes; dados pessoais não integram literatura compartilhada. |
| MRF13 | Avaliação da IA | Executa consultas e casos rotulados, separados do conhecimento indexado. | Mede recuperação, aderência, bloqueios, isolamento, JSON e latência; mocks não aprovam modelo real. |
| MRF14 | Chat/adaptação | Conversa usa contexto autorizado; nova dor/limitação reabre triagem e busca evidências. | Adaptação válida cria versão PENDENTE; abstenção não muda a ficha e conteúdo excluído não volta ao contexto ativo. |
| MRF15 | Governança do corpus | Controla quarentena, aprovação, versões e revogação dos documentos. | Download não é aprovação; instruções em documentos não governam os agentes. |

## Percurso de uma solicitação

1. Autenticar/autorizar cliente e obter snapshot do onboarding e da ficha vigente.
2. Validar dados obrigatórios e executar triagem conforme política revisada.
3. Se elegível, recuperar evidências do corpus aprovado para o caso e objetivo.
4. Para adaptação por saúde, conferir suporte pertinente: score alto e menção à
   doença sozinhos não bastam. Na ausência de suporte, abster-se sem gerar ficha.
5. Biomecânica seleciona exercícios compatíveis; periodização organiza sessões e
   prescrições; código valida restrições/catálogo/faixas e o revisor procura falhas.
6. Dentro dos limites de correção, validar saída e versão-base; backend publica
   uma versão com parecer PENDENTE e registra as fontes utilizadas.
7. Cliente já pode consultar e conversar. Instrutor designado recebe aviso/fila e
   avalia depois; sua decisão não substitui evidência nem contorna bloqueio.

A aprovação de um documento para RAG, a validação automática de uma proposta e o
parecer do instrutor são três decisões diferentes.

## Fichas rejeitadas

| Evento | Efeito confirmado |
|---|---|
| A vigente é rejeitada | A continua consultável com motivo e chat. |
| B posterior é gerada/publicada | B começa PENDENTE e é a atual; A rejeitada continua disponível. |
| B é aceita ou a tentativa de gerar B falha | Não dispara exclusão de A. |
| B posterior também é rejeitada | Excluir conteúdo/itens de A; B é a rejeitada retida e permanece consultável. |
| C posterior também é rejeitada | Excluir conteúdo/itens de B e reter C. |
| Evento duplicado ou parecer atrasado | Não apaga versão mais recente, não reutiliza número e não duplica exclusão. |

Auditoria mantém identificação, responsável, parecer, datas e motivo da exclusão;
registros/snapshots de treinos já executados e fichas aceitas não são apagados por
essa política. Conteúdo excluído não pode reaparecer por consulta direta,
exportação ou contexto ativo/cache do chat. A conversa passada não é reescrita,
mas não serve para restaurar automaticamente uma prescrição excluída.

## Biometria e infraestrutura

CompreFace é integração de biometria, separada da IA de treino e de seu banco
vetorial. Matrícula pelo atendente não exige pagamento confirmado; identificação
facial, autorização interna e passagem simulada da catraca são etapas distintas.
Hospedagem/versão do CompreFace e execução antes da fase final de Docker ainda
precisam ser resolvidas em GATE-06/GATE-08; não foi implantado serviço nesta entrega.

## Referências internas

- [Macrorequisitos](../requisitos/macrorequisitos-ia-rag.md).
- [Requisitos funcionais, especialmente RF-15/17/19/35/36](../requisitos/requisitos-funcionais.md).
- [Regras de negócio](../requisitos/regras-de-negocio.md).
- [Decisões confirmadas](decisoes-iniciais.md).
- [Fluxos e contrato facial](fluxos-atualizados.md).
- [Materiais bibliográficos](../../materiais/rag/README.md).

## Verificação documental

A alteração é de especificação e bibliografia; não há código de aplicação nem
testes executáveis do produto configurados. Conferir IDs/links, ausência de
referências ativas ao fornecedor anterior, integridade do catálogo e originais,
e whitespace. Os cenários novos de regressão estão em TRN-03/TRN-04/AI-05/AI-06
e na estratégia de testes para execução quando esses módulos forem implementados.
