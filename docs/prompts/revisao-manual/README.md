# Revisão manual do AcademIA

Use este pacote com o repositório do AcademIA aberto. As etapas 01 a 09 registram a revisão manual anterior. Para tratar as falhas de integração da auditoria de 27/11/2026, comece pelo 10 e execute um prompt por rodada.

| Ordem | Prompt | Depende de |
|---|---|---|
| 01 | [Revisão inicial e reprodução](01-revisao-inicial.md) | Relato do teste manual |
| 02 | [Navegação por papel](02-navegacao.md) | 01 |
| 03 | [Meu perfil e endereço](03-meu-perfil.md) | 01, 02 |
| 04 | [Envio e reconhecimento facial](04-biometria.md) | 01 |
| 05 | [Matrícula e acesso na ficha do cliente](05-matricula-e-acesso.md) | 01, 02, 04 |
| 06 | [Idade durante o onboarding](06-idade-onboarding.md) | 01 |
| 07 | [Triagem e respostas “Não sei”](07-triagem.md) | 01 |
| 08 | [Foto privada no perfil](08-foto-no-perfil.md) | 01, 03, 04 |
| 09 | [Revisão final antes do VAL-02](09-revisao-final.md) | Mudanças executadas com evidência e registro das pendências |
| 10 | [Verificação da revisão do Alembic](10-revisao-alembic.md) | Auditoria de 27/11/2026 |
| 11 | [Matrícula sem módulo financeiro](11-matricula-sem-financeiro.md) | Auditoria de 27/11/2026 |

A [nota da auditoria](auditoria-2026-11-27.md) registra a reprodução e a evidência dos dois casos. As correções 10 e 11 são independentes. A execução de VAL-02 segue o manifesto oficial.

## Regras comuns de execução

- Leia o `AGENTS.md` vigente, a visão geral e os capítulos pertinentes do `SPEC.md`, o prompt mestre, o contexto e o contrato operacional de `docs/prompts/`. Consulte o manifesto para identificar o estado real da entrega e preserve as mudanças em andamento no checkout.
- Execute apenas o prompt escolhido. Este pacote complementa a especificação, os prompts operacionais, os gates e o VAL-02.
- Os prompts 01 e 09 são revisões. Os prompts 02 a 08 autorizam a implementação do seu escopo quando selecionados. Use a lista de caminhos de cada um como limite. Dependências, contratos e configurações de outros módulos seguem as condições do AGENTS.md.
- Em mudança de comportamento, atualize apenas requisitos, decisões, contratos e fontes do SPEC diretamente afetados. Registre as evidências em `docs/testes/` quando pertinente. Recompile o SPEC pelas fontes e use `python scripts/gerar_spec.py --check`.
- Resolva os comandos pela estratégia e pelo registro em `docs/testes/`. Use PostgreSQL de teste, fixtures sintéticas e evidência sanitizada. Diferencie stub, integração real e verificação manual. Preserve os relatórios históricos. Nenhum ensaio deve copiar dados, fotos ou segredos da instalação de uso.
- Preserve a aplicação local, as contas existentes, os dois iniciadores, o fluxo financeiro simulado e a aprovação posterior de fichas. Docker fica restrito ao CompreFace dedicado. Evite alterações no iniciador, salvo quando necessárias no escopo autorizado.
- Toda operação sobre Git segue GATE-05 e a autorização da conversa. Publique evidências sanitizadas, mantendo logs privados e o relatório detalhado de uso na pasta local.

## Relatório ao terminar uma etapa

Siga o formato do `AGENTS.md`. Em até oito linhas, informe arquivos alterados, testes executados, resultados e pendências.
