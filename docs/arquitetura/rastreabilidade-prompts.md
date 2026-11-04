# Rastreabilidade dos prompts

Matriz vigente de cartões → módulos → requisitos; atribuição não comprova implementação.
[Manifesto](../prompts/README.md) registra sequência/gates. AI-03 depende do serviço
de publicação TRN-03 e AI-05 do formulário de atualização ONB-03.

| Prompt | Módulos | Requisitos |
|---|---|---|
| [FND-01](../prompts/01-fundacao/FND-01-fontes-de-verdade.md) | MOD-00–MOD-12 | RF-01–RF-38, RN-01–RN-39, RNF-01–RNF-18, MRF01–MRF15 |
| [FND-02A](../prompts/01-fundacao/FND-02A-propostas-de-adrs.md) | MOD-00 | RNF-01–RNF-18 e requisitos técnicos transversais |
| [FND-02B](../prompts/01-fundacao/FND-02B-aprovacao-dos-gates.md) | MOD-00 | RNF-01–RNF-18, MRF01–MRF15 |
| [FND-03](../prompts/01-fundacao/FND-03-modelo-logico.md) | MOD-01–MOD-12 | RF-01–RF-38, RN-01–RN-39, MRF01–MRF15 |
| [FND-04](../prompts/01-fundacao/FND-04.md) | MOD-00 | RNF-02, RNF-04, RNF-07, RNF-08, RNF-10 |
| [FND-05](../prompts/01-fundacao/FND-05.md) | MOD-00 | RNF-03, RNF-07, RNF-10, RNF-16; RN-33 |
| [FND-06](../prompts/01-fundacao/FND-06.md) | MOD-00 | RNF-04, RNF-06, RNF-07, RNF-15, RNF-16; RN-23, RN-32 |
| [FND-07](../prompts/01-fundacao/FND-07.md) | MOD-00 | RNF-01, RNF-07, RNF-08, RNF-10, RNF-14 |
| [FND-08](../prompts/01-fundacao/FND-08.md) | MOD-00, MOD-12 | RN-23, RN-26, RN-27, RN-32, RN-33; RNF-06, RNF-15, RNF-17 |
| [IAM-01](../prompts/02-identidade-pessoas/IAM-01.md) | MOD-01 | RF-04; RN-02, RN-04; RNF-08 |
| [IAM-02](../prompts/02-identidade-pessoas/IAM-02.md) | MOD-01 | RF-01, RF-04, RF-05, RF-07; RN-01, RN-02, RN-03, RN-33 |
| [IAM-03](../prompts/02-identidade-pessoas/IAM-03.md) | MOD-01 | RF-05; RN-04, RN-05, RN-11, RN-28, RN-29 |
| [IAM-04](../prompts/02-identidade-pessoas/IAM-04.md) | MOD-01 | RF-04, RF-05; RN-02, RN-04; RNF-14 |
| [IAM-05](../prompts/02-identidade-pessoas/IAM-05.md) | MOD-01, MOD-12 | RF-06; RN-02; RNF-09, RNF-15 |
| [NTF-01](../prompts/02-identidade-pessoas/NTF-01.md) | MOD-12 | RF-09, RF-35; RN-23, RN-26, RN-27; RNF-09, RNF-17 |
| [PES-01](../prompts/02-identidade-pessoas/PES-01.md) | MOD-01 | RF-07, RF-08; RN-01, RN-03, RN-04, RN-26, RN-33 |
| [PES-02](../prompts/02-identidade-pessoas/PES-02.md) | MOD-01 | RF-01, RF-02, RF-03; RN-01, RN-04, RN-05, RN-33 |
| [PES-03](../prompts/02-identidade-pessoas/PES-03.md) | MOD-02 | RF-34; RN-03, RN-04, RN-11, RN-31, RN-33 |
| [ONB-01](../prompts/03-onboarding/ONB-01.md) | MOD-03, MOD-12 | RF-09, RF-10; RN-05, RN-23; RNF-09, RNF-17 |
| [ONB-02](../prompts/03-onboarding/ONB-02.md) | MOD-03 | RF-11, RF-12, RF-13, RF-14; RN-11, RN-21, RN-32, RN-33; MRF03 |
| [ONB-03](../prompts/03-onboarding/ONB-03.md) | MOD-03 | RF-10, RF-11, RF-12, RF-13, RF-14; RN-05, RN-11; RNF-14 |
| [ONB-04](../prompts/03-onboarding/ONB-04.md) | MOD-02, MOD-03 | RF-12, RF-14, RF-34; RN-11, RN-21, RN-31, RN-33; MRF03, MRF12 |
| [TRN-01](../prompts/04-treinos/TRN-01.md) | MOD-04, MOD-10 | RF-15, RF-19, RF-32, RF-38; RN-20, RN-31, RN-33, RN-37; MRF05, MRF09 |
| [TRN-02](../prompts/04-treinos/TRN-02.md) | MOD-04 | RF-17; RN-14, RN-18, RN-19, RN-20, RN-31, RN-33, RN-37, RN-38 |
| [TRN-03](../prompts/04-treinos/TRN-03.md) | MOD-04, MOD-02, MOD-12 | RF-17, RF-35; RN-12, RN-14, RN-16, RN-17, RN-18, RN-31, RN-37, RN-38 |
| [TRN-04](../prompts/04-treinos/TRN-04.md) | MOD-04 | RF-16, RF-17; RN-05, RN-28, RN-37, RN-38, RN-39; MRF07 |
| [AI-01](../prompts/05-ia-rag/AI-01.md) | MOD-06, MOD-10 | RF-15, RF-19; RN-13, RN-15, RN-29, RN-30, RN-37; MRF03, MRF08, MRF09, MRF12 |
| [AI-02](../prompts/05-ia-rag/AI-02.md) | MOD-06 | MRF03–MRF06, MRF08, MRF11, MRF12, MRF15; RN-15, RN-16; RNF-06, RNF-18 |
| [AI-03](../prompts/05-ia-rag/AI-03.md) | MOD-06, MOD-04, MOD-10 | RF-15, RF-17; RN-13, RN-15, RN-16, RN-17, RN-19, RN-37, RN-38, RN-39; MRF04, MRF05, MRF06, MRF08, MRF09, MRF11, MRF12, MRF15 |
| [AI-04](../prompts/05-ia-rag/AI-04.md) | MOD-06, MOD-04, MOD-12 | RF-15, RF-34, RF-35; RN-12, RN-14, RN-16, RN-26, RN-31; MRF10 |
| [AI-05](../prompts/05-ia-rag/AI-05.md) | MOD-06 | RF-18, RF-19; RN-15, RN-16, RN-17, RN-18, RN-29, RN-30, RN-37, RN-38, RN-39; MRF14 |
| [AI-06](../prompts/05-ia-rag/AI-06.md) | MOD-05, MOD-06, MOD-04, MOD-10 | RF-15, RF-17, RF-18, RF-19, RF-32, RF-35, RF-38; RN-37, RN-38, RN-39; MRF04, MRF08, MRF09, MRF11, MRF12, MRF13; RNF-07, RNF-18 |
| [RAG-01](../prompts/05-ia-rag/RAG-01.md) | MOD-05 | MRF01, MRF11, MRF15; RN-23, RN-28 |
| [RAG-02](../prompts/05-ia-rag/RAG-02.md) | MOD-05 | MRF01, MRF02; RN-39; RNF-05, RNF-08, RNF-10 |
| [RAG-03](../prompts/05-ia-rag/RAG-03.md) | MOD-05 | MRF01, MRF11, MRF15 |
| [RAG-04](../prompts/05-ia-rag/RAG-04.md) | MOD-05 | MRF01, MRF11, MRF15; RNF-17 |
| [RAG-05](../prompts/05-ia-rag/RAG-05.md) | MOD-05 | MRF02, MRF11, MRF12, MRF15; RN-29, RN-39; RNF-13 |
| [TST-01](../prompts/05-ia-rag/TST-01.md) | MOD-00, MOD-01, MOD-02, MOD-03, MOD-04, MOD-05, MOD-06, MOD-10, MOD-12 | RF-01–RF-19, RF-32, RF-33, RF-34, RF-35, RF-38; RN-37, RN-38, RN-39; RNF-07, RNF-10, RNF-14, RNF-18; MRF03–MRF06, MRF08–MRF14 |
| [ACS-01](../prompts/06-acesso/ACS-01.md) | MOD-07 | RF-03, RF-22; RN-10, RN-26, RN-34 |
| [ACS-02](../prompts/06-acesso/ACS-02.md) | MOD-07 | RF-20, RF-21, RF-36; RN-06, RN-07; RNF-04, RNF-17 |
| [ACS-03](../prompts/06-acesso/ACS-03.md) | MOD-07, MOD-08 | RF-21, RF-36, RF-37; RN-06, RN-07, RN-24, RN-35, RN-36 |
| [ACS-04](../prompts/06-acesso/ACS-04.md) | MOD-07, MOD-12 | RN-08, RN-09, RN-27, RN-35, RN-36 |
| [ACS-05](../prompts/06-acesso/ACS-05.md) | MOD-07 | RF-23, RF-24; RN-32, RN-33; RNF-17 |
| [ACS-06](../prompts/06-acesso/ACS-06.md) | MOD-07 | RF-23, RF-25; RN-04, RN-05, RN-28, RN-34; RNF-14 |
| [ACS-07](../prompts/06-acesso/ACS-07.md) | MOD-07 | RF-37; RN-06, RN-09, RN-32; RNF-04, RNF-17 |
| [MEM-00](../prompts/06-acesso/MEM-00.md) | MOD-08 | RF-26 parcialmente; RN-04, RN-27, RN-33 |
| [MEM-01](../prompts/06-acesso/MEM-01.md) | MOD-08 | RF-31 parcialmente; RN-22, RN-35, RN-36 |
| [AUL-01](../prompts/07-complementares/AUL-01.md) | MOD-09 | RF-30; RN-04, RN-32, RN-33; RNF-14 |
| [AUL-02](../prompts/07-complementares/AUL-02.md) | MOD-09 | RN-25; RF complementar de reservas a aprovar |
| [DSH-01](../prompts/07-complementares/DSH-01.md) | MOD-11 | RF-28, RF-29; RN-04, RN-23, RN-28, RN-34 |
| [EQP-01](../prompts/07-complementares/EQP-01.md) | MOD-10 | RF-15, RF-19, RF-32, RF-33, RF-38; RN-04, RN-33, RN-37; RNF-14 |
| [FIN-01](../prompts/08-financeiro/FIN-01.md) | MOD-08 | RF-26, RF-27; RN-04, RN-05, RN-24, RN-33 |
| [FIN-02](../prompts/08-financeiro/FIN-02.md) | MOD-08 | RF-31; RN-22, RN-24, RN-35; RNF-17 |
| [FIN-03](../prompts/08-financeiro/FIN-03.md) | MOD-08, MOD-11 | RF-28, RF-29; RN-04, RN-28, RN-32 |
| [INF-01](../prompts/09-infraestrutura/INF-01.md) | MOD-00 | RNF-10, RNF-11; RNF-08 |
| [INF-02](../prompts/09-infraestrutura/INF-02.md) | MOD-00 | RNF-05, RNF-09, RNF-11, RNF-12 |
| [INF-03](../prompts/09-infraestrutura/INF-03.md) | MOD-00 | RNF-08, RNF-11, RNF-12, RNF-15 |
| [INF-04](../prompts/09-infraestrutura/INF-04.md) | MOD-00 | RNF-07, RNF-10, RNF-11, RNF-12 |
| [VAL-01](../prompts/10-validacao-final/VAL-01.md) | MOD-00–MOD-12 | RF-01–RF-38; RN-01–RN-39; RNF-01–RNF-18; MRF01–MRF15 e critérios vigentes |
| [VAL-02](../prompts/10-validacao-final/VAL-02.md) | MOD-00–MOD-12 conforme escopo | RNF-07 e critérios dos módulos selecionados |
| [VAL-03](../prompts/10-validacao-final/VAL-03.md) | MOD-00 | RNF-10, RNF-11; contexto acadêmico |

## Escopo vigente

MRF01–MRF15 são vigentes; os MRFs agentivos retirados não são executáveis.
RF-38/TRN-01 cobrem catálogo; RNF-18/AI-02/AI-06 cobrem tempo e chamadas.
A [revisão didática](../analises/2026-11-04-revisao-didatica-e-consistencia.md)
registra a dispensa de aprovação médica formal e as correções de contratos.
