# Regras de negócio

| ID | Regra | Aplicação |
|---|---|---|
| RN-01 | Cada pessoa possui uma identidade UUID. E-mail normalizado é único entre contas ativas/inativas; perfis cliente/funcionário podem coexistir na mesma identidade, sem criar usuário duplicado. | Cadastro |
| RN-02 | Conta global INATIVA/BLOQUEADA não autentica nem usa sessão anterior. Inativação de um perfil retira apenas suas capacidades conforme ADR-002; outro perfil ativo permanece se a conta estiver ativa. | Autenticação |
| RN-03 | Perfil funcionário inativo perde operações de funcionário, preservando histórico e eventual perfil cliente ativo. Conta global inativa bloqueia ambos; papéis do frontend não anulam a restrição. | Funcionários/Auditoria |
| RN-04 | Toda operação protegida considera papéis e permissões do usuário autenticado. | Segurança |
| RN-05 | Cliente visualiza somente dados do próprio contexto, salvo compartilhamento explícito. | Privacidade |
| RN-06 | Reconhecimento facial identifica/verifica; autorização de entrada ocorre separadamente. | Biometria/Acesso |
| RN-07 | Correspondência abaixo do limiar nunca vira identificação positiva automática. | Biometria |
| RN-08 | Deve existir fluxo alternativo para falha de reconhecimento facial. | Biometria |
| RN-09 | Liberação manual que contorne regra normal registra responsável e motivo. | Controle de acesso |
| RN-10 | Dados biométricos são tratados separadamente dos cadastrais comuns. | Dados sensíveis |
| RN-11 | Informações médicas, lesões e restrições não ficam disponíveis sem necessidade funcional. | Dados sensíveis |
| RN-12 | Cliente pode consultar treino e conversar com a IA sem aceite prévio; instrutor pode avaliar e aceitar/rejeitar posteriormente. | IA |
| RN-13 | Orquestrador cruza resumo do onboarding, análise assistida e política estruturada; caso grave definido/bloqueado não recebe treino. LLM não diagnostica nem remove bloqueio determinístico. | IA/Treino |
| RN-14 | Instrutor designado pode criar ficha manual ou modificar integralmente sugestão da IA; aplica catálogo/recursos e versionamento com autoria, sem exigir disponibilidade do LLM/RAG. | IA/Treino |
| RN-15 | Restrições do cliente prevalecem sobre otimizações da IA. Adaptação a condição de saúde exige evidência pertinente recuperada do corpus aprovado; sem suporte suficiente, não é gerada/publicada. | IA/Treino |
| RN-16 | IA não modifica silenciosamente conteúdo publicado; validações técnicas precedem publicação e parecer profissional é independente. | IA/Treino |
| RN-17 | Adaptação explícita pela IA passa por triagem/validações e cria nova versão; conversa informativa nunca altera ficha silenciosamente. | IA/Treino |
| RN-18 | Treinos históricos não são reescritos retroativamente. Conteúdo antigo pode ser excluído pelo limite de 15 (RF-17/RN-38) ou substituição de rejeitada (RF-35); auditoria e registros/snapshots de treinos executados permanecem preservados. | Histórico |
| RN-19 | Falha da IA não impede montagem manual pelo instrutor. | Disponibilidade |
| RN-20 | Exercício inativo permanece em históricos, mas não é selecionável em novas prescrições. | Exercícios |
| RN-21 | Avaliações possuem data e responsável para evolução cronológica. | Avaliação |
| RN-22 | Somente planos ativos originam novas matrículas. | Planos |
| RN-23 | Informações sensíveis não aparecem desnecessariamente em logs. | Dados sensíveis |
| RN-24 | No escopo acadêmico, ausência de pagamento não bloqueia matrícula nem acesso com matrícula válida. Eventual bloqueio financeiro futuro exige decisão explícita e pertence ao motor de acesso, não ao reconhecimento facial. | Financeiro/Acesso |
| RN-25 | Aula com limite não excede capacidade sem exceção autorizada. | Agenda |
| RN-26 | Alterações críticas de permissão, biometria e configuração geram aviso. | Notificação |
| RN-27 | Autor de ação problemática não apaga livremente a própria evidência. | Auditoria |
| RN-28 | Exportações respeitam as mesmas permissões de telas e APIs. | Segurança |
| RN-29 | Dados de um cliente nunca compõem contexto de IA de outro cliente. | IA/Privacidade |
| RN-30 | Respostas da IA não são apresentadas como diagnóstico médico. | IA |
| RN-31 | Profissional responsável permanece identificável nas fichas que criou ou alterou. | Treino |
| RN-32 | Registros temporais usam padrão consistente para rastreabilidade. | Sistema |
| RN-33 | Exclusão/inativação não quebra relacionamentos históricos necessários. Nas exclusões de RF-17/RF-35, manter referência de auditoria e snapshots de execuções, sem expor novamente conteúdo excluído como ficha consultável. | Integridade |
| RN-34 | Dados biométricos não são enviados para relatórios operacionais comuns. | Dados sensíveis |
| RN-35 | Somente cliente habilitado com matrícula existente, ativa e vigente pode seguir à autorização. Matrícula ausente/futura/vencida/encerrada nega acesso; plano comprado ou rosto reconhecido sozinho não cria matrícula ou libera catraca. | Controle de acesso |
| RN-36 | Liberação da catraca valida identidade, matrícula, validade, modalidade e limites de acesso. | Autorização de entrada |
| RN-37 | Nova prescrição/adaptação só usa exercícios ativos cujos recursos obrigatórios ou alternativa completa cadastrada estão disponíveis na academia. Disponibilidade é cadastral e operacional, sem exigir controle de ocupação em tempo real. Dispensa de equipamento deve ser explícita. | Equipamentos/Treino |
| RN-38 | Cada cliente mantém no máximo 15 versões publicadas completas, incluindo a vigente. Publicar excedente exclui conteúdo das mais antigas, independentemente do parecer, sem apagar auditoria/snapshots de treinos executados. A regra de rejeitadas também se aplica e pode reduzir esse total. | Fichas/Retenção |
| RN-39 | Interface, prescrições, chat e explicações ao usuário são em português. Fontes estrangeiras são permitidas com original/idioma identificados e recuperação/tradução avaliadas; não há aprovação automática da fonte ou de uma tradução pela IA. | IA/Idioma |

