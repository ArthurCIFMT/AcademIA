# Módulos e responsabilidades

| Código | Módulo | Responsabilidade principal |
|---|---|---|
| MOD-00 | Plataforma e arquitetura | Configuração, contratos, erros, tempo, testes, adapters de arquivos e infraestrutura. |
| MOD-01 | Identidade e pessoas | Usuários, papéis, clientes, funcionários, autenticação e autorização. |
| MOD-02 | Designação profissional | Vínculo cliente–instrutor, responsabilidade vigente e histórico. |
| MOD-03 | Onboarding e avaliações | Convites, dados físicos/saúde, avaliações versionadas e conclusão. |
| MOD-04 | Exercícios e fichas | Catálogo, prescrição, publicação, versões imutáveis e parecer profissional posterior. |
| MOD-05 | Base de conhecimento RAG | Corpus, ingestão, embeddings e ferramentas de busca/contexto documental com proveniência. |
| MOD-06 | Orquestrador e IA | Resumo de onboarding, triagem assistida, rotas fixas de RAG, geração/adaptação pelo LLM, validação e chat com orçamento. |
| MOD-07 | Biometria e acesso | API facial real, referência/captura, decisão, simulador externo de catraca, frequência e lotação. |
| MOD-08 | Planos, matrícula e financeiro | Matrícula pelo atendente sem pagamento obrigatório, validade/limites e financeiro tardio. |
| MOD-09 | Agenda e reservas | Aulas, capacidade e eventual reserva. |
| MOD-10 | Equipamentos | MVP: cadastro administrativo, disponibilidade e contrato de recursos para prescrição. |
| MOD-11 | Dashboard e relatórios | Indicadores de clientes, frequência, lotação e receita. |
| MOD-12 | Auditoria e notificações | Evidências, entrega de avisos, eventos duráveis e rastreabilidade. |

## Resultado da revisão de cobertura

Os 13 módulos cobrem o escopo pedido. As lacunas identificadas são refinamentos de
fluxo, e não justificam novos módulos: publicação independente de parecer,
biometria real com catraca fictícia e matrícula pelo atendente independente de pagamento.
Os [fluxos atualizados](fluxos-atualizados.md) prevalecem sobre a política antiga de
aprovação como pré-condição.
Veja a [análise de cobertura](revisao-modulos.md) e a [análise do MER](revisao-mer.md).

## Limites principais

- MOD-01 é proprietário das identidades e papéis; outros módulos referenciam o
  identificador, mas não manipulam credenciais. Também fecha bootstrap e primeiro acesso.
- MOD-02 é proprietário da designação vigente e de seu histórico, mas não do
  estado das fichas.
- MOD-03 é proprietário do onboarding e avaliações; expõe somente contextos
  autorizados e versionados.
- MOD-04 é proprietário do catálogo, versões, publicação e parecer por versão.
  Valida contexto/restrições antes de publicar. Parecer posterior não condiciona
  a consulta ou o chat e não reescreve o conteúdo publicado.
- MOD-05 é proprietário do corpus e da recuperação, não de dados pessoais.
  Expõe recuperação semântica por contrato; não depende do LLM ou de planner.
- MOD-06 coordena etapas fixas de dúvidas, resumo/triagem e geração/adaptação.
  Usa contratos autorizados; não há pesquisa iterativa ou planner LLM. Etapas,
  consumo e evidências são dados próprios, sem acesso direto a tabelas alheias.
- MOD-10 é proprietário do inventário/disponibilidade; MOD-04 mantém requisitos
  de recursos dos exercícios/variações e consulta MOD-10 por contrato. MOD-06
  recebe candidatos elegíveis e MOD-04 revalida antes de publicar.
- MOD-04 aplica limite de 15 versões publicadas completas por cliente; exclusão
  antiga preserva autoria/auditoria e snapshots de execuções, quando existentes.
