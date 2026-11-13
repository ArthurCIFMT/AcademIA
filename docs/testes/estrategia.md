# Estratégia incremental de testes

## Estado

A estratégia se baseia em AGENTS.md, RNF-07 e critérios de aceite RF/RN/MRF.
As suites disponíveis e seus comandos constam no [registro de comandos](comandos.md).

## Níveis

| Código | Nível | O que comprova |
|---|---|---|
| DOC | Documentação | IDs, links, dependências, escopo e diff coerentes |
| BE | Unitários backend | Regras e transições isoladas, sem APIs pagas |
| INT | Integração | API, persistência e constraints em PostgreSQL de teste |
| API | Contrato | Métodos, estados HTTP, JSON e OpenAPI compatíveis |
| FE | Componentes frontend | Formulários, permissões visuais e estados de falha |
| E2E | Ponta a ponta | Usuários reais de teste percorrem interface e backend |
| DB | Migrations | Instalação limpa e evolução preservando dados |
| RAG | Recuperação | Chunking, filtros, evidências, relevância e latência |
| IA | Avaliação | Resumo sem perda de alertas, triagem assistida, dúvidas, geração e limites |
| INF | Infraestrutura | Subida, persistência, rede e healthchecks na fase final |

## Distribuição

- Cada prompt testa o comportamento que introduz; teste não é só uma etapa final.
- FND-04/06 configuram testes Python e contratos; FND-05 configura banco de teste.
- FND-07 configura componentes, tipos, lint e build do frontend.
- TST-01 configura/executa o roteiro E2E do MVP.
- RAG-05 mede recuperação e AI-06 executa o conjunto de avaliação da IA.
- VAL-02 reúne aceitação dos módulos finais, sem substituir testes anteriores.
- Docker, Compose e Testcontainers ficam para depois do MVP e da maioria dos módulos.

## Banco e integrações

Use banco de teste separado do banco de desenvolvimento. Testes devem limpar apenas
dados de teste identificados, sem apagar bancos compartilhados. Cubra rollback,
unicidade, concorrência e idempotência quando exigidos pela regra.
Use adapters falsos para unitários de e-mail/LLM/facial/pagamento; integre o serviço
real ou sandbox no aceite correspondente, registrando evidência e limitações.
Não dispare cobranças reais nem envie mensagens a pessoas reais nos testes.

## IA e corpus

Monte fixtures sintéticas rotuladas separadas do corpus de conhecimento.
Documentos artificiais podem testar o pipeline, mas não representar literatura
validada. Corpus, regras acadêmicas de bloqueio e resultados esperados precisam de
conferência técnica do responsável do projeto, sem aprovação médica/jurídica externa. Registre modelo, embeddings, parâmetros e versões.
Inclua dados insuficientes, caso bloqueado, restrição, contradição, falha de provedor,
instrução maliciosa documental e tentativa de consultar outro cliente.
Os casos críticos esperados bloqueiam geração/publicação em 100% da suíte definida.
Isso é um critério de regressão desse conjunto, não garantia clínica universal.
Métricas de relevância e demais limiares devem ser definidos antes da avaliação.
Medir p95 de busca <= 2 s com volume, hardware, amostra e consultas documentados;
não confundir latência vetorial com o tempo completo do LLM.

## Evidência

Por entrega, registrar comandos reais, ambiente, resultados, falhas, testes não
executados e requisito coberto. Percentual de cobertura sozinho não é aceite.
Não testar apenas o caminho feliz. A suíte crítica do MVP inclui isolamento por
cliente, instrutor não designado, bloqueio de saúde e conteúdo publicado imutável.

## Cenários acrescentados pela revisão de fluxo

- Cliente lê treino e usa chat com parecer PENDENTE, antes de qualquer aceite.
- Aceite/rejeição identifica versão e responsável; rejeição continua visível e
  não bloqueia consulta/chat; versão alterada não herda aceite anterior.
- A rejeitada → B PENDENTE preserva A; rejeitar B exclui conteúdo de A e mantém B.
  Aceitar B, falhar na geração ou repetir evento não exclui A. Cobrir rejeições
  concorrentes/fora de ordem e preservar auditoria/execuções sem recuperar conteúdo
  excluído por API, exportação, cache ou contexto ativo do chat.
- Adaptação por saúde exige evidência pertinente recuperada: fonte ausente,
  irrelevante, incompatível ou conflitante impede gerar/publicar adaptação.
- Cliente sem instrutor designado mantém consulta/chat; pendência de revisão é explícita.
- Atendente autorizado matricula/renova sem pagamento ou comprovante; matrícula
  funciona com estado financeiro ausente, pendente/recusado e gateway indisponível.
- Cliente com matrícula válida usa o fluxo facial sem consulta financeira obrigatória;
  usuário sem permissão, matrícula ausente/vencida e limites inválidos continuam recusados.
