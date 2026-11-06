# Auditoria de requisitos, IA e referências — 2026-11-06

## Resultado e alcance

Revisão da especificação de uma academia acadêmica: 38 RFs, 39 RNs, 18 RNFs,
15 MRFs e 61 prompts operacionais. Foram detalhados 24 critérios de RF já existentes
(187 critérios RF + 67 MRF = 254), preservando IDs e requisitos anteriores.
Esta entrega ajusta documentação/modelo lógico e o verificador documental;
não implementa API, frontend, migrations, embeddings, reconhecimento ou LLM.

Fontes: [RFs](../requisitos/requisitos-funcionais.md),
[RNs](../requisitos/regras-de-negocio.md),
[MRFs](../requisitos/macrorequisitos-ia-rag.md),
[ADRs](../arquitetura/decisoes/README.md),
[manifesto](../prompts/README.md) e
[modelo lógico](../arquitetura/modelo-de-dados/modelo-logico.json).

## Lacunas corrigidas

| Achado | Correção e rastreabilidade |
|---|---|
| RF-03 ainda tratava alcance da inativação como pendência | ADR-002 já aceito: conta global e perfis independentes; RF-01/RF-03/RF-08 e RN-01–RN-03 alinhados. |
| Aceites de autenticação genéricos | CA-04.4/CA-04.5, CA-05.4 e CA-06.4 explicitam revogação, sessão, origem/CSRF, resposta de recuperação e permissões a cada requisição. |
| Conclusão do formulário confundível com elegibilidade | CA-10.4, CA-12.4 e CA-13.4 distinguem sessão restrita, SIM/NAO/NAO_SEI e dado desconhecido. Ausente não é saudável. |
| Geração e criação manual sem aceites negativos suficientes | CA-15.12–CA-15.15 e CA-18.8 explicitam replay/conflito, falhas/quota/JSON, criação manual atribuível e instruções indevidas. |
| Cadastro de pessoa, compra, matrícula e rosto confundíveis | RF-31 e RN-35 esclarecem passos distintos; CA-21.5/CA-21.6 recusam matrícula inválida, mas preservam acesso sem pagamento com matrícula válida. |
| RF-31 cobria matrícula, mas não detalhava a compra antes solicitada | CA-31.7–CA-31.9 mantêm checkout/retorno autenticado no FIN-02 tardio, sem matrícula automática ou pagamento obrigatório. Modelo passa a relacionar pagamento ao plano da compra. |
| Biometria e lotação sem aceites de consistência suficientes | CA-20.5, CA-22.4, CA-23.5 e CA-24.5 cobrem origem confiável, troca facial falha, passagem confirmada, replay e saída sem entrada. |
| Nome duplicado de exercício dependia de regra indefinida | CA-38.1/TRN-01 e invariantes definem trim, espaços colapsados e lowercase; campo único no modelo, inclusive inativos. Decisão técnica dentro da delegação vigente. |
| Designação e parecer com lacunas de autorização | CA-34.5/CA-35.10 explicitam perda de acesso do antigo responsável, concorrência, motivo de rejeição e pendência sem instrutor. |
| README do RAG dizia que todo acervo estava pendente | Alinhado ao catálogo: sete documentos selecionados, onze em reserva. Seleção não é indexação nem teste real. |
| Rodapé do manifesto ainda dizia FND-01 pronto | Corrigido para FND-01–FND-03 concluídos documentalmente, FND-04/FND-07 prontos; sem antecipar implementação. |

Prompts afetados receberam os critérios do respectivo escopo, e a
[rastreabilidade](../arquitetura/rastreabilidade-prompts.md) foi regenerada a partir
dos 61 cartões. Não há nova cadeia agentiva nem exigência médica/jurídica externa.

## Cobertura do uso solicitado da IA