- MOD-06 gera conteúdo e decisões técnicas por contrato; MOD-04 publica conteúdo
  validado com parecer PENDENTE, sem esperar aceite humano.
- MOD-07 separa API facial real, autorização interna e API externa fictícia de catraca.
- MOD-08 permite matrícula pelo atendente sem depender de pagamento e fornece
  validade ao motor de acesso. Registros financeiros são uma capacidade posterior.
- MOD-12 entrega avisos e registra auditoria, mas não se torna proprietário das
  entidades nem do workflow de origem.
- A exportação pertence ao módulo dono do dado, com a mesma autorização da consulta.
- MOD-06 publica por contrato de MOD-04 e solicita aviso por MOD-12 para avaliação
  posterior; não duplica estado de publicação nem atribui aceite profissional.

## Dependências essenciais

```text
MOD-00: fundação técnica
  ├── MOD-01: identidade e pessoas
  │    ├── MOD-02: designação
  │    ├── MOD-03: onboarding/avaliação
  │    ├── MOD-04: treino manual/revisão
  │    ├── MOD-10: equipamentos disponíveis no MVP
  │    └── MOD-07/08/09: extensões do domínio
  └── MOD-12: auditoria/avisos disponíveis desde a fundação

MOD-03 + MOD-04 + MOD-05 + MOD-02 + MOD-10
  └── MOD-06

MOD-08 + MOD-07
  └── decisão de acesso

Módulos entregues
  └── MOD-11: indicadores consolidados
```

As setas indicam pré-condições conceituais, não acesso direto a tabelas. MOD-12 é
usado por onboarding e revisão desde cedo; não depende de todos os módulos.
O manifesto registra o grafo exato por cartão.

## Estados globais recomendados

### Publicação e parecer de treino (dimensões independentes)

Publicação: `RASCUNHO` → `PUBLICADO` → `SUBSTITUIDO`.

Parecer por versão publicada: `PENDENTE` → `ACEITO` ou `REJEITADO`.

Validação técnica da geração tem estado próprio. Publicar exige validações técnicas,
mas não aceite profissional; publicação torna conteúdo visível. Nova versão começa
com parecer PENDENTE. Rejeitar a vigente mantém sua consulta; quando uma ficha
posterior também é rejeitada, excluir o conteúdo da rejeitada anterior e manter
a nova conforme RF-35. Apenas gerar/aceitar não dispara exclusão. Preservar
auditoria e treinos executados; aceite continua sem bloquear consulta/chat.
O limite global de RF-17 retém no máximo 15 versões publicadas completas,
incluindo vigente, removendo conteúdo mais antigo ao publicar excedente. Aplica-se
independentemente do parecer, inclusive à última rejeitada se ela expirar. A regra
de rejeitadas pode reduzir o total abaixo de 15; numeração de versão não reinicia.

### Triagem de IA

- `DADOS_INSUFICIENTES`;
- `BLOQUEADO_POR_SEGURANCA`;
- `ELEGIVEL_PARA_GERACAO`.

A triagem da demonstração não possui liberação por laudo ou aprovação médica.
Dúvida/dado faltante é DADOS_INSUFICIENTES; erro/timeout é estado técnico da execução.
Parecer posterior do instrutor é independente desses estados.

### Usuário

- `CONVIDADO`;
- `ATIVO`;
- `INATIVO`;
- `BLOQUEADO`.

Essas enumerações são propostas e devem ser confirmadas no modelo lógico.

## Integração do orquestrador

MRF01–MRF15 definem RAG semântico e LLM; os 13 módulos permanecem.
[Fluxo e contratos](rag-semantico.md) e [dados](modelo-de-dados/dados-rag-ia.md).
MOD-03 fornece snapshot, MOD-05 literatura, MOD-04 catálogo/publicação, MOD-10 recursos.
Orquestrador não equivale a pesquisa agentiva; evidência não remove bloqueio das regras acadêmicas de triagem.