## Detalhamento vigente e decisões posteriores

- RN-01/RN-02/RN-03: [ADR-002](../arquitetura/decisoes/ADR-002-identidade-e-papeis.md)
  já define identidade, unicidade e alcance de conta/perfis; não é pendência.
- RN-13: [triagem v1](onboarding-e-triagem.md) definida; ensaio real de IA futuro.
- RN-26: NTF-01 já prevê instrutor designado para ficha e administrador para
  alterações críticas, aviso interno persistente + e-mail, com falha/reenvio
  idempotente. Não depender de sucesso do e-mail para preservar pendência.
- RN-08/RN-36: detalhes de janela de acesso e alternativa manual permanecem no
  GATE-08 pós-MVP; fornecedor CompreFace, matrícula sem pagamento obrigatório e
  catraca fictícia já estão definidos.
- RN-25: reservas/capacidade são escopo futuro (GATE-07); agenda básica permanece.
- Financeiro/compra: FIN-02/GATE-09 são tardios. Compra confirmada pode preceder
  matrícula pelo atendente; o caminho acadêmico sem confirmação financeira continua.
- Exercícios: nome/variação normalizado (trim, espaços internos colapsados e lowercase)
  é único na academia, inclusive inativos. Reativar/editar registro existente evita
  duplicar identidade do movimento; descrições/prescrições históricas são snapshots.

[Auditoria de 2026-11-06](../analises/2026-11-06-auditoria-rf-rn-ia.md).