| Capacidade solicitada | Requisitos e regras | Entrega planejada | Situação |
|---|---|---|---|
| Tirar dúvidas com fontes recuperadas, em português | RF-18; MRF01/MRF02/MRF11/MRF14; RN-30/RN-39 | RAG-01–RAG-05, AI-05 | Especificado; ingestão e recuperação ainda não executadas. |
| Ler onboarding resumido sem assumir saúde por ausência | RF-11–RF-15; MRF03/MRF08; RN-13 | ONB-02/ONB-03, AI-01/AI-02 | Campos/schema/regras e casos sintéticos definidos; ensaio real pendente. |
| Criar ficha pelo LLM gratuito com conhecimento especializado | RF-15; MRF04–MRF06/MRF09/MRF15 | AI-02/AI-03, TRN-03 | Groq/Llama e limites definidos; sem chamada real nesta revisão. |
| Criar/editar manualmente quando IA não estiver disponível | CA-15.11/CA-15.14; RN-14/RN-19; MRF10 | TRN-01–TRN-03 | Especificado; não depende de LLM, embeddings ou Qdrant. |
| Adaptar treino somente com evidência para a condição informada | RF-19; RN-15/RN-17; MRF14 | ONB-03, AI-05 | Confirmação/versionamento, triagem e nova versão obrigatórios; sem suporte, abstenção. |
| Respeitar equipamentos realmente disponíveis | RF-32/RF-38; RN-37; MRF09 | EQP-01, TRN-01, AI-03 | Catálogo/inventário relacional, IDs elegíveis e revalidação na publicação. |
| Cliente consultar antes do parecer e instrutor revisar depois | RF-16/RF-34/RF-35; RN-12; MRF10 | PES-03, TRN-03, AI-04 | Parecer PENDENTE não bloqueia; rejeição e retenção de 15 preservadas. |
| Não misturar clientes nem confiar em instruções do PDF | RF-05/CA-18.8; RN-29; MRF12 | IAM-03, RAG/AI e testes de isolamento | Autorização backend, fontes como dados e sem escrita livre do modelo. |
| Confirmar qualidade/tempo no provedor real | MRF13; RNF-13/RNF-18 | RAG-05, AI-06 | Plano existe; qualidade, disponibilidade gratuita e latência não comprovadas por documentação. |

O fluxo é de RAG semântico com etapas fixas: dúvidas usam até uma geração;
ficha/adaptação, até uma análise de triagem e uma geração. Sem retry LLM automático,
planner, pesquisa iterativa ou livro inteiro no contexto. Grave bloqueado não recebe
ficha; dados necessários desconhecidos não classificam cliente como elegível.
A alternativa manual preserva regras de domínio aplicáveis e não depende de laudo.

## Matrícula e biometria acadêmica

Fluxo normal da fase financeira: escolher plano ativo → compra confirmada →
atendente registra matrícula → funcionário autorizado cadastra foto → nova captura
no CompreFace → motor verifica matrícula/modalidade/limites → catraca fictícia →
passagem simulada confirmada registra frequência/lotação.

A exceção acadêmica permanece: atendente matricula/renova sem pagamento confirmado.
Cadastro de conta ou compra não cria matrícula; rosto reconhecido não autoriza
sozinho; ALLOW/recebimento do comando não significa passagem. CompreFace real precisa
ser testado em ACS-01/ACS-02; o simulador só comprova integração, sem hardware físico.
O limiar inicial 0,95 é score de correspondência, não acurácia comprovada de 95%.

## Corpus, scripts e preservação

- 18 PDFs, 783 páginas declaradas, sete selecionados para ingestão e onze em reserva.
  O corpus inicial permite começar a indexação, sem alegar cobertura universal de
  patologias ou prescrição individual. Lacunas de suporte exigem abstenção; futura
  ampliação deve seguir resultados de RAG-05/AI-06, sem baixar materiais nesta revisão.
- PDFs, metadados bibliográficos, MER PNG e XML extraído preservados. O PNG original
  continua como origem histórica; a especificação evolutiva é o modelo lógico textual.
- Um único script versionado encontrado: scripts/verificar_documentacao.py. É útil,
  somente leitura e foi mantido/estendido para corpus selecionado e correspondência
  entre JSON/DBML. Nenhum script inútil foi encontrado ou removido.
- Documentos de transição agentic/rag antigos são referências históricas explícitas
  para o fluxo vigente; não são módulos extras nem autorização para implementá-los.
  Ferramentas pontuais desta revisão ficam fora do repositório.

## Verificação e próximos passos

Ver [cenários de regressão planejados](../testes/aceite-rf-rn-2026-11-06.md) e
[estratégia](../testes/estrategia.md). A auditoria documental confere links/IDs,
metadados, grafo, PDFs/MER e modelo/corpus. Parser oficial DBML e Ajv verificam o
modelo lógico e dez casos de contrato do formulário, sem simular backend ou LLM.
O modelo revisto contém 42 tabelas, 284 campos e 61 referências.

Verificações executadas na proposta: auditor documental sem erros/avisos (112
Markdown, 768 links locais, 254 critérios e 61 cartões rastreados); parser oficial
@dbml/core validou 42 tabelas/61 referências; Ajv validou dez casos do formulário.
Seis regressões em memória do verificador passaram, incluindo referência inválida,
tipo divergente, hash de corpus divergente, seleção duplicada e aprovação alterada.
PDFs/MER e 32 casos documentais anteriores permanecem íntegros.

FND-04 e FND-07 continuam liberados. Serviços/chaves serão configurados no prompt
correspondente. GATE-07/08/09 permanecem para reservas opcionais, detalhes da
integração de acesso e gateway posterior; não impedem iniciar os scaffolds.
Não é possível declarar IA, biometria ou MVP funcionando antes dessas implementações
com seus testes reais. Não há nova escolha obrigatória a pedir ao responsável agora.
