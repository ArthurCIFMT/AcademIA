# Onboarding e triagem acadêmica — especificação v1

Status: DEFINIDO por delegação do responsável em 2026-11-04.
Contrato: [JSON Schema](schemas/onboarding-v1.schema.json).
Responsável técnico do corpus/casos: mantenedor do projeto por delegação, sem aprovação externa.

## Cadastro e público do protótipo

CLIENTE: nome 2–120 caracteres, e-mail válido/único normalizado, data_nascimento
civil não futura, telefone opcional até 25 caracteres. Sem CPF/foto/sexo obrigatórios.
FUNCIONARIO: nome, e-mail, cargo (2–80), admissão e papéis operacionais; datas/status
separados da conta. Academia: nome/endereço/descrição em configuração singleton.
Idade é calculada na data de conclusão e congelada no snapshot, sem repetir data
de nascimento no prompt. Autogeração inicial limitada a adultos (18+), porque o
corpus selecionado é delimitado a esse contexto. Cadastro de menor não é proibido,
mas autogeração retorna BLOQUEADO_POR_SEGURANCA com motivo ESCOPO_ETARIO, sem
declarar doença. Fluxo manual não ganha bloqueio clínico novo implícito.

## Campos do formulário

| Campo | Tipo/unidade/validação | Obrigatório para concluir | Observação |
|---|---|---|---|
| altura_cm | Número, cm, 50–250, uma casa decimal | Sim | Limite de entrada da demonstração; não é teste de aptidão. |
| peso_kg | Número, kg, 20–350, uma casa decimal | Sim | Mesmo critério; valor fora da faixa pede correção/manual. |
| objetivo_principal | CONDICIONAMENTO / FORCA / HIPERTROFIA / ATIVIDADE_GERAL | Sim | Não gera prescrição de emagrecimento clínico ou dieta. |
| experiencia | INICIANTE / INTERMEDIARIO / AVANCADO | Sim | AVANCADO é registrado; geração especializada depende de suporte, sem inferir nível por idade. |
| nivel_atividade | SEDENTARIO / LEVE / MODERADO / ELEVADO | Sim | Autodeclarado. |
| dias_semana | Inteiro 1–6 | Sim | Máximo de dias solicitados, não obrigação de preencher todos. |
| duracao_sessao_min | Inteiro 20–120 | Sim | Disponibilidade declarada, não fórmula clínica. |
| possui_condicoes_saude / condicoes_saude | SIM / NAO / NAO_SEI + lista até 10 | Sim | SIM exige categoria/descrição/gravidade declarada; NAO ou NAO_SEI exige lista vazia. |
| usa_medicamentos / medicamentos | SIM / NAO / NAO_SEI + lista até 10 | Sim | Nome e observação; não coletar dose para calcular tratamento. |
| possui_dor_lesao_limitacao / limitacoes | SIM / NAO / NAO_SEI + lista até 8 | Sim | Região, descrição e gravidade declarada; sem diagnóstico inferido. |
| restricao_exercicio_declarada | SIM / NAO / NAO_SEI | Sim | SIM bloqueia geração conforme regra acadêmica; não abre fluxo de laudo. |
| evento_saude_importante_recente | SIM / NAO / NAO_SEI | Sim | SIM bloqueia; texto explicativo deixa claro que é relato, não avaliação médica. |
| observacoes | Texto até 1000 caracteres | Campo pode ser vazio | Não descartar alerta relevante encontrado aqui. |

Os intervalos são validações técnicas da demonstração escolhidas pelo projeto,
não limites médicos ou garantia de saúde. Rascunho aceita incompletude; concluir
exige schema completo. Responder NAO_SEI é dado válido para persistência/conclusão,
mas impede elegibilidade quando necessário à triagem; null/campo ausente não vira NAO.
Não permitir contradição SIM + lista vazia ou NAO + lista com itens.
Pydantic implementa o contrato, com testes de correspondência ao JSON Schema.
Observação vazia é string vazia; listas sem ocorrência são [].

## Resumo enviado ao modelo

Projeção em código: idade, altura/peso, objetivo, experiência, nível de atividade,
dias/duração, flags de saúde, condições/medicamentos/limitações e observações relevantes.
Preservar texto de alerta, negação, desconhecido e gravidade; remover nome/e-mail,
telefone, foto, identificadores externos e notas administrativas. Referenciar
snapshot_id/version separadamente como metadado interno.
Teto inicial do resumo: 2400 caracteres. Se alerta relevante não couber, retornar
DADOS_INSUFICIENTES com motivo CONTEXTO_EXCEDIDO; não truncar ou fazer chamada extra
só para resumir. Campos de saúde identificáveis nunca vão ao índice compartilhado.

## Decisão determinística e análise assistida

| Ordem | Condição | Estado / efeito |
|---|---|---|
| 1 | Conta/perfil sem autorização | 401/403; não iniciar IA |
| 2 | Sem onboarding concluído/schema inválido | DADOS_INSUFICIENTES; solicitar preenchimento |
| 3 | Idade menor que 18 | BLOQUEADO_POR_SEGURANCA / ESCOPO_ETARIO |
| 4 | Qualquer condição/limitação declarada GRAVE, restricao_exercicio_declarada=SIM ou evento_saude_importante_recente=SIM | BLOQUEADO_POR_SEGURANCA / ALERTA_GRAVE_DECLARADO |
| 5 | Flag necessária ou gravidade de ocorrência=NAO_SEI, contradição ou contexto excedido | DADOS_INSUFICIENTES com motivo objetivo |
| 6 | Campos explícitos não bloqueantes | Recuperar evidências pertinentes e fazer até uma análise assistida |
| 7 | LLM sinaliza indício grave na descrição livre | BLOQUEADO_POR_SEGURANCA / ALERTA_GRAVE_TEXTO; não diagnosticar |
| 8 | LLM sinaliza dúvida/contradição/lacuna de suporte | DADOS_INSUFICIENTES; não presumir saudável |
| 9 | Sem bloqueio/lacuna e com contexto válido | ELEGIVEL_PARA_GERACAO, sujeito aos recursos e suporte da geração |

Bloqueio de caso grave tem precedência sobre dado desconhecido; resposta favorável
do LLM, parecer do instrutor ou documento não remove bloqueio determinístico.
Erro/quota/timeout do provedor é falha técnica da execução, nunca elegibilidade.
É proibido concluir doença, trocar medicamento, dosear tratamento ou exigir laudo.
Declaração de medicamento/condição não grave não bloqueia por si só: a adaptação
solicitada exige evidência pertinente e ausência de conflito. Sem suporte, abster-se.
Texto livre com gravidade incerta não ganha liberação presumida.

## Alteração e versão

Cliente autenticado confirma mudança pelo contrato de MOD-03. Reabrir cria novo
rascunho baseado no snapshot anterior; concluir/confirmar cria nova versão. API
exige versão-base atual, 409 em conflito. Snapshot anterior e avaliação do instrutor
ficam preservados, triagem antiga é invalidada para novos pedidos.
Chat não escreve dados de saúde ou ficha. Pedido explícito de adaptação com novo
relato relevante leva ao formulário; somente após confirmação/versão reexecuta IA.
Avaliação do instrutor é datada e atribuída, opcional para a geração inicial.
