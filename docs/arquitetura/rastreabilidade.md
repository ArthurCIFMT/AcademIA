# Matriz inicial de rastreabilidade

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

## Lacunas controladas

| Lacuna | Tratamento planejado |
|---|---|
| Regra acadêmica de caso grave | Definida em onboarding-e-triagem.md; ensaio de AI-06 ainda futuro, sem liberação médica formal. |
| Reserva/capacidade de aula | Prompt opcional condicionado à validação de escopo. |
| Destinatários de avisos críticos | Definir antes do módulo de notificações. |
| Fluxo alternativo de biometria | Definir antes de ACS-04. |
| Provedor de LLM/embeddings | Porta/adaptador; escolha em ADR. |
| Execução local de serviços sem Docker | Definir no gate de infraestrutura local. |
| Cálculo de lucro | Fora do modelo atual; usar receita/faturamento. |

## Regra de manutenção

Todo prompt operacional deve declarar os IDs cobertos. Ao concluir uma entrega,
esta matriz deve ser atualizada com o prompt, teste ou evidência correspondente.

## Cobertura dos requisitos não funcionais

- RNF-01–RNF-06: FND-02B, FND-04, FND-06 e FND-07.
- RNF-07: transversal a todos os prompts de implementação e VAL-02.
- RNF-08–RNF-09: FND-06, IAM-01 e NTF-01.
- RNF-10–RNF-12: GATE-06 e INF-01–INF-04.
- RNF-13: RAG-05 e AI-06.
- RNF-14: prompts de interface e VAL-02.
- RNF-15–RNF-17: FND-06, FND-08 e integrações correspondentes.

## Orquestrador semântico

MRF01–MRF15 e 67 critérios governam MOD-05/06. [Cenários](../testes/rag-ia-semantico.md)
cobrem dúvidas, resumo sem perda de alertas, triagem, geração, limites e fontes.
RF-38/TRN-01 formalizam catálogo; RNF-18/AI-02/AI-06 cobrem orçamento/tempo.
Atribuição de prompt não comprova implementação ou ensaio real.
