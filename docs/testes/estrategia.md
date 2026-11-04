# Estratégia incremental de testes

## Estado

Plano de verificação, não testes já implementados ou executados.
Origem: AGENTS.md, RNF-07 e critérios de aceite RF/RN/MRF.
Ferramentas e comandos reais serão registrados pelos prompts de fundação.

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
| IA | Avaliação | Triagem, restrições, abstenção, contexto e proposta |
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
validada. Corpus, política de bloqueio e resultados esperados precisam de revisão
do responsável. Registre modelo, embeddings, parâmetros e versões.
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
- Cliente sem instrutor designado mantém consulta/chat; pendência de revisão é explícita.
- Atendente autorizado matricula/renova sem pagamento ou comprovante; matrícula
  funciona com estado financeiro ausente, pendente/recusado e gateway indisponível.
- Cliente com matrícula válida usa o fluxo facial sem consulta financeira obrigatória;
  usuário sem permissão, matrícula ausente/vencida e limites inválidos continuam recusados.
- Cadastro biométrico exige matrícula; nova captura é comparada pelo serviço facial
  real com a referência, incluindo outra pessoa, ausência de rosto e baixa qualidade.
- Mock facial testa contratos/regras; aceite biométrico requer evidência do provedor
  real configurado. Não publicar fotos nem credenciais nos relatórios.
- API fictícia de catraca recebe decisão autenticada, rejeita comando expirado e
  separa confirmação do comando da passagem simulada; replay não duplica presença.
