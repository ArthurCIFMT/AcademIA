# Matriz de rastreabilidade da entrega acadêmica

Veja também a [rastreabilidade dos cartões](rastreabilidade-prompts.md), que liga
cada prompt aos requisitos e módulos. Associação de prompt não comprova execução.

## Cobertura por módulo

A tabela indica cobertura e colaboração. O proprietário de cada dado/workflow é
definido em modulos.md; participar de um requisito não transfere seu ownership.

| Módulo | Requisitos funcionais | Regras de negócio | Macrorequisitos |
|---|---|---|---|
| MOD-00 | Transversal | RN-23, RN-32, RN-33 | Critérios técnicos transversais |
| MOD-01 | RF-01–RF-08 | RN-01–RN-05, RN-11, RN-28 | MRF12 |
| MOD-02 | RF-34; apoio a RF-35 pela designação | RN-11, RN-31, RN-33 | Apoio a MRF10 |
| MOD-03 | RF-09–RF-14 | RN-11, RN-13, RN-21, RN-23, RN-32, RN-33 | MRF03, MRF08 |
| MOD-04 | RF-15–RF-17, RF-19, RF-35, RF-38 | RN-14–RN-20, RN-31, RN-33, RN-37–RN-39 | MRF05–MRF07, MRF09, MRF10 |
| MOD-05 | — | RN-15, RN-23, RN-29, RN-30, RN-39 | MRF01, MRF02, MRF11, MRF15 |
| MOD-06 | RF-15, RF-18, RF-19 | RN-12–RN-19, RN-29, RN-30, RN-37–RN-39 | MRF04–MRF06, MRF08–MRF14 |
| MOD-07 | RF-20–RF-25, RF-36, RF-37 | RN-06–RN-10, RN-24, RN-26, RN-34–RN-36 | — |
| MOD-08 | RF-26, RF-27, RF-31 | RN-22, RN-24, RN-35, RN-36 | — |
| MOD-09 | RF-30 | RN-25 | — |
| MOD-10 | RF-32, RF-33; apoio a RF-15/RF-19 | RN-04, RN-33, RN-37 | MRF05, MRF09, MRF13, MRF14 |
| MOD-11 | RF-28, RF-29 | RN-23, RN-28, RN-34 | — |
| MOD-12 | Transversal | RN-03, RN-09, RN-23, RN-26–RN-28, RN-31–RN-33 | MRF11–MRF13, MRF15 |


## Escopo de admissão do PG-02

