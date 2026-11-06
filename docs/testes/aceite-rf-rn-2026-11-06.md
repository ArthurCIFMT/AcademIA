# Regressões de aceitação RF/RN — 2026-11-06

Plano, não resultado de testes da aplicação. Cada prompt implementa os testes do
próprio escopo e registra comandos reais em [comandos](comandos.md).
Usar apenas clientes/funcionários sintéticos, PostgreSQL de teste isolado e
provedor real/sandbox no aceite correspondente. Não antecipar pagamento ou Docker.

| Cenário | Critérios/regras | Resultado esperado | Prompts / nível |
|---|---|---|---|
| E-mail ativo/inativo repetido e pessoa já funcionária | CA-01.2; RN-01 | Outra identidade é recusada; perfil autorizado reutiliza identidade sem criar sessão/conta duplicada. | IAM-02/PES-02; BE/INT/API |
| Inativar conta, cliente ou funcionário acumulado | CA-03.2, CA-08.3, CA-05.4; RN-02/RN-03 | Conta bloqueia tudo; perfil isolado retira só suas capacidades na próxima requisição. | IAM-01/IAM-03/PES-01; BE/INT/API |
| Logout/expiração/revogação, CSRF e recuperação | CA-04.4/CA-04.5, CA-06.4 | Sessões inválidas negadas; mutação sem origem/CSRF falha; recuperação não enumera contas e revoga sessões. | IAM-01/IAM-05; BE/INT/API |
| Convite trocado/reutilizado e acesso além do formulário | CA-10.4; RF-10 | Token não permite login geral ou acesso a terceiro; expiração/consumo seguem o contrato. | ONB-01; BE/INT/API |
| SIM sem detalhe, NAO/NAO_SEI e campo ausente | CA-12.4/CA-13.4; MRF03/MRF08 | Validar schema; ausência não vira saudável; conclusão estrutural não implica elegibilidade. | ONB-02/AI-01/AI-06; BE/INT/IA |
| Replay de geração, chave com entrada diferente | CA-15.12 | Não repete chamada/publicação; divergência dá conflito. | AI-02/AI-03/AI-06; BE/INT/IA |
| Quota/chave ausente/timeout/cancelamento/JSON inválido | CA-15.13; MRF04/MRF15 | Encerra execução sem alterar vigente, resposta tardia não publica e não existe retry/fallback pago oculto. | AI-02/AI-06; BE/INT/IA |
| Ficha manual com LLM, embeddings e vetorial indisponíveis | CA-15.11/CA-15.14; RN-14/RN-19 | Instrutor designado monta e publica com autoria/recursos/versão; cliente ou instrutor alheio não publica. | TRN-02/TRN-03/AI-06; BE/INT/E2E |
| Instrução maliciosa e IDs de outro cliente | CA-18.8; RN-29; MRF12 | Não remove bloqueio, muda permissão, escreve domínio ou recupera conversa alheia. | IAM-03/AI-05/AI-06; BE/API/IA |
| Evento facial duplicado com payload alterado | CA-20.5 | Origem não confiável é negada; conflito não reprocessa evento. | ACS-02/ACS-04; BE/INT/API |
| Compra paga sem matrícula e matrícula válida sem pagamento | CA-21.5/CA-21.6/CA-31.9 | Compra não libera; matrícula válida passa ao motor sem dependência financeira, sujeita às demais regras. | MEM-01/ACS-03/FIN-02; BE/INT/API |
| Face conhecida com conta inativa, matrícula futura/vencida, limite/modalidade inválidos | CA-21.5; RN-35/RN-36 | DENY com motivo, sem comando de liberação válido. | ACS-03; BE/INT/API |
| Cadastrar face sem matrícula e falhar na troca | RF-22/CA-22.4 | Sem matrícula recusa; falha externa não declara troca concluída nem perde referência anterior silenciosamente. | ACS-01; BE/INT/API |
| ALLOW/ack sem passagem, repetição de entrada ou saída órfã | CA-23.5/CA-24.5 | Só passagem válida correlacionada altera presença; replay/inconsistência não duplica ou negativa lotação. | ACS-04/ACS-05; BE/INT/API |
| Compra própria, plano inativo e callback fora de ordem | CA-31.7–CA-31.9, CA-26.4 | Contratação válida associa plano/cliente/valor; confirmar só via origem autenticada, sem duplicar/recuar estado ou matricular automaticamente. | FIN-01/FIN-02; BE/INT/API |
| Trocar instrutor e registrar parecer concorrente | CA-34.5/CA-35.10 | Apenas responsável vigente autorizado; motivo na rejeição, histórico preservado, sem dois principais. | PES-03/TRN-03; BE/INT/API |
| Nome/variação de exercício com espaços/caixa e registro inativo | CA-38.1 | Nome normalizado único em transação/constraint; nenhuma duplicata ou reutilização de ID. | TRN-01; BE/INT/API |

Não substitui [SV-01–SV-24](rag-ia-semantico.md), casos de triagem, retenção de 15,
evidência pertinente para adaptação, PT/EN, teste facial real ou ensaio de latência.
Mocks conferem comportamento controlado; AI-06 e ACS-02 registram as evidências reais.
