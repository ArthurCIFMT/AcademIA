# Requisitos funcionais

## Convenções

- Os IDs originais foram preservados.
- RF-24 e RF-25 permanecem separados: cálculo e apresentação são capacidades
  distintas.
- RF-34 e RF-35 foram acrescentados a partir das solicitações explícitas sobre
  designação de instrutor e avaliação posterior dos treinos da IA.
- RF-36 e RF-37 explicitam reconhecimento facial real e catraca fictícia,
  conforme solicitação posterior; não há hardware físico neste projeto.
- Mudanças de redação não alteram o propósito original.

## Usuários, clientes e funcionários

### RF-01 — Cadastrar cliente

Permitir que usuário administrativo registre novo cliente e o vincule a um e-mail.

- CA-01.1: dados obrigatórios válidos criam cliente com identificador único.
- CA-01.2: e-mail associado a outra conta ativa é rejeitado.
- CA-01.3: dados inválidos retornam validação e não criam cadastro parcial.

### RF-02 — Consultar e pesquisar clientes

Permitir que usuários administrativos localizem e consultem clientes.

- CA-02.1: usuário autorizado lista clientes.
- CA-02.2: pesquisa por nome ou e-mail retorna correspondências.
- CA-02.3: usuário sem autorização não consulta dados de terceiros.

### RF-03 — Atualizar e alterar estado do cliente

Permitir alteração cadastral e ativação ou desativação do cliente.

- CA-03.1: alterações válidas persistem após nova consulta.
- CA-03.2: cliente desativado deixa de ser usuário habilitado.
- CA-03.3: desativação não apaga o histórico.
- CA-03.4: cliente elegível à biometria precisa de foto facial válida.

Pendência de detalhamento: CA-03.2 exige definir o alcance da desativação quando
a identidade também possuir perfil de funcionário. Estado da conta, estado de
perfil e permissões acumuladas não são sinônimos; registrar a matriz antes de
implementar IAM-02/PES-01/PES-02, sem presumir uma política ainda não aprovada.

### RF-04 — Autenticar usuário

Identificar cliente ou funcionário antes de acessar áreas protegidas.

- CA-04.1: credenciais válidas de usuário ativo iniciam sessão.
- CA-04.2: credenciais inválidas não iniciam sessão.
- CA-04.3: rota protegida sem sessão válida retorna não autenticado.

### RF-05 — Autorizar funções conforme papéis

Aplicar permissões de cliente, administrador, atendente e instrutor.

- CA-05.1: cliente não acessa funções administrativas.
- CA-05.2: administrador acessa as operações previstas.
- CA-05.3: chamada direta a API proibida também é rejeitada.

### RF-06 — Recuperar acesso por e-mail

Permitir recuperação de conta vinculada a e-mail.

- CA-06.1: solicitação válida inicia o envio da recuperação.
- CA-06.2: token expirado ou utilizado é recusado.
- CA-06.3: após recuperação, o usuário autentica com a nova credencial.
- Observação: infraestrutura SMTP em contêiner pertence à fase final de Docker.

### RF-07 — Cadastrar funcionário

Permitir cadastro básico de funcionário.

- CA-07.1: administrador cria funcionário com dados obrigatórios.
- CA-07.2: funcionário recebe identificador único.
- CA-07.3: duplicidade incompatível de conta ou e-mail é recusada.

### RF-08 — Consultar, atualizar e desativar funcionário

Manter dados e estado de funcionários.

- CA-08.1: administrador lista e consulta funcionários.
- CA-08.2: alterações válidas persistem.
- CA-08.3: funcionário desativado perde permissões, preservando histórico.

## Onboarding e avaliações

### RF-09 — Enviar convite de onboarding por e-mail

Enviar ao cliente cadastrado um link seguro para o primeiro onboarding.

- CA-09.1: convite é enviado ao e-mail vinculado.
- CA-09.2: link referencia o onboarding do cliente correto.
- CA-09.3: falha de envio é registrada como falha.

### RF-10 — Acessar onboarding por link seguro

Abrir o formulário correspondente a partir do convite recebido.

- CA-10.1: token válido abre o formulário correto.
- CA-10.2: token inválido ou expirado é rejeitado.
- CA-10.3: token não abre onboarding de outro cliente.

### RF-11 — Registrar dados físicos

