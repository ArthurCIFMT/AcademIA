# Falhas de integração da auditoria de 27/11/2026

A auditoria da revisão `ec2d05a` cobriu 196 critérios de 38 requisitos funcionais e as 39 regras de negócio. Foram usados dados sintéticos, PostgreSQL de teste, Mailpit e Edge. No grupo de integração, 194 testes passaram, dois falharam e 11 foram pulados. Também passaram 20 testes do grupo de migrations, oito jornadas do MVP e a jornada de acesso.

| Falha | Observação reproduzida | Prompt de correção |
|---|---|---|
| `test_migration_roundtrip_and_metadata` | O roundtrip chega a `0029` e a asserção espera `0026`. A comparação inicial de metadados passa. | [10 — Verificação da revisão do Alembic](10-revisao-alembic.md) |
| `test_attendant_enrolls_and_renews_without_financial_dependency[None]` | A montagem em `0024` não tem `usuario.endereco`. O login retorna HTTP 500 antes da matrícula. As variantes pendente e recusado no schema atual passam. | [11 — Matrícula sem módulo financeiro](11-matricula-sem-financeiro.md) |

O ensaio adicional em `0029` comprovou criação e renovação com HTTP 201, tentativa direta pelo cliente com HTTP 403, dois registros no histórico e zero consultas financeiras no fluxo observado. Ele usou tabelas financeiras presentes e sem registros. O cenário de ausência dessas tabelas ainda requer correção da fixture.

Este registro é um extrato para orientar as correções. As duas falhas permanecem pendentes até nova execução dos testes. O aceite do VAL-02 tem execução própria. As demais observações da auditoria, incluindo o recorte de IA e a RN-26, seguem fora destes dois cartões.
