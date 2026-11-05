# ADR-003 — Academia única, Git e convenções

Status: ACEITA
Data: 2026-11-04
Origem: responsável delegou a seleção de frameworks, campos e regras técnicas;
academia única foi escolhida expressamente. Escolhas registradas sem exigir nova aprovação.

Decisão expressa do responsável: uma academia. ACADEMIA é configuração singleton
(id=1), sem tenant_id, seletor de unidade ou isolamento multitenant no MVP.
Introduzir múltiplas academias exigirá nova decisão e migration, não será presumido.

Git: entregas acadêmicas podem ir diretamente à main em commits coesos após
verificação; push no origin configurado, sem force/rebase de histórico compartilhado.
Preservar mudanças alheias. PR opcional para entregas maiores. Esta política
formaliza o fluxo já autorizado/utilizado, sem novo checkpoint por prompt.

UTC em timestamptz; API ISO 8601; apresentação America/Sao_Paulo e pt-BR.
Datas civis como nascimento/vencimento usam date, sem converter nascimento a UTC.
Dinheiro decimal(12,2), BRL; nunca float. UUID para domínio, inteiro para versões.
Paginação padrão 20, máximo 100; erros com code/message/details/correlation_id.
Atualização concorrente usa version/revisão de recurso e 409 em base superada.
Credenciais e dados locais fora do Git; .env.example sem segredos.
