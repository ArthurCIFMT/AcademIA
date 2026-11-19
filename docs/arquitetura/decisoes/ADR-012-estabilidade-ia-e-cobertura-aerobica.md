# ADR-012 — Contrato estruturado e cobertura aeróbica após revisão manual

Status: ACEITA no escopo de reparo solicitado pelo responsável em 2026-11-19.
Substitui o modo de saída e os orçamentos do perfil principal definidos na ADR-006;
modelo, gratuidade, fronteiras, regras de saúde e quantidade de chamadas permanecem.

## Problema observado

O desenvolvimento registrou uma ficha rejeitada por contrato e uma segunda
execução limitada pela quota. O código anterior escondia a causa de validação
em um motivo genérico. A saída rejeitada não foi armazenada: não é possível
atribuir retroativamente a falha a um campo específico. O catálogo cresceu para
31 exercícios; o prompt de geração ocupava cerca de 20 mil bytes. A resposta
à pergunta sobre esteira não tinha cobertura aeróbica suficiente no corpus ativo.

## Decisão

- Groq/GPT-OSS 120B usa response_format=json_schema, strict=true, conforme a
  [documentação oficial](https://console.groq.com/docs/structured-outputs).
  Objetos fechados, propriedades obrigatórias, opcionais anuláveis e enums com
  os IDs enviados restringem a forma. Validações de domínio continuam obrigatórias:
  formato correto não prova pertinência clínica, qualidade ou recursos válidos.
- O schema vai no campo próprio do transporte, sem duplicá-lo no texto do system.
  As instruções e a separação entre dados e instruções são preservadas.
- Perfil principal projeta até 12 candidatos viáveis, distribuídos por grupos
  musculares de forma determinística. Exclui proibidos e preserva os exercícios
  viáveis da ficha-base em adaptação, mesmo quando excedem esse alvo; mantém
  o teto de 40 e de bytes. Não escolhe a prescrição: itens continuam do LLM.
  Descrição longa sai dessa projeção; nomes, grupos, IDs e combinações ficam.
  A impressão digital e a revalidação final consideram o inventário completo.
- Saída de geração principal: até 2048 tokens; triagem 400 e chat 600 permanecem.
  Essa reserva favorece a demonstração curta. Fichas maiores podem esgotá-la:
  saída interrompida não publica, não é completada artificialmente e não abre
  retry. O instrutor mantém o fluxo manual. Não há promessa de geração ilimitada
  com quota gratuita; concorrência e limites do fornecedor continuam externos.
- Prompt academia-ia-v4 explicita cópia de recursos por candidato, ordem por dia,
  repetições numéricas, exemplo curto e resposta parcial sustentada por evidência.
  Meta semanal não é transformada em prescrição diária individual.
- Validações da ficha registram códigos seguros específicos; HTTP 400 é recusa
  do provedor, HTTP 429 é quota. A tela explica quota e recusa sem expor conteúdo
  clínico, resposta bruta, chave ou raciocínio interno.
- Acrescentar à preparação local quatro recortes do guia brasileiro do Ministério
  da Saúde, apenas páginas físicas 24/25, política explícita v2, finalidade DUVIDAS.
  Há orientação geral para adultos sobre duração/intensidade e divisão do tempo,
  não um protocolo individual de esteira. Extração integral pendente permanece
  pendente: o sucesso dessa seleção não aprova outras páginas ou fontes.

Os perfis de reserva conservam seus modos/orçamentos e exigem seleção e avaliação
próprias. Não adicionar fallback, pesquisa iterativa, retries ou plano pago.
Não alterar onboarding, aprovação do instrutor, cadastros ou acesso de clientes.

## Verificação

[Regressão da revisão manual](../../testes/reparo-ia-20261119.md) separa testes
controlados, recuperação real e chamadas reais. Relatórios AI-06/TST-01 anteriores
são históricos: não herdam novos hashes nem comprovam a versão alterada.
