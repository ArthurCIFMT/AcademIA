# Revisão manual do AcademIA

Os cartões 01 a 11 estão concluídos e podem ser reutilizados como roteiros de
regressão. O cartão 12 está pronto para checagens recorrentes de segurança.
Escolha o cartão do fluxo em avaliação e use contas sintéticas. Se houver
regressão reproduzida, aplique apenas a correção autorizada, em rodada própria.

| Cartão | Fluxo | Estado |
|---|---|---|
| 01 | [Revisão inicial e reprodução](01-revisao-inicial.md) | CONCLUÍDO |
| 02 | [Navegação por papel](02-navegacao.md) | CONCLUÍDO |
| 03 | [Meu perfil e endereço](03-meu-perfil.md) | CONCLUÍDO |
| 04 | [Envio e reconhecimento facial](04-biometria.md) | CONCLUÍDO |
| 05 | [Matrícula e acesso na ficha do cliente](05-matricula-e-acesso.md) | CONCLUÍDO |
| 06 | [Idade durante o onboarding](06-idade-onboarding.md) | CONCLUÍDO |
| 07 | [Triagem e respostas “Não sei”](07-triagem.md) | CONCLUÍDO |
| 08 | [Foto privada no perfil](08-foto-no-perfil.md) | CONCLUÍDO |
| 09 | [Conferência integrada antes do VAL-02](09-revisao-final.md) | CONCLUÍDO |
| 10 | [Verificação da revisão do Alembic](10-revisao-alembic.md) | CONCLUÍDO |
| 11 | [Matrícula sem módulo financeiro](11-matricula-sem-financeiro.md) | CONCLUÍDO |
| 12 | [Segurança básica do site](12-seguranca-basica.md) | PRONTO |

O registro dos fluxos está em `docs/testes/comandos.md`, nas seções de revisão
após VAL-01, Revisão 10 e Revisão 11. A [nota da auditoria](auditoria-2026-11-27.md)
preserva o diagnóstico inicial. O teste manual do responsável pode ocorrer
antes da próxima rodada operacional. A aceitação integral de VAL-02 segue o
manifesto oficial.

## Regras comuns de execução

- Leia o AGENTS.md, os trechos do SPEC e o contrato operacional aplicáveis ao
  cartão. Use 01, 09 e 12 apenas para diagnóstico e verificação. Se encontrarem uma
  falha, retorne ao cartão de correção correspondente.
- Rode as verificações nas pastas indicadas, com os ambientes já provisionados.
  As integrações usam a URL de `academia_test`; o teste de convites requer
  Mailpit isolado. Configure apenas as variáveis necessárias no processo de
  teste. Os comandos e pré-requisitos de cada ambiente estão em
  `docs/testes/comandos.md`. Um caso obrigatório pulado fica pendente na rodada.
- No Windows, se o ambiente `.venv` já estiver provisionado e o `uv` não estiver
  no PATH, execute em `backend/` com `& ./.venv/Scripts/python.exe -m pytest`
  no lugar de `uv run --locked pytest`. Para o runner, use
  `& ./.venv/Scripts/python.exe -m tests.acceptance` com os mesmos argumentos.
- Use contas, fotos e dados de saúde sintéticos. Separe evidência de serviço
  real, simulador, dublê e inspeção manual. Compare o cenário observado com o
  resultado esperado, identifique a revisão e preserve as evidências anteriores.
- Para uma correção, limite o diff aos caminhos do cartão e à documentação
  diretamente afetada. Se precisar mudar um contrato fora do escopo, registre a
  dependência. Mantenha o banco de uso, as configurações privadas e as migrations
  já aplicadas preservados. Siga o AGENTS.md para avaliar o iniciador e verificar
  ou recompilar a SPEC.
- Toda operação sobre Git segue GATE-05 e a autorização da conversa. Publique
  evidência sanitizada. Relatórios detalhados, fotos, dados e logs privados
  permanecem no ambiente local.

## Jornadas de navegador

Para os IDs E2E-01 a E2E-08, use o runner do MVP em `backend/`, com PostgreSQL de
teste vazio, Mailpit em loopback e Node 24. Dê um nome novo à saída de cada
rodada. O runner executa as oito jornadas em uma única rodada. Nos cartões,
os IDs indicam quais resultados inspecionar no relatório.

```powershell
$env:ACADEMIA_E2E = '1'
uv run --locked python -m tests.acceptance --output ./data/e2e/revisao-01
```

Verifique o rollback e a aprovação das jornadas indicadas. Para acesso e
frequência, use o comando Edge do cartão 05. Para CompreFace real, use a
coleção sintética do cartão 04.

## Relatório ao terminar uma etapa

Siga o AGENTS.md. Em até oito linhas, informe arquivos alterados, testes
executados, resultados e pendências.
