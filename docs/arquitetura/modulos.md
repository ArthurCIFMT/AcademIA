# Módulos e responsabilidades

| Código | Módulo | Responsabilidade principal |
|---|---|---|
| MOD-00 | Plataforma e arquitetura | Configuração, contratos, erros, tempo, testes, adapters de arquivos e infraestrutura. |
| MOD-01 | Identidade e pessoas | Usuários, papéis, clientes, funcionários, autenticação e autorização. |
| MOD-02 | Designação profissional | Vínculo cliente–instrutor, responsabilidade vigente e histórico. |
| MOD-03 | Onboarding e avaliações | Convites, dados físicos/saúde, avaliações versionadas e conclusão. |
| MOD-04 | Exercícios e fichas | Catálogo, prescrição, publicação, versões imutáveis e parecer profissional posterior. |
| MOD-05 | Base de conhecimento RAG | Documentos, chunking, embeddings, busca e evidências. |
| MOD-06 | IA e adaptação | Triagem, regras, agentes, geração, revisão automática, chat e propostas. |
| MOD-07 | Biometria e acesso | API facial real, referência/captura, decisão, simulador externo de catraca, frequência e lotação. |
| MOD-08 | Planos, matrícula e financeiro | Matrícula pelo atendente sem pagamento obrigatório, validade/limites e financeiro tardio. |
| MOD-09 | Agenda e reservas | Aulas, capacidade e eventual reserva. |
| MOD-10 | Equipamentos | Cadastro administrativo e consulta de equipamentos ativos. |
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
  │    └── MOD-07/08/09/10: extensões do domínio
  └── MOD-12: auditoria/avisos disponíveis desde a fundação

MOD-03 + MOD-04 + MOD-05 + MOD-02
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

### Triagem de IA

- `DADOS_INSUFICIENTES`;
- `BLOQUEADO_POR_SEGURANCA`;
- `REQUER_LIBERACAO_PROFISSIONAL`;
- `ELEGIVEL_PARA_GERACAO`.

### Usuário

- `CONVIDADO`;
- `ATIVO`;
- `INATIVO`;
- `BLOQUEADO`.

Essas enumerações são propostas e devem ser confirmadas no modelo lógico.
