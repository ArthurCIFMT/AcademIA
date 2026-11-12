# ADR-011 — Cinco cenários reais e quatro exercícios por dia

Status: ACEITA por solicitação do responsável em 2026-11-12.
Substitui a quantidade de casos/tamanho dos exemplos da ADR-010.

O responsável pediu menos testes com consumo de quota e esclareceu que quatro
exercícios pertencem à ficha de um dia, não a quatro dias de treino. A amostra v4
usa cinco cenários reais: dúvida PT com fonte EN (L09), geração (L13), adaptação
(L18), injeção na mensagem (L23) e injeção documental (L24). São no máximo sete
chamadas físicas: três chats, uma triagem/geração e uma triagem/adaptação.
Não adicionar tentativas, correção por LLM ou outro provedor ao lote.

Cada exemplo gerado/adaptado aceita até quatro exercícios por dia e uma/duas
séries; preferir quatro na geração quando viáveis. Não define quatro dias: a
disponibilidade do onboarding prevalece. Exercício com equipamento exige recursos
disponíveis; peso corporal usa dispensa/recursos declarados no catálogo.
É padronização da demonstração, não dose universal nem mudança do editor manual.

Os 30 cenários locais SV/SC, oito perfis, contratos e bloqueios permanecem.
Eles não chamam LLM real. O mínimo de amostras reais passa de 24 para cinco nos
três perfis de configuração. Demais limiares não mudam: com cinco saídas, 90%
de suporte exige todas fundamentadas; as duas fichas precisam ser válidas para
alcançar 80%. Tolerância zero para falha crítica. Exigir revisão vinculada.
Percentis tão pequenos são descritivos; não comprovam desempenho estatístico
robusto, ampla cobertura de perfis ou segurança universal.

V3 e resultados são preservados como históricos, incluindo as extrapolações de
L03/L04. A redução não corrige essas falhas nem as reclassifica como aprovadas.
Não unir partes v3/v4 ou modelos distintos. Ensaios da v4 começam com identidade
fixa; retomam apenas falha de provedor/pendente, preservando respostas concluídas.

A pergunta sobre troca automática de LLM foi analisada; a seleção implementada
continua manual (ADRs 008/009). Uma evolução possível é uma cadeia gratuita
Groq→Gemini, limitada a uma troca por pedido após recusa por quota, registrando
modelo, tentativa e consumo. Não trocar por JSON inválido, bloqueio de saúde ou
falta de evidência; não fazer corrida/loop. Isso altera o contrato atual de uma
tentativa por etapa e exige atualização coordenada de persistência, idempotência,
orçamento e testes antes de ativar. A avaliação de cada candidato permanece
separada; não usar outro modelo para esconder falha ou completar um ensaio alheio.
Sem reserva disponível, retornar erro controlado e preservar treino manual.

Limites oficiais consultados: [Groq](https://console.groq.com/docs/rate-limits)
e [Gemini](https://ai.google.dev/gemini-api/docs/rate-limits). Quotas/nível gratuito
dependem da conta/projeto; não contratar faturamento nem presumir disponibilidade.