Registrar os dados físicos e funcionais previstos no formulário aprovado.

- CA-11.1: campos físicos previstos podem ser persistidos.
- CA-11.2: campos obrigatórios são validados.
- CA-11.3: formulário editável recupera corretamente dados salvos.

### RF-12 — Registrar medicações e condições de saúde

Registrar queixas, medicações, lesões e condições informadas pelo cliente.

- CA-12.1: formulário separa queixas, medicações e histórico relevante.
- CA-12.2: dados ficam associados somente ao cliente correto.
- CA-12.3: usuário sem permissão não acessa esses dados por interface ou API.

### RF-13 — Validar e concluir onboarding

Concluir o formulário somente após o preenchimento obrigatório.

- CA-13.1: formulário obrigatório incompleto não é concluído.
- CA-13.2: conclusão registra estado e data/hora.
- CA-13.3: a IA identifica a existência de onboarding válido.

### RF-14 — Consultar o próprio onboarding

Permitir ao cliente revisar os dados que informou.

- CA-14.1: cliente autenticado consulta somente o próprio onboarding.
- CA-14.2: valores exibidos correspondem aos persistidos.
- CA-14.3: consulta de outro cliente é bloqueada.

## Fichas de treino e IA

### RF-15 — Gerar proposta de ficha utilizando IA

Gerar proposta inicial com base no onboarding e em conhecimento recuperado.

- CA-15.1: onboarding não concluído impede a geração.
- CA-15.2: chamada bem-sucedida produz proposta estruturada e persistível.
- CA-15.3: proposta pertence exclusivamente ao cliente correto.
- CA-15.4: caso bloqueado pela política de saúde não recebe proposta de treino.
- CA-15.5: proposta utiliza a versão identificada do onboarding.
- CA-15.6: após triagem e validações técnicas, o treino é publicado e fica visível
  ao cliente com parecer profissional PENDENTE, sem exigir aceite prévio.
- CA-15.7: prescrição adaptada a condição de saúde exige evidência pertinente
  recuperada do corpus aprovado, vinculada à recomendação; ausência ou conflito
  não resolvido impede gerar/publicar essa adaptação e retorna justificativa.
- CA-15.8: geração só seleciona exercícios ativos com todos os recursos necessários
  disponíveis na academia ou alternativa completa cadastrada. Disponibilidade é
  fornecida por MOD-10 e revalidada antes da publicação; dado ausente não libera seleção.
- CA-15.9: ficha e explicações ao cliente são em português, inclusive quando a
  evidência recuperada está em inglês, preservando fonte, sentido, unidades e negações.

### RF-16 — Visualizar ficha de treino atual

Exibir ao cliente sua ficha vigente em formato utilizável, especialmente no celular.

- CA-16.1: cliente visualiza a versão atual publicada com parecer PENDENTE, ACEITO
  ou REJEITADO exibido separadamente; ausência de aceite não impede consulta.
- CA-16.2: cliente sem ficha recebe estado vazio adequado.
- CA-16.3: cliente não consulta ficha de terceiro.
- CA-16.4: visualização é utilizável em celular.

### RF-17 — Persistir e versionar a ficha

Manter a ficha e criar nova versão quando uma alteração validada for publicada.

- CA-17.1: primeira ficha cria versão inicial.
- CA-17.2: alteração publicada cria versão posterior e atualiza a vigente sem
  depender de aceite profissional; nova versão começa com parecer PENDENTE.
- CA-17.3: versão atual permanece após nova consulta.
- CA-17.4: conteúdo de versão publicada ou histórica não é modificado retroativamente;
  pareceres são registros separados e não reescrevem a prescrição.
- CA-17.5: a exclusão da ficha rejeitada anterior segue CA-35.7; não apaga
  auditoria nem registros/snapshots de treinos já executados. Número de versão
  excluída não é reutilizado.
- CA-17.6: cada cliente possui no máximo 15 versões publicadas completas, incluindo
  a vigente; ao publicar a 16ª, excluir conteúdo/itens das versões mais antigas
  até restarem 15, independentemente do parecer. A vigente nunca é eliminada.
- CA-17.7: exclusão por limite retira conteúdo de consultas, exportações e contexto
  ativo/cache do chat; mantém identificação, datas, autoria, parecer e motivo em
  auditoria protegida e preserva registros/snapshots de treinos já executados.
