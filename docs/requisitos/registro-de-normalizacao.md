# Registro de normalização dos requisitos

Este documento torna explícitas as mudanças de redação feitas durante a
consolidação. O propósito é preservar a origem sem carregar ambiguidades para os
prompts de implementação.

| Item | Normalização | Motivo |
|---|---|---|
| RF-03/CA-03.4 | “Cliente habilitado” passou a “elegível à biometria”. | Conta, matrícula, biometria e autorização são estados distintos. |
| RF-05 | “Perfil” passou a papéis acumuláveis. | Uma identidade pode ser cliente, administrador, atendente e/ou instrutor. |
| RF-06/CA-06.4 | SMTP em Docker saiu do critério funcional. | Containerização é requisito não funcional tardio. |
| RF-15/RF-16/RF-17/RF-19/RF-35 | Publicação tecnicamente validada independe do aceite posterior do instrutor. | Correção explícita do responsável: cliente vê treino e usa chat antes do parecer. |
| RF-21/CA-21.4 | Limiar inicial de correspondência de 95%, separado da detecção/qualidade. | Não equivale à acurácia de 95%; a métrica é mapeada pelo adapter facial. |
| RF-24/RF-25 | Mantidos separados. | Cálculo de domínio e exibição são capacidades testáveis distintas. |
| RF-28/RF-29 | “Lucro” passou a faturamento/receita. | Sem despesas não existe cálculo de lucro. |
| RF-31 | Atendente matricula/renova sem exigir pagamento confirmado, comprovante ou módulo financeiro. | Correção explícita do responsável para o projeto acadêmico; substitui a exigência anterior. |
| RF-34/RF-35 | Designação preservada; avaliação profissional agora posterior e independente. | Solicitações posteriores do responsável; rejeição permanece identificada sem ocultar treino/chat. |
| RF-36/RF-37 | Acrescentados reconhecimento facial real e API de catraca fictícia. | Solicitação explícita: referência após matrícula, captura nova, decisão e passagem simulada. |
| MRF01 | Remoção genérica de caracteres virou preservação semântica. | Símbolos e unidades podem ser relevantes para o conteúdo. |
| MRF02 | Mantida similaridade de cosseno e acrescentada abstenção. | Preserva requisito original e trata recuperação insuficiente. |
| MRF04 | Triagem foi colocada antes dos agentes geradores. | Casos bloqueados não devem chegar à geração. |
| MRF05 | Limites também passaram a regras estruturadas. | Banco vetorial/LLM não garante invariantes matemáticas. |
| MRF06 | Rejeições também são persistidas. | Auditoria registra tentativas sem confundi-las com conteúdo validado/publicado. |
| MRF08–MRF15 | Marcados como derivados e pendentes. | Foram propostos na análise, não fornecidos inicialmente como tabela aprovada. |

O texto original permanece recuperável no histórico da conversa e no material
fonte. Antes de FND-01 ser concluído, o responsável deve aceitar as normalizações
ou solicitar ajustes.
