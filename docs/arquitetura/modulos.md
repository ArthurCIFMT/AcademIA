# Módulos e responsabilidades

| Código | Módulo | Responsabilidade principal |
|---|---|---|
| MOD-00 | Plataforma e arquitetura | Configuração, contratos, erros, tempo, testes, adapters de arquivos e infraestrutura. |
| MOD-01 | Identidade e pessoas | Usuários, papéis, clientes, funcionários, autenticação e autorização. |
| MOD-02 | Designação profissional | Vínculo cliente–instrutor, responsabilidade vigente e histórico. |
| MOD-03 | Onboarding e avaliações | Convites, dados físicos/saúde, avaliações versionadas e conclusão. |
| MOD-04 | Exercícios e fichas | Catálogo, ficha manual, itens, versões, histórico e aprovação. |
| MOD-05 | Base de conhecimento RAG | Documentos, chunking, embeddings, busca e evidências. |
| MOD-06 | IA e adaptação | Triagem, regras, agentes, geração, revisão automática, chat e propostas. |
| MOD-07 | Biometria e acesso | Referência facial, eventos externos, decisão, frequência e lotação. |
| MOD-08 | Planos, matrícula e financeiro | Plano, matrícula, validade, limites, cobrança e pagamento tardio. |
| MOD-09 | Agenda e reservas | Aulas, capacidade e eventual reserva. |
| MOD-10 | Equipamentos | Cadastro administrativo e consulta de equipamentos ativos. |
| MOD-11 | Dashboard e relatórios | Indicadores de clientes, frequência, lotação e receita. |
| MOD-12 | Auditoria e notificações | Evidências, entrega de avisos, eventos duráveis e rastreabilidade. |

## Resultado da revisão de cobertura

Os 13 módulos cobrem o escopo pedido. As lacunas identificadas são refinamentos de
fluxo, e não justificam novos módulos: bootstrap/primeiro acesso, atualidade da
proposta antes da aprovação e dependências da interface de notificações.
Veja a [análise de cobertura](revisao-modulos.md) e a [análise do MER](revisao-mer.md).

## Limites principais

- MOD-01 é proprietário das identidades e papéis; outros módulos referenciam o
  identificador, mas não manipulam credenciais. Também fecha bootstrap e primeiro acesso.
- MOD-02 é proprietário da designação vigente e de seu histórico, mas não do
  estado das fichas.
- MOD-03 é proprietário do onboarding e avaliações; expõe somente contextos
  autorizados e versionados.
- MOD-04 é proprietário do catálogo, versões, workflow de revisão e decisão de
  aprovação/rejeição. Antes de ativar uma proposta, verifica compatibilidade com
  avaliação/restrições e versão-base segundo política de atualidade definida.
- MOD-05 é proprietário do corpus e da recuperação, não de dados pessoais.
- MOD-06 cria propostas e decisões de fluxo, nunca uma ficha ativa diretamente.
- MOD-07 separa reconhecimento externo de autorização interna.
- MOD-08 fornece estado de matrícula ao motor de acesso.
- MOD-12 entrega avisos e registra auditoria, mas não se torna proprietário das
  entidades nem do workflow de origem.
- A exportação pertence ao módulo dono do dado, com a mesma autorização da consulta.
- MOD-06 submete propostas de IA ao workflow de MOD-04 e solicita aviso por
  MOD-12; não duplica o mecanismo de aprovação.

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

### Proposta/ficha

`RASCUNHO` → `AGUARDANDO_REVISAO` → `EM_REVISAO` → `APROVADA` → `ATIVA`

Saídas alternativas: `AJUSTES_SOLICITADOS`, `REJEITADA`, `SUBSTITUIDA`.

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