- CA-17.8: publicação e aplicação do limite são transacionais/idempotentes;
  concorrência não ultrapassa 15 nem deixa duas vigentes. Versões continuam com
  numeração crescente; rascunhos e tentativas não publicadas não contam como ficha
  disponível. Falha na publicação não elimina ficha válida.

### RF-18 — Conversar com assistente de IA

Disponibilizar chat contextualizado sobre o treino do próprio cliente.

- CA-18.1: cliente autenticado envia mensagem e recebe resposta sem exigir aceite
  do instrutor, inclusive quando ainda não possui ficha avaliada.
- CA-18.2: assistente recebe somente o contexto autorizado do cliente.
- CA-18.3: mensagens de clientes diferentes não se misturam.
- CA-18.4: indisponibilidade do provedor gera erro controlado.

### RF-19 — Propor alteração dinâmica de treino via IA

Propor adaptação quando dor, limitação ou condição interferir no treino.

- CA-19.1: dor ou limitação relatada gera adaptação contextualizada somente
  quando o cliente é elegível e existe evidência pertinente recuperada do corpus
  aprovado para a condição e a adaptação propostas.
- CA-19.2: adaptação passa novamente pela triagem/validações e, quando válida,
  é publicada em nova versão com parecer PENDENTE; aceite prévio não é necessário.
- CA-19.3: partes não relacionadas não são apagadas.
- CA-19.4: versão publicada permanece após nova autenticação; versões anteriores
  e pareceres permanecem rastreáveis, respeitando a exclusão de CA-35.7.
- CA-19.5: falta de evidência, fonte inadequada ao caso ou conflito não resolvido
  impede publicar a adaptação; registrar abstenção sem alterar a ficha vigente.
- CA-19.6: adaptação respeita equipamentos disponíveis, idioma português e limite
  de 15 versões; recurso que ficou indisponível durante o fluxo exige revalidação.

## Biometria, acesso e frequência

### RF-20 — Receber evento externo de identificação facial

Disponibilizar contrato REST autenticado para o resultado de identificação facial
externa, normalizado pelo adaptador confiável. Não pressupõe webhook nativo do
CompreFace: reconhecimento, autorização e passagem simulada de RF-37 são distintos.

- CA-20.1: requisição autenticada e válida segue o JSON documentado.
- CA-20.2: JSON inválido retorna erro de validação.
- CA-20.3: aplicação não implementa o algoritmo de reconhecimento facial do provedor.
- CA-20.4: mesmo identificador externo não cria duplicidade.

### RF-21 — Verificar identidade e habilitação para acesso

Associar a identidade externa e executar separadamente as regras de autorização.

- CA-21.1: identidade externa conhecida é associada ao cliente.
- CA-21.2: identidade desconhecida produz decisão de negação apropriada.
- CA-21.3: cliente desativado não é tratado como habilitado.
- CA-21.4: correspondência facial somente é aceita quando atinge o limiar
  configurado, inicialmente 0,95 na escala 0–1 do CompreFace (95% na apresentação).
  Essa pontuação não constitui medida de acurácia do sistema.

### RF-22 — Inserir referência biométrica do cliente

Permitir que funcionário autorizado capture/cadastre a referência facial após
matrícula registrada pelo atendente, sem exigir pagamento confirmado.

- CA-22.1: cliente já matriculado possui foto com exatamente um rosto e qualidade
  conforme critérios técnicos do provedor; imagem inválida não cria referência.
- CA-22.2: nova referência substitui a anterior conforme política definida.
- CA-22.3: somente funcionário autorizado altera a referência.

### RF-23 — Registrar entrada, saída e frequência

Persistir eventos de acesso utilizados como histórico de frequência.

- CA-23.1: entrada válida cria registro de entrada.
- CA-23.2: saída válida cria registro de saída.
- CA-23.3: evento repetido não é contado duas vezes.
- CA-23.4: registros possuem data/hora e cliente relacionados.

### RF-24 — Calcular lotação atual

Derivar a quantidade de pessoas presentes a partir dos eventos válidos.

- CA-24.1: entrada válida incrementa uma vez.
- CA-24.2: saída válida decrementa uma vez.
- CA-24.3: evento duplicado não altera novamente o total.
- CA-24.4: valor nunca é negativo.