- Cadastro biométrico exige matrícula; nova captura é comparada pelo CompreFace
  real com a referência, incluindo outra pessoa, ausência de rosto e baixa qualidade.
- Mock facial testa contratos/regras; aceite biométrico requer evidência do provedor
  real configurado. Não publicar fotos nem credenciais nos relatórios.
- API fictícia de catraca recebe decisão autenticada, rejeita comando expirado e
  separa confirmação do comando da passagem simulada; replay não duplica presença.

## Critérios adicionais do MVP: recursos, retenção e idioma

- Administrador mantém equipamentos; outro perfil não altera o inventário.
  Gerar somente com recursos ativos/operacionais; testar falta/inativação,
  combinações obrigatórias, alternativa completa, dispensa explícita e vínculo ausente.
- Alteração de disponibilidade durante geração impede publicar plano inviável;
  mudança posterior é sinalizada sem editar versões históricas.
- Testar 15 → 16 versões publicadas: ficam 15 completas incluindo vigente,
  conteúdo mais antigo sai de consulta/exportação/cache/contexto ativo. Parecer
  aceito/rejeitado não dispensa limite. Rascunhos/tentativas não entram na contagem.
- Cobrir concorrência, rollback, replay e numeração crescente, preservando
  metadados de auditoria e registros/snapshots de execuções quando existentes.
  A exclusão por rejeição e a por limite têm motivos distintos e são idempotentes.
- Consultas PT devem recuperar fontes PT/EN esperadas e gerar saída ao usuário em
  português. Avaliar suporte, unidades/negações e falhas de tradução por casos
  rotulados; não aprovar desempenho apenas pelo rótulo multilíngue do modelo.
- Fixtures/seeds de equipamentos serão produzidos na implementação; não são
  inventário real nem literatura clínica. A revisão atual não cria esses dados.
- Usar os critérios identificados de MRF01–MRF15 conforme a tabela completa, sem tratar
  exemplos sintéticos como casos clínicos automaticamente validados.

## Orquestrador com RAG semântico

[Cenários SV-01–SV-24](rag-ia-semantico.md) cobrem dúvidas, projeção resumida sem perda
de alertas, triagem assistida, geração LLM, contexto curto, fontes, falhas e limites.
MRF01–MRF15 e seus 67 critérios são a referência atual; não há teste obrigatório
de planner, escolha dinâmica de ferramentas ou pesquisa iterativa.
AI-01/AI-02 testam regras/projeção/orquestrador com doubles; AI-03 integra persistência;
AI-06 executa ensaio real e mede p50/p95 por rota, busca, chamadas e tokens.
p95 ≤ 2 s é da busca vetorial, não da geração completa. Os 32 casos documentais
anteriores exigem revisão antes do aceite. Não declarar aplicação testada só por
atualizar estes arquivos. Critérios numéricos de qualidade são definidos antes do ensaio.

Na revisão didática, cobrir SV-21–SV-24: sem laudo obrigatório, confirmação de
novo snapshot antes de adaptar, publicação/aviso únicos e ausência de retries
automáticos das etapas LLM. A execução e as partes pendentes estão no manifesto
e no guia de TST-01; planejamento não equivale a aprovação.

## Detalhamento RF/RN de 2026-11-06

[Regressões de aceite](aceite-rf-rn-2026-11-06.md) vinculam os critérios adicionados
aos prompts e níveis de teste, incluindo falhas da IA, criação manual sem IA,
sessões/perfis, compra versus matrícula e passagem versus identificação.
O verificador documental também confere corpus selecionado e modelo JSON/DBML;
essa checagem não executa regras de FastAPI, SQL ou provedores reais.

## Execução local parcial de TST-01

O [runner E2E](aceitacao-mvp.md) e os [oito cenários](tst01-cenarios.json) executam
navegador, API e persistência reais com IA controlada. Relatório separa esse
resultado do aceite do provedor real e de PG-01. Não substituir AI-06 pendente
pela navegação ou por uma fixture aprovada. Concorrência permanece nos testes
PostgreSQL próprios; o harness E2E serializa requisições para savepoints.

## Fechamento do MVP

A [consolidação TST-01](tst01-consolidacao.json) fechou PG-01 em 2026-11-12,
com oito jornadas E2E compatíveis, 14 críticos atuais e AI-06 real aprovado.
O [guia](aceitacao-mvp.md) define verificação de código, fontes, casos completos,
rollback, migration e hashes dos relatórios/verificador. A execução local mantém
seu snapshot original; a decisão final está no arquivo próprio de consolidação.
Não repetir chamadas LLM ao consolidar nem apresentar testes históricos como
novamente executados. Mudanças futuras invalidam evidências incompatíveis.
