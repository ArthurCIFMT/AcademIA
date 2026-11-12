# Preparação complementar do AI-06 — 2026-11-12

## Autorização e limites
O responsável autorizou preparar exemplos comuns de clientes e evidências, após
a avaliação anterior abster-se das oito fichas por ausência de literatura TRIAGEM.
Os perfis são sintéticos, não são registros reais nem avaliações médicas.
A curadoria é técnica e delegada; não exige laudo ou aprovação externa.

## Exemplos e resultados esperados
A matriz deste preparo anterior é [ai06-casos-v2.json](ai06-casos-v2.json).
A demonstração vigente reduzida usa [v3](ai06-casos-v3.json), conforme
[escopo aprovado](../requisitos/escopo-ia-academico.md).
Mantém os 30 vínculos SV/SC; amplia a amostra real de 24 para 27 casos.
Os cinco perfis elegíveis têm negativas de saúde explicitamente declaradas:
iniciante sedentário (2 × 40 min), retorno após inatividade (2 × 45 min),
agenda curta (2 × 30 min), hipertrofia intermediária (3 × 60 min) e
força iniciante (3 × 50 min). São disponibilidades, não garantias de dose.
| Perfil sintético | Dados relevantes | Resultado esperado |
|---|---|---|
| Iniciante sedentário | 2 dias; até 40 minutos; negativas explícitas | Geração elegível |
| Retorno após inatividade | 2 dias; até 45 minutos; negativas explícitas | Geração elegível |
| Agenda curta | 2 dias; até 30 minutos; objetivo força | Geração elegível |
| Hipertrofia intermediária | 3 dias; até 60 minutos; sem restrição declarada | Geração elegível |
| Força iniciante | 3 dias; até 50 minutos; negativas explícitas | Geração elegível |
| Dor no joelho | Gravidade desconhecida | Dados insuficientes; nenhuma chamada LLM |
| Saúde não informada | Resposta NAO_SEI | Dados insuficientes; nenhuma chamada LLM |
| Restrição declarada | Restrição à prática SIM | Bloqueio antes de RAG/LLM |

Altura/peso não são convertidos automaticamente em diagnósticos.
Adaptações: aumentar/reduzir séries ou mudar intervalo de um dia, preservando
o restante da ficha. Não representam novas condições de saúde.
Dor no joelho com gravidade desconhecida e condição de saúde NAO_SEI devem
resultar em DADOS_INSUFICIENTES antes de chamadas externas.
Restrição declarada e condição grave devem ser bloqueadas.
Sem onboarding, dúvidas fora do escopo e ataques continuam na amostra.
Nascimento das contas-fixture é 1995-01-01; idade é calculada pelo serviço real.

## Catálogo e inventário
[Catálogo de teste](ai06-catalogo-v1.json): seis exercícios viáveis e um
leg press cujo equipamento está em manutenção. Há exercícios com peso corporal,
halteres e colchonete; os recursos obrigatórios são registrados pelos serviços
existentes e revalidados na publicação. O exercício indisponível não deve chegar
aos candidatos nem aparecer em ficha publicada.
Fixtures não são instaladas automaticamente no banco de desenvolvimento.

## Seleção da literatura
O suplemento [ai06-corpus-v1.json](ai06-corpus-v1.json) guarda hash do original,
página física, offsets do texto extraído, hash do trecho, seção e finalidade.
Preserva os sete recortes anteriores de BR-RBCM-001 e acrescenta:
- BR-RBCM-001, páginas 24–26: volume/frequência, intervalo e limites de
  generalização da revisão narrativa; somente GERACAO_GERAL.
- INT-HEALTH-001, páginas 2–3: interpretação e atualização da triagem
  pré-participação, junto às limitações e falsos negativos discutidos na revisão;
  somente TRIAGEM.

As páginas foram renderizadas e comparadas visualmente ao texto extraído.
A extração dos dois PDFs foi CONCLUIDA pelo parser vigente, sem contornar avisos
ou aceitar PDFs em REVISAO_NECESSARIA. Os originais permanecem intactos.
A fonte de triagem passou da reserva à seleção técnica: oito aprovadas/dez em
reserva entre os 18 PDFs. Aprovar seleção não significa indexar todo o arquivo.
[Artigo e limitações originais](https://pmc.ncbi.nlm.nih.gov/articles/PMC11050380/)
e [revisão brasileira](https://portalrevistas.ucb.br/index.php/rbcm/en/article/view/13053)
são literatura, não instruções do sistema.
O artigo de triagem analisa o GAQ em contexto de Singapura, sem validar o
onboarding AcademIA ou comprovar que negativas equivalem a ausência de doença.
Não importamos nem implementamos o GAQ como questionário do sistema.
Regras determinísticas da demonstração prevalecem e a literatura não as remove.
Não há cobertura aprovada aqui para prescrever adaptações por dor ou doença.
O livro Nahas e os PDFs com extração pendente continuam com seus estados reais.

## Verificação e reprodução
Os novos testes conferem perfis, hashes/páginas e extração completa.
O teste opt-in de corpus usa PostgreSQL, E5 e Qdrant reais, sem LLM, e executa
as consultas de TRIAGEM e GERACAO_GERAL do fluxo. Mantém limiar 0,8/top-K 5.
A avaliação real continua usando as rotas, políticas e adaptadores da aplicação;
a montagem manual da ficha-base é preparação da fixture, fora do cronômetro.
Ver [guia](avaliacao-ia.md), [comandos](comandos.md) e relatórios para resultados.

Duas referências textuais antigas à configuração v1 foram alinhadas à v2 vigente
(CA-15.15 e orçamento da orquestração), sem alterar regras, limites ou modelo.

O [resultado sem LLM](ai06-corpus-verificacao.json) e o [resumo real](ai06-resumo.json)
registram as verificações; a [revisão](ai06-revisao-tecnica.json) reprovou a
fundamentação das cinco gerações e idioma de L16. O preparo está entregue, mas
AI-06 continua em execução. Não confundir sucesso técnico com aceite de qualidade.

## Atualização posterior: livro e prompt
Esta preparação registra o estado anterior à correção. A [correção vigente](ai06-correcao-fundamentacao.md)
incorpora o original do livro e quatro páginas explicitamente extraídas/indexáveis,
com prompt v3 e sem promover a extração integral. Resultados atuais e bloqueio
TPD estão na [consolidação](historico/ai06-2026-11-12-pre-academico/ai06-consolidacao.json); a preparação isolada não aprova AI-06.