### RF-25 — Exibir lotação atual

Mostrar aos usuários a quantidade atual de pessoas na academia.

- CA-25.1: página apresenta o valor calculado.
- CA-25.2: nova consulta reflete eventos processados.
- CA-25.3: informação é legível em celular.

## Planos, matrícula e financeiro

### RF-26 — Registrar e atualizar situação de cobrança

Manter controle básico de cobranças por cliente.

- CA-26.1: usuário autorizado registra competência, vencimento e situação.
- CA-26.2: atualização persiste.
- CA-26.3: cobrança pertence ao cliente correto.

### RF-27 — Consultar situação de cobrança

Permitir consulta autorizada da situação financeira já registrada.

- CA-27.1: usuário autorizado consulta registros do cliente.
- CA-27.2: cliente pode visualizar a própria situação quando disponível.
- CA-27.3: cliente não consulta cobrança de terceiro.

### RF-31 — Matricular cliente e manter vínculo com plano

Permitir que um plano seja associado à conta por matrícula com validade definida.

- CA-31.1: atendente autorizado cria ou renova matrícula sem exigir pagamento
  confirmado, comprovante ou existência do módulo financeiro.
- CA-31.2: matrícula possui início, término e estado consultáveis.
- CA-31.3: matrícula vencida deixa de ser válida sem apagar o histórico.
- CA-31.4: registro de pagamentos, gateway e checkout são capacidades posteriores;
  não são pré-condições da matrícula manual no escopo acadêmico.
- CA-31.5: usuário sem permissão não matricula; ausência de pagamento, pendência
  financeira ou indisponibilidade do gateway não bloqueiam a ação do atendente.
- CA-31.6: matrícula manual registra responsável, início, término e plano ativo;
  falta de pagamento não invalida automaticamente uma matrícula vigente.

## Dashboard, aulas e equipamentos

### RF-28 — Disponibilizar dashboard administrativo

Apresentar página administrativa consolidando informações do sistema.

- CA-28.1: somente perfil autorizado acessa o dashboard.
- CA-28.2: página consolida indicadores dos módulos implementados, incluindo
  quantidade de clientes assinantes e funcionários, faturamento por períodos e
  histórico de acesso por dias/horas quando essas fontes estiverem disponíveis.
- CA-28.3: falha de indicador não expõe dados indevidos.

### RF-29 — Exibir indicadores consolidados

Apresentar indicadores provenientes dos módulos implementados.

- CA-29.1: exibe ao menos clientes ativos, histórico semanal de frequência e
  lotação atual.
- CA-29.2: quando disponíveis, exibe faturamento/receita mensal, anual e total.
- Observação: sem despesas cadastradas, o sistema não denomina receita como lucro.

### RF-30 — Gerenciar agenda de aulas

Permitir que usuário administrativo mantenha dias e horários das aulas.

- CA-30.1: administrador cria aula com identificação, data e horário.
- CA-30.2: ocorrência pode ser alterada ou retirada.
- CA-30.3: mudanças aparecem na visualização correspondente.

### RF-32 — Gerenciar equipamentos

Permitir ao administrador cadastrar, consultar, atualizar e desativar equipamentos
da academia no MVP; disponibilidade operacional restringe prescrições.

- CA-32.1: administrador autorizado cadastra nome e situação/disponibilidade.
- CA-32.2: equipamento pode possuir imagem.
- CA-32.3: cadastro permanece disponível em nova consulta.
- CA-32.4: administrador autorizado altera informações; outros perfis não mantêm o inventário.
- CA-32.5: equipamento inativo ou operacionalmente indisponível não aparece como
  disponível ao cliente e não pode sustentar novas prescrições.
- CA-32.6: serviço de disponibilidade expõe recursos atuais por contrato para
  MOD-04/MOD-06; banco vetorial/LLM não determina o inventário da academia.
- CA-32.7: exercício/variação declara recursos obrigatórios e alternativas completas;
  só dispensa equipamentos quando isso está explicitamente cadastrado. Alterar
  disponibilidade não reescreve fichas históricas; consulta sinaliza indisponibilidade.

### RF-33 — Consultar equipamentos disponíveis

Permitir que visitantes ou clientes consultem equipamentos ativos e suas imagens.

