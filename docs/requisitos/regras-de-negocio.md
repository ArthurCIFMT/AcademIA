# Regras de negócio

| ID | Regra | Aplicação |
|---|---|---|
| RN-01 | Cada pessoa possui identidade única segundo o identificador definido pelo projeto. | Cadastro |
| RN-02 | Usuário inativo não pode autenticar-se normalmente. | Autenticação |
| RN-03 | Funcionário inativado perde permissões operacionais, mas mantém histórico. | Funcionários/Auditoria |
| RN-04 | Toda operação protegida considera papéis e permissões do usuário autenticado. | Segurança |
| RN-05 | Cliente visualiza somente dados do próprio contexto, salvo compartilhamento explícito. | Privacidade |
| RN-06 | Reconhecimento facial identifica/verifica; autorização de entrada ocorre separadamente. | Biometria/Acesso |
| RN-07 | Correspondência abaixo do limiar nunca vira identificação positiva automática. | Biometria |
| RN-08 | Deve existir fluxo alternativo para falha de reconhecimento facial. | Biometria |
| RN-09 | Liberação manual que contorne regra normal registra responsável e motivo. | Controle de acesso |
| RN-10 | Dados biométricos são tratados separadamente dos cadastrais comuns. | Dados sensíveis |
| RN-11 | Informações médicas, lesões e restrições não ficam disponíveis sem necessidade funcional. | Dados sensíveis |
| RN-12 | Cliente pode consultar treino e conversar com a IA sem aceite prévio; instrutor pode avaliar e aceitar/rejeitar posteriormente. | IA |
| RN-13 | IA não cria sugestão de treino para caso grave de saúde definido pela política. | IA/Treino |
| RN-14 | Instrutor pode modificar integralmente uma sugestão. | IA/Treino |
| RN-15 | Restrições do cliente prevalecem sobre otimizações da IA. Adaptação a condição de saúde exige evidência pertinente recuperada do corpus aprovado; sem suporte suficiente, não é gerada/publicada. | IA/Treino |
| RN-16 | IA não modifica silenciosamente conteúdo publicado; validações técnicas precedem publicação e parecer profissional é independente. | IA/Treino |
| RN-17 | Alteração proposta pela IA cria nova proposta/versão. | IA/Treino |
| RN-18 | Treinos históricos não são alterados retroativamente. A rejeitada anterior tem seu conteúdo excluído somente quando uma ficha posterior também é rejeitada, conforme RF-35; auditoria e treinos executados permanecem preservados. | Histórico |
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
| RN-33 | Exclusão/inativação não quebra relacionamentos históricos necessários. Na exclusão prevista em CA-35.7, manter referência de auditoria e snapshots de execuções, sem expor novamente o conteúdo excluído como ficha consultável. | Integridade |
| RN-34 | Dados biométricos não são enviados para relatórios operacionais comuns. | Dados sensíveis |
| RN-35 | Cliente sem matrícula existente e vigente não recebe autorização de acesso. | Controle de acesso |
| RN-36 | Liberação da catraca valida identidade, matrícula, validade, modalidade e limites de acesso. | Autorização de entrada |

## Regras que exigem detalhamento antes do módulo correspondente

- RN-01: definir UUID interno, unicidade de e-mail e eventual identificador externo.
- RN-08: definir o fluxo alternativo e quem pode executá-lo.
- RN-13: definir critérios operacionais e fontes para casos graves.
- RN-25: decidir se reservas fazem parte do escopo ou fase futura.
- RN-26: definir destinatários, canais e tratamento de falha.
- RN-36: definir modalidades e limites de acesso dos planos.