| Precondição | Verificação |
|---|---|
| Núcleo acadêmico | PG-01 concluído, com a regressão de consulta/chat antes do parecer, avaliação posterior e isolamento reexecutada no INF-04. [Jornadas no Edge](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). |
| Módulos complementares selecionados | Matrículas, biometria, catraca fictícia, frequência, agenda e painel concluídos conforme manifesto. [CompreFace real em ACS-02](../testes/comandos.md#acs-02--reconhecimento-facial-e-eventos). [Agenda](../testes/comandos.md#aul-01--agenda-de-aulas-por-ocorrências). [Frequência e lotação](../testes/comandos.md#acs-06--interface-de-frequência-e-lotação). |
| Financeiro | Registro manual didático, cobranças, compra e indicadores simulados. Matrícula continua independente. [FIN-02](../testes/comandos.md#fin-02--compra-simulada-de-plano). [FIN-03](../testes/comandos.md#fin-03--indicadores-financeiros-simulados). |
| Qualidade visual | UX-09 concluído. Verificações de módulos posteriores constam nos cartões de agenda, acesso e financeiro, com a jornada de acesso/checkout em INF-04. [Aceite UX-09](../testes/ux09-aceite-visual.md). [Integração no Edge](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). |
| Infraestrutura local | INF-01–INF-04 concluídos. PostgreSQL, Qdrant, Mailpit, arquivos persistentes e iniciador local exercitados no Windows. [Rede e persistência](../testes/comandos.md#inf-03--segurança-e-persistência-locais). [Instalação e restauração](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). |
| Itens futuros | Reservas/capacidade ficam dispensadas nesta entrega, conforme RN-25 e o ADR-005. Pagamento real e containerização integral permanecem fora do escopo. [Decisão e limites](../requisitos/contexto-e-escopo.md#escopo-da-entrega-acadêmica-local). |

PG-02 comprova prontidão para iniciar a validação final. A regressão do conjunto
atual, incluindo a pendência da verificação histórica de migrations, fica em VAL-02.
[Conferência e pendências encontradas](../testes/comandos.md#val-01--conferência-documental-e-do-modelo).

## Matriz de aceite do escopo selecionado

Cada linha liga seu requisito a cartões concluídos e à execução documentada.
Os intervalos das RNs e RNFs agrupam critérios que compartilham a mesma evidência.
`Entregue` indica capacidade com evidência em um recorte identificado. A matriz
registra a rodada que verificou cada caso. Ela inclui resultados históricos e
evidência de regressão. Os limites conhecidos ficam explícitos na própria linha
ou nas notas abaixo.

### Requisitos funcionais

| ID | Implementação e cartões | Evidência ou motivo de dispensa | Estado |
|---|---|---|---|
| RF-01 | PES-02/UX-08 · cadastro e perfil cliente | [Validação e identidade](../testes/comandos.md#cadastro-e-manutenção-de-clientes). [CPF opcional e duplicidade](../testes/comandos.md#cadastro-de-clientes-com-cpf-opcional--revisão-0017). | Entregue |
| RF-02 | PES-02/UX-08 · busca autorizada e detalhe | [Lista e consulta](../testes/comandos.md#cadastro-e-manutenção-de-clientes). [Idade calculada](../testes/comandos.md#idade-no-cadastro-e-no-onboarding). | Entregue |
| RF-03 | PES-02/ACS-01 · edição, estado e referência facial | [Edição e estados](../testes/comandos.md#cadastro-e-manutenção-de-clientes). [CPF](../testes/comandos.md#cadastro-de-clientes-com-cpf-opcional--revisão-0017). [Referência com matrícula](../testes/comandos.md#acs-01--referência-facial). | Entregue |
| RF-04 | IAM-01/02/04 · sessão, contas e perfis | [Sessão](../testes/comandos.md#verificações-de-identidade). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-08. | Entregue |
| RF-05 | IAM-03/04/UX-03 · papéis, políticas na API e perfil próprio | [Autorização](../testes/comandos.md#verificações-de-autorização). [Navegação e perfil próprio](../testes/comandos.md#revisão-dos-fluxos-após-val-01). | Entregue |
| RF-06 | IAM-05/NTF-01 · recuperação com Mailpit e revogação | [Token e envio](../testes/comandos.md#recuperação-de-acesso). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-08. | Entregue |
| RF-07 | PES-01/UX-08 · cadastro de funcionário | [Cadastro e unicidade](../testes/comandos.md#cadastro-e-manutenção-de-funcionários). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-01. | Entregue |
| RF-08 | PES-01/UX-08 · manutenção e inativação de funcionário | [Atualização e permissão](../testes/comandos.md#cadastro-e-manutenção-de-funcionários). | Entregue |
| RF-09 | ONB-01/NTF-01 · convite e falha SMTP | [Convite, validade e envio](../testes/comandos.md#convite-inicial-de-onboarding). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-01. | Entregue |
| RF-10 | ONB-01/03/UX-04 · link vinculado ao cliente | [Vínculo e expiração](../testes/comandos.md#convite-inicial-de-onboarding). [Formulário](../testes/comandos.md#formulário-responsivo-do-onboarding). | Entregue |
| RF-11 | ONB-02/03/UX-04 · campos físicos e rascunho | [Persistência](../testes/comandos.md#persistência-do-onboarding). [Idade derivada do cadastro](../testes/comandos.md#idade-no-cadastro-e-no-onboarding). | Entregue |
| RF-12 | ONB-02/04 · dados de saúde e acesso por designação | [Contexto do cliente](../testes/comandos.md#persistência-do-onboarding). [Restrições ao instrutor](../testes/comandos.md#avaliação-profissional-por-designação). | Entregue |
| RF-13 | ONB-02/03/AI-01 · conclusão e snapshot de origem | [Conclusão](../testes/comandos.md#persistência-do-onboarding). [Dados insuficientes e triagem](../testes/comandos.md#triagem-acadêmica-e-preparação-ai-01). | Entregue |
| RF-14 | ONB-02/03/UX-04 · consulta do próprio onboarding | [Consulta e retomada](../testes/comandos.md#formulário-responsivo-do-onboarding). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-01 e E2E-02. | Entregue |
| RF-15 | AI-01–AI-04/TRN-02 · triagem, geração com catálogo e treino manual | [Bloqueios](../testes/comandos.md#triagem-acadêmica-e-preparação-ai-01). [Publicação validada](../testes/comandos.md#geração-persistente-ai-03). [AI-06 v4](../testes/ai06-enxuto.md). | Entregue |
| RF-16 | TRN-04/UX-06 · ficha própria por dia e exportação | [Consulta e exportação móveis](../testes/comandos.md#consulta-móvel-e-exportação-do-treino). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-03 e E2E-05. | Entregue |
| RF-17 | TRN-03/04/AI-03 · versões, retenção e histórico | [Versões e publicação](../testes/comandos.md#publicação-e-parecer-posterior). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-04 e E2E-05. | Entregue |
| RF-18 | AI-05/UX-05 · dúvida em português com evidências e histórico | [Chat](../testes/comandos.md#chat-e-adaptação-ai-05). [Histórico após nova ficha](../testes/comandos.md#histórico-do-chat-e-regressão-completa-do-mvp--2026-11-19). [AI-06 v4](../testes/ai06-enxuto.md). | Entregue |
| RF-19 | AI-05/UX-05 · adaptação explícita e versionada | [Triagem, confirmação e nova versão](../testes/comandos.md#chat-e-adaptação-ai-05). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-04. [AI-06 v4](../testes/ai06-enxuto.md). | Entregue |
| RF-20 | ACS-02 · DTO de identificação e origem confiável | [Contrato, conflito e deduplicação](../testes/comandos.md#acs-02--reconhecimento-facial-e-eventos). | Entregue |
| RF-21 | ACS-02/03/04/MEM-01 · limiar e decisão de acesso | [Identidade e score](../testes/comandos.md#acs-02--reconhecimento-facial-e-eventos). [Matrícula, modalidade e limite](../testes/comandos.md#acs-03--motor-de-autorização-e-passagens). [Alternativa manual](../testes/comandos.md#acs-04--confirmação-manual-de-identidade). | Entregue |
| RF-22 | ACS-01 · cadastro, substituição e miniatura privada | [Cadastro e substituição com CompreFace real](../testes/comandos.md#acs-01--referência-facial). [Matrícula e acesso com miniatura privada](../testes/comandos.md#revisão-dos-fluxos-após-val-01). | Entregue |
| RF-23 | ACS-03/05/06 · passagem confirmada e histórico | [Entrada, saída e deduplicação](../testes/comandos.md#acs-05--frequência-e-lotação). [Jornada da catraca](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RF-24 | ACS-05 · cálculo de presença | [Total e consistência](../testes/comandos.md#acs-05--frequência-e-lotação). [Lotação 0 → 1 → 0](../testes/comandos.md#acs-06--interface-de-frequência-e-lotação). | Entregue |
| RF-25 | ACS-06 · lotação em consulta móvel | [Verificação no Edge](../testes/comandos.md#acs-06--interface-de-frequência-e-lotação). | Entregue |
| RF-26 | FIN-01/MEM-00/FIN-02 · cobrança e recebimento simulado | [CRUD, vínculo e valor](../testes/comandos.md#fin-01--cobranças-e-consulta-financeira). [Estados da simulação](../testes/comandos.md#fin-02--compra-simulada-de-plano). | Entregue |
| RF-27 | FIN-01 · consulta própria e administrativa | [Permissões e visualização](../testes/comandos.md#fin-01--cobranças-e-consulta-financeira). [Consulta no Edge](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RF-28 | DSH-01/FIN-03 · painel, frequência e faturamento | [Acesso e falha parcial](../testes/comandos.md#dsh-01--painel-administrativo). [Agregados financeiros](../testes/comandos.md#fin-03--indicadores-financeiros-simulados). | Entregue |
| RF-29 | DSH-01/FIN-03 · indicadores operacionais e financeiros | [Clientes, frequência e lotação](../testes/comandos.md#dsh-01--painel-administrativo). [Mês, ano e total simulados](../testes/comandos.md#fin-03--indicadores-financeiros-simulados). | Entregue |
| RF-30 | AUL-01 · agenda administrativa, pública e do cliente | [CRUD, cancelamento e três telas](../testes/comandos.md#aul-01--agenda-de-aulas-por-ocorrências). | Entregue |
| RF-31 | MEM-01/FIN-02 · compra simulada e matrícula pelo atendente | [Matrícula e renovação independentes](../testes/comandos.md#mem-01--planos-e-matrículas). [Catálogo, recibo e idempotência](../testes/comandos.md#fin-02--compra-simulada-de-plano). [Jornada do recibo](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RF-32 | EQP-01/UX-08 · manutenção de equipamentos, imagem e estado | [Cadastro, imagem e disponibilidade](../testes/comandos.md#inventário-e-catálogo-de-equipamentos). [Aceite UX-09](../testes/ux09-aceite-visual.md). | Entregue |
| RF-33 | EQP-01/UX-08 · consulta pública responsiva | [Catálogo e filtros](../testes/comandos.md#inventário-e-catálogo-de-equipamentos). [Aceite UX-09](../testes/ux09-aceite-visual.md). | Entregue |
| RF-34 | PES-03/ONB-04/UX-07 · designação e substituição com histórico | [Designações e permissões](../testes/comandos.md#designação-de-instrutor). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-01. | Entregue |
| RF-35 | TRN-03/AI-04/UX-07/NTF-01 · fila, aviso, parecer e retenção | [Parecer, autoria e rejeição](../testes/comandos.md#publicação-e-parecer-posterior). [Acompanhamento](../testes/comandos.md#acompanhamento-e-interface-ai-04). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-03 a E2E-05. | Entregue |
| RF-36 | ACS-02 · nova captura com CompreFace | [Comparação real histórica e falhas controladas](../testes/comandos.md#acs-02--reconhecimento-facial-e-eventos). | Entregue |
| RF-37 | ACS-07/03/06 · simulador separado e callback | [Comando, reenvio e contrato](../testes/comandos.md#acs-07--simulador-de-catraca). [Decisão e retorno](../testes/comandos.md#acs-03--motor-de-autorização-e-passagens). [Jornada no Edge](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RF-38 | TRN-01/EQP-01/UX-08 · exercícios e recursos elegíveis | [Catálogo, autorização e combinações](../testes/comandos.md#catálogo-de-exercícios). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-06. | Entregue |

### Regras de negócio

| ID | Implementação e cartões | Evidência ou motivo de dispensa | Estado |
|---|---|---|---|
| RN-01–RN-03 | PES-01/02/IAM-02 · identidade, conta, perfis e histórico | [Funcionários](../testes/comandos.md#cadastro-e-manutenção-de-funcionários). [Clientes](../testes/comandos.md#cadastro-e-manutenção-de-clientes). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-08. | Entregue |
| RN-04–RN-05 | IAM-03 · autorização e escopo próprio | [Políticas](../testes/comandos.md#verificações-de-autorização). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-02. | Entregue |
| RN-06–RN-07 | ACS-02/03 · identificação separada e limiar | [Comparação](../testes/comandos.md#acs-02--reconhecimento-facial-e-eventos). [Autorização](../testes/comandos.md#acs-03--motor-de-autorização-e-passagens). | Entregue |
| RN-08–RN-09 | ACS-04 · confirmação manual auditada | [Ator, motivo e mesmas regras de entrada](../testes/comandos.md#acs-04--confirmação-manual-de-identidade). | Entregue |
| RN-10 | ACS-01 · separação da referência facial | [Cadastro e atualização](../testes/comandos.md#acs-01--referência-facial). | Entregue |
| RN-11 | IAM-03/ONB-04 · acesso à saúde por necessidade funcional | [Atribuição e revogação](../testes/comandos.md#avaliação-profissional-por-designação). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-02. | Entregue |
| RN-12 | TRN-03/AI-05 · consulta/chat antes do parecer | [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-03 a E2E-05. | Entregue |
| RN-13 | AI-01/03 · triagem e bloqueio determinístico | [Casos graves e dados insuficientes](../testes/comandos.md#triagem-acadêmica-e-preparação-ai-01). [AI-06 v4](../testes/ai06-enxuto.md). | Entregue |
| RN-14 | TRN-02/03 · ficha manual e nova versão profissional | [Editor e recursos](../testes/comandos.md#editor-de-ficha-manual). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-07. | Entregue |
| RN-15 | RAG-05/AI-05 · evidência pertinente para adaptação | [Relatório RAG-05](../testes/rag05-avaliacao.json). [Abstenção e restrições](../testes/comandos.md#chat-e-adaptação-ai-05). | Entregue |
| RN-16–RN-19 | TRN-03/04/AI-05 · imutabilidade, retenção, adaptação e falha de IA | [Publicação, exclusão e auditoria](../testes/comandos.md#publicação-e-parecer-posterior). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-04, E2E-05 e E2E-07. Preservação de históricos no escopo vigente. | Recorte acadêmico |
| RN-20–RN-21 | TRN-01/ONB-04 · exercício inativo e avaliação atribuível | [Histórico de exercícios](../testes/comandos.md#catálogo-de-exercícios). [Autor e data](../testes/comandos.md#avaliação-profissional-por-designação). | Entregue |
| RN-22 | MEM-01 · matrícula de plano ativo | [Plano, estado e renovação](../testes/comandos.md#mem-01--planos-e-matrículas). | Entregue |
| RN-23 | FND-06/NTF-01/INF-03 · dados sensíveis e logs | [SMTP sem tokens em registros de entrega](../testes/comandos.md#notificações). [Falha local sem segredos](../testes/comandos.md#inf-03--segurança-e-persistência-locais). | Entregue |
| RN-24 | MEM-01/ACS-03/FIN-02 · financeiro independente do acesso | [Matrícula com e sem registro financeiro](../testes/comandos.md#mem-01--planos-e-matrículas). [Autorização](../testes/comandos.md#acs-03--motor-de-autorização-e-passagens). | Entregue |
| RN-25 | AUL-02 · capacidade somente se houver reservas | [Escopo vigente](../requisitos/contexto-e-escopo.md#escopo-da-entrega-acadêmica-local). AUL-01 mantém a agenda. | Dispensado nesta entrega |
| RN-26 | NTF-01/PES-01/ACS-01 · avisos críticos | [Projeção e destinatários](../testes/comandos.md#notificações). [Alterações de permissão](../testes/comandos.md#cadastro-e-manutenção-de-funcionários). [Biometria](../testes/comandos.md#acs-01--referência-facial). Alterações em arquivos de configuração são feitas fora da aplicação e não têm evidência de aviso automatizado. | Evidência parcial |
| RN-27 | FND-08/TRN-03 · auditoria protegida | [Auditoria após expurgo e parecer](../testes/comandos.md#publicação-e-parecer-posterior). [Regressão do MVP](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RN-28 | IAM-03/TRN-04 · autorização da exportação | [Exportação e titularidade](../testes/comandos.md#consulta-móvel-e-exportação-do-treino). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-05. | Entregue |
| RN-29–RN-30 | AI-01/05/06 · contexto isolado e respostas informativas | [Isolamento e limites](../testes/comandos.md#chat-e-adaptação-ai-05). [AI-06 v4](../testes/ai06-enxuto.md). | Entregue |
| RN-31 | TRN-02/03/ONB-04 · autoria e decisão atribuíveis | [Autor da ficha e do parecer](../testes/comandos.md#publicação-e-parecer-posterior). | Entregue |
| RN-32–RN-33 | FND-05/06/08 e módulos de domínio · UTC e integridade histórica | [Retenção e histórico](../testes/comandos.md#publicação-e-parecer-posterior). [Datas e fuso](../testes/comandos.md#aul-01--agenda-de-aulas-por-ocorrências). [Paridade e restauração da revisão](../testes/comandos.md#val-01--conferência-documental-e-do-modelo). | Entregue |
| RN-34 | ACS-06/DSH-01 · relatórios sem dados biométricos | [Consulta agregada](../testes/comandos.md#acs-06--interface-de-frequência-e-lotação). [DTO e isolamento dos indicadores](../testes/comandos.md#dsh-01--painel-administrativo). | Entregue |
| RN-35–RN-36 | MEM-01/ACS-03/04 · matrícula, autorização e dispositivo | [Motivos de negativa, validação e passagem](../testes/comandos.md#acs-03--motor-de-autorização-e-passagens). [Mesmo motor no fluxo manual](../testes/comandos.md#acs-04--confirmação-manual-de-identidade). | Entregue |
| RN-37 | EQP-01/TRN-01/AI-03 · restrição de recursos | [Disponibilidade e alternativas](../testes/comandos.md#catálogo-de-exercícios). [Revalidação da publicação](../testes/comandos.md#geração-persistente-ai-03). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-06. | Entregue |
| RN-38 | TRN-03 · máximo de 15 versões completas | [Retenção e recusa de reversão indevida](../testes/comandos.md#publicação-e-parecer-posterior). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-05. | Entregue |
| RN-39 | RAG-05/AI-06/UX-09 · português com fontes multilíngues | [Relatório RAG-05](../testes/rag05-avaliacao.json). [AI-06 v4](../testes/ai06-enxuto.md). [Aceite UX-09](../testes/ux09-aceite-visual.md). | Entregue |

### Requisitos não funcionais

| ID | Implementação e cartões | Evidência ou motivo de dispensa | Estado |
|---|---|---|---|
| RNF-01 | FND-07/UX-02 · React, TypeScript e Vite | [Instalação pelo lockfile, build e frontend](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RNF-02–RNF-03 | FND-04/05/INF-04 · Python e PostgreSQL | [Ambiente limpo e migration](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RNF-04 | FND-06 · REST, JSON e OpenAPI | [Contrato, API pelo proxy e regressão](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Entregue |
| RNF-05 | RAG-02/05 · Qdrant local e porta vetorial | [Persistência e isolamento do índice](../testes/comandos.md#conexão-vetorial-local). [Relatório RAG-05](../testes/rag05-avaliacao.json). | Entregue |
| RNF-06 | FND-06/ACS-07/AI-02 · JSON nas fronteiras | [Comando e callback](../testes/comandos.md#acs-07--simulador-de-catraca). [Schemas da IA](../testes/comandos.md#orquestrador-e-contratos-ai-02). | Entregue |
| RNF-07 | TST-01/INF-04 · suítes unitária, integração, API e E2E | [Suítes executadas](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). [Asserção histórica de migration pendente de atualização em VAL-02](../testes/comandos.md#val-01--conferência-documental-e-do-modelo). | Evidência com pendência |
| RNF-08 | FND-04/INF-03 · ambiente e confidencialidade | [Isolamento de credenciais e arquivos](../testes/comandos.md#inf-03--segurança-e-persistência-locais). | Entregue |
| RNF-09 | NTF-01/IAM-05/ONB-01 · e-mail local | [SMTP real em loopback](../testes/comandos.md#notificações). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-01 e E2E-08. | Entregue |
| RNF-10–RNF-12 | INF-01–INF-04/GATE-08 · instalação, rede e armazenamento locais | [Loopback e firewall](../testes/comandos.md#inf-03--segurança-e-persistência-locais). [Instalação e reinício](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). [CompreFace dedicado](preparacao-gate-08.md). | Entregue |
| RNF-13 | RAG-05 · p95 da busca ≤ 2 s no conjunto fixado | [Relatório RAG-05](../testes/rag05-avaliacao.json). Busca p95 2,12 ms em 28 consultas com sete trechos. | Recorte medido |
| RNF-14 | UX-09/ACS-06/AUL-01/FIN-03 · interface móvel | [Aceite UX-09](../testes/ux09-aceite-visual.md). [Agenda](../testes/comandos.md#aul-01--agenda-de-aulas-por-ocorrências). [Visitas e lotação](../testes/comandos.md#acs-06--interface-de-frequência-e-lotação). [Painel financeiro](../testes/comandos.md#fin-03--indicadores-financeiros-simulados). | Entregue |
| RNF-15 | FND-06/NTF-01/INF-03 · diagnósticos com minimização | [Falha do PostgreSQL](../testes/comandos.md#inf-03--segurança-e-persistência-locais). [Entrega SMTP e proteção de links](../testes/comandos.md#notificações). | Entregue |
| RNF-16 | FND-05/06 · UTC e ISO 8601 | [Fusos e intervalos](../testes/comandos.md#aul-01--agenda-de-aulas-por-ocorrências). [Agregação em São Paulo](../testes/comandos.md#fin-03--indicadores-financeiros-simulados). | Entregue |
| RNF-17 | FND-08/AI-03/ACS-07/FIN-02 · idempotência | [Repetição de geração](../testes/comandos.md#geração-persistente-ai-03). [Reenvio e confirmação](../testes/comandos.md#acs-07--simulador-de-catraca). [Recibo sem duplicação](../testes/comandos.md#fin-02--compra-simulada-de-plano). | Entregue |
| RNF-18 | AI-02/05/06 · orçamento, etapas fixas e medições | [Limites e chamadas](../testes/comandos.md#orquestrador-e-contratos-ai-02). [AI-06 v4](../testes/ai06-enxuto.md). Percentis da amostra real são descritivos. | Recorte medido |
| RNF-19–RNF-20 | UX-01–UX-09 e interfaces posteriores · componentes e qualidade visual | [Aceite UX-09](../testes/ux09-aceite-visual.md). [Agenda](../testes/comandos.md#aul-01--agenda-de-aulas-por-ocorrências). [Acesso móvel](../testes/comandos.md#acs-06--interface-de-frequência-e-lotação). [Painel financeiro](../testes/comandos.md#fin-03--indicadores-financeiros-simulados). [Checkout no Edge](../testes/comandos.md#inf-04--instalação-local-e-teste-integrado). | Amostra de navegador |

### Macrorequisitos de IA e RAG

| ID | Implementação e cartões | Evidência ou motivo de dispensa | Estado |
|---|---|---|---|
| MRF01 | RAG-01/03/04 · curadoria, extração, chunks, E5 e armazenamento | [Corpus](../testes/comandos.md#corpus-documental). [Extração](../testes/comandos.md#extração-pdf-e-txt). [Indexação](../testes/comandos.md#indexação-e-embeddings-locais). | Entregue |
| MRF02 | RAG-02/05 · busca, filtros, similaridade e abstenção | [Índice](../testes/comandos.md#conexão-vetorial-local). [Relatório RAG-05](../testes/rag05-avaliacao.json). | Entregue |
| MRF03 | ONB-02/04/AI-01 · onboarding e resumo minimizado | [Dados versionados](../testes/comandos.md#persistência-do-onboarding). [Resumo e ausências](../testes/comandos.md#triagem-acadêmica-e-preparação-ai-01). | Entregue |
| MRF04 | AI-02/03/05 · máquina de estados e orçamento | [Fluxo fixo e contratos](../testes/comandos.md#orquestrador-e-contratos-ai-02). [Execução persistente](../testes/comandos.md#geração-persistente-ai-03). | Entregue |
| MRF05 | AI-02/03/TRN-01 · geração estruturada sobre catálogo elegível | [Validação e publicação](../testes/comandos.md#geração-persistente-ai-03). [AI-06 v4](../testes/ai06-enxuto.md). | Entregue |
| MRF06 | AI-02/03/TRN-03 · validação técnica e parecer separado | [Falha e consistência](../testes/comandos.md#geração-persistente-ai-03). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-03 e E2E-06. | Entregue |
| MRF07 | TRN-03/04/UX-06 · ficha móvel, exportação e retenção | [Entrega própria](../testes/comandos.md#consulta-móvel-e-exportação-do-treino). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-05. | Entregue |
| MRF08 | AI-01/03 · triagem e evidências por snapshot | [Política e estados](../testes/comandos.md#triagem-acadêmica-e-preparação-ai-01). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-03. | Entregue |
| MRF09 | TRN-01/EQP-01/AI-03 · catálogo viável e validação pré-publicação | [Recursos](../testes/comandos.md#catálogo-de-exercícios). [Mudança de inventário](../testes/comandos.md#geração-persistente-ai-03). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-06. | Entregue |
| MRF10 | TRN-02/03/AI-04/NTF-01 · edição, avisos e parecer | [Parecer posterior](../testes/comandos.md#publicação-e-parecer-posterior). [Avisos persistentes](../testes/comandos.md#notificações). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-07. | Entregue |
| MRF11 | RAG-05/AI-02/05/06 · proveniência, referência e idioma | [Relatório RAG-05](../testes/rag05-avaliacao.json). [Citações e fontes](../testes/comandos.md#chat-e-adaptação-ai-05). [AI-06 v4](../testes/ai06-enxuto.md). | Entregue |
| MRF12 | IAM-03/AI-01/05 · isolamento, minimização e retenção | [Contextos segregados](../testes/comandos.md#chat-e-adaptação-ai-05). [Histórico consultável e janela limitada](../testes/comandos.md#histórico-do-chat-e-regressão-completa-do-mvp--2026-11-19). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-02 e E2E-05. | Entregue |
| MRF13 | RAG-05/AI-06 · avaliação real e determinística | [Relatório RAG-05](../testes/rag05-avaliacao.json). [AI-06 v4](../testes/ai06-enxuto.md). [Amostra aceita](../requisitos/escopo-ia-academico.md#avaliação-e-retrabalho). | Recorte medido |
| MRF14 | AI-05/UX-05 · chat e adaptação e revisão de histórico | [Dúvida, confirmação e adaptação](../testes/comandos.md#chat-e-adaptação-ai-05). [Regressão do histórico](../testes/comandos.md#histórico-do-chat-e-regressão-completa-do-mvp--2026-11-19). [Jornadas do MVP](../testes/aceitacao-mvp.md#o-que-as-jornadas-demonstram), E2E-04. | Entregue |
| MRF15 | AI-02/03/06/RAG-02 · perfis explícitos, falhas e retenção operacional | [Adaptadores e orçamento](../testes/comandos.md#orquestrador-e-contratos-ai-02). [Retenção e auditoria](../testes/comandos.md#geração-persistente-ai-03). [AI-06 v4](../testes/ai06-enxuto.md). Reservas têm qualificação própria. | Recorte acadêmico |

## Correspondência entre MER, modelo e migrations

| Fonte | Conferência |
|---|---|
| [MER original](modelo-de-dados/original/README.md) | Preservado pelo hash de referência. Suas 18 entidades são conceituais. O [relatório comparativo](revisao-mer.md) registra os desdobramentos de identidade, designação, versões, equipamentos, IA e acesso. |
| [Modelo lógico DBML](modelo-de-dados/modelo-logico.dbml), [JSON](modelo-de-dados/modelo-logico.json) e [dicionário](modelo-de-dados/dicionario.md) | 44 tabelas, 363 colunas e 76 referências lógicas. `academia` fica planejada como configuração singleton. |
| [Migrations e PostgreSQL](../../database/README.md) | Revisão `0027` com 43 tabelas, 357 colunas e 77 constraints de chave estrangeira no schema `academia`. Foi comparado ao metadata do ORM antes e depois do round trip. A 0027 acrescenta os dois campos do recibo simulado. |
| [Diagrama físico histórico](modelo-de-dados/visualizacao-otimizada/README.md) | Retrato da revisão 0016, mantido como evidência da normalização. |

As contagens de referências lógicas e constraints físicas usam critérios próprios.
Após VAL-01, as migrations 0028 e 0029 acrescentaram endereço e miniatura.
O modelo físico passa a 359 colunas, com as mesmas tabelas e referências.
O Qdrant é armazenamento vetorial separado. Os ensaios de paridade da revisão
`0027` e a divergência na expectativa do teste legado constam no
[registro de execução](../testes/comandos.md#val-01--conferência-documental-e-do-modelo).

## Limites e pendências

- O aceite facial real de ACS-01/02 usou amostras sintéticas externas ao Git.
  As jornadas INF-04 usaram resposta facial controlada e catraca HTTP fictícia.
  O limiar configurado é pontuação de correspondência do provedor.
- AI-06 qualifica a amostra e o perfil avaliados. A manutenção posterior do
  contrato e do corpus tem [evidência própria](../testes/reparo-ia-20261119.md).
  As demais fontes e os quatro PDFs pendentes permanecem sem promoção automática.
- A agenda usa ocorrências sem reservas, e a aplicação preserva os registros
  históricos existentes. Um módulo de registro de execução de treinos exige
  escopo próprio. [Fluxos vigentes](fluxos-atualizados.md).
- A avaliação visual cobre o Windows/Edge e as larguras declaradas. A revisão
  manual do responsável permanece disponível. [Escopo da avaliação](../testes/ux09-aceite-visual.md).
