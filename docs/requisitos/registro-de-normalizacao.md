# Registro de normalização dos requisitos

Este documento torna explícitas as mudanças de redação feitas durante a
consolidação. O propósito é preservar a origem sem carregar ambiguidades para os
prompts de implementação.

| Item | Normalização | Motivo |
|---|---|---|
| RF-03/CA-03.4 | “Cliente habilitado” passou a “elegível à biometria”. | Conta, matrícula, biometria e autorização são estados distintos. |
| RF-05 | “Perfil” passou a papéis acumuláveis. | Uma identidade pode ser cliente, administrador, atendente e/ou instrutor. |
| RF-06/CA-06.4 | SMTP em Docker saiu do critério funcional. | Containerização é requisito não funcional tardio. |
| RF-15 | “Gerar ficha” passou a “gerar proposta”. | RN-16/RN-17 e aprovação profissional impedem ativação silenciosa. |
| RF-21/CA-21.4 | Precisão foi expressa como limiar mínimo configurado de 95%. | O sistema recebe confiança externa; não implementa o algoritmo facial. |
| RF-24/RF-25 | Mantidos separados. | Cálculo de domínio e exibição são capacidades testáveis distintas. |
| RF-28/RF-29 | “Lucro” passou a faturamento/receita. | Sem despesas não existe cálculo de lucro. |
| RF-31 | Acrescentados validade e histórico da matrícula. | Requisito original possuía somente um critério insuficiente para o domínio. |
| RF-34/RF-35 | Acrescentados. | Solicitação posterior confirmou designação de instrutor e aprovação da IA. |
| MRF01 | Remoção genérica de caracteres virou preservação semântica. | Símbolos e unidades podem ser relevantes para o conteúdo. |
| MRF02 | Mantida similaridade de cosseno e acrescentada abstenção. | Preserva requisito original e trata recuperação insuficiente. |
| MRF04 | Triagem foi colocada antes dos agentes geradores. | Casos bloqueados não devem chegar à geração. |
| MRF05 | Limites também passaram a regras estruturadas. | Banco vetorial/LLM não garante invariantes matemáticas. |
| MRF06 | Rejeições também são persistidas. | Auditoria exige registrar tentativas, sem ativá-las. |
| MRF08–MRF15 | Marcados como derivados e pendentes. | Foram propostos na análise, não fornecidos inicialmente como tabela aprovada. |

O texto original permanece recuperável no histórico da conversa e no material
fonte. Antes de FND-01 ser concluído, o responsável deve aceitar as normalizações
ou solicitar ajustes.