- CA-33.1: interface lista como disponíveis somente equipamentos ativos e operacionais.
- CA-33.2: apresenta nome e imagem quando cadastrada.
- CA-33.3: apresenta informações adicionais disponíveis.
- CA-33.4: equipamento desativado ou indisponível não aparece como disponível.
- CA-33.5: listagem é utilizável em celular.

## Designação e revisão profissional

### RF-34 — Designar instrutor responsável ao cliente

Vincular cada cliente a um instrutor principal vigente, preservando substituições.

- CA-34.1: administrador designa instrutor ativo a um cliente.
- CA-34.2: substituição encerra o vínculo anterior sem apagar o histórico.
- CA-34.3: somente funcionário com papel de instrutor pode ser responsável.
- CA-34.4: sistema identifica inequivocamente o instrutor principal vigente.

### RF-35 — Registrar avaliação posterior do treino pelo instrutor

Comunicar propostas ao instrutor responsável e permitir sua decisão profissional.

- CA-35.1: nova proposta gera evento/aviso ao instrutor designado e aparece em
  uma fila consultável; falha de aviso fica registrada sem perder a pendência.
- CA-35.2: instrutor pode aceitar ou rejeitar com parecer; modificação cria nova versão.
- CA-35.3: decisão registra instrutor e data/hora.
- CA-35.4: consulta do treino e chat estão disponíveis ao cliente antes do parecer;
  o aceite profissional não é pré-condição de publicação.
- CA-35.5: rejeição mantém a ficha consultável pelo cliente com motivo e chat;
  permanece disponível até outra ficha posterior receber rejeição ou expirar pelo
  limite global de 15 versões de RF-17.
- CA-35.6: parecer aplica-se somente à versão avaliada; nova versão não herda aceite.
- CA-35.7: quando uma ficha posterior é rejeitada, excluir o conteúdo/itens da
  rejeitada anterior, retirando-o das consultas, exportações e contexto do chat;
  a nova rejeitada ocupa seu lugar e permanece visível. A exclusão é automática,
  transacional e idempotente, com metadados de identificação, parecer, responsável,
  data e motivo da exclusão preservados em auditoria protegida. Fichas aceitas e
  registros/snapshots de treinos executados não são apagados por essa regra.
- CA-35.8: apenas gerar/publicar nova ficha, falhar na geração ou aceitá-la não
  dispara essa exclusão. Repetição ou parecer atrasado sobre versão mais antiga
  não elimina indevidamente a rejeitada mais recente nem cria duas fichas vigentes.
- CA-35.9: a exclusão específica de rejeitadas é independente da retenção global;
  publicar nova versão pode expirar uma antiga pelo limite de RF-17, inclusive
  aceita/rejeitada. A proteção às fichas aceitas em CA-35.7 refere-se somente à
  substituição de rejeitadas, sem dispensar o limite global.

## Integração facial e catraca acadêmica

### RF-36 — Reconhecer cliente por nova captura facial

Comparar uma nova captura com referências cadastradas usando CompreFace,
sem implementar algoritmo de reconhecimento no AcademIA.

- CA-36.1: captura com um rosto é enviada pelo backend ao provedor configurado.
- CA-36.2: identidade é resolvida pelo vínculo externo local e pontuação de
  correspondência; identidade alegada pelo navegador não determina o cliente.
- CA-36.3: rosto desconhecido, ambiguidade, baixa similaridade, imagem inválida
  ou falha do provedor não resultam em identificação positiva automática.
- CA-36.4: aceite da integração inclui cadastro e comparação reais; mock comprova
  contratos e regras, mas não comprova funcionamento da biometria facial.

### RF-37 — Integrar API externa fictícia de catraca

Enviar decisão de acesso a um serviço simulador separado, sem catraca física.

- CA-37.1: comando JSON autenticado identifica requisição, decisão, direção e validade.
- CA-37.2: simulador recebe ALLOW/DENY e registra resultado sem movimento físico.
- CA-37.3: recebimento do comando é distinto de confirmação de passagem simulada;
  somente esta última pode gerar frequência/lotação, conforme decisão válida.
- CA-37.4: repetição, expiração, negação e falha não duplicam nem inventam entrada.
- CA-37.5: evidências distinguem reconhecimento real e passagem simulada.
