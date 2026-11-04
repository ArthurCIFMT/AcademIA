# Comparação com o modelo didático do professor

O exemplo foi fornecido como referência para análise, não como ordem para apagar
os arquivos de planejamento já autorizados.

| Aspecto | Exemplo do professor | Organização adotada |
|---|---|---|
| Tarefa do mestre | Elaborar plano sem implementar | 00-prompt-mestre.md agora faz essa mesma tarefa |
| Contexto | Domínio, atores, funcionalidades e stack | Domínio, fontes, decisões, módulos, atores, fluxos, invariantes e dados |
| Saída | Módulos, sequência, dependências, aceite | Mesmo conjunto, incluindo testes e escopo do MVP |
| Limite | Resposta de até 40 linhas | Substituído por resumo breve e plano detalhado, conforme revisão solicitada |
| Restrições | Sem arquivos, instalação ou alteração de código | Aplicadas quando o mestre é executado |
| Execução posterior | Prompts operacionais | Cartões individuais + contexto + contrato comum |
| Regras permanentes | Complementadas por AGENTS.md | Mantidas em AGENTS.md |

O antigo arquivo mestre orientava implementação. Seu conteúdo foi preservado em
00-contexto-de-execucao.md para que as duas tarefas tenham nomes inequívocos.

Na revisão seguinte, o responsável pediu um mestre completo além do modelo didático.
Foram incluídos os 13 módulos com ownership, fluxos ponta a ponta, análise do MER,
marcos do MVP, gates, estratégia de testes, evolução de requisitos e rastreabilidade.
A completude vem do conteúdo e das fontes referenciadas, não de repetir todos os
requisitos dentro do mestre. O plano detalhado não está mais limitado a 40 linhas.

Criar os arquivos dos prompts é a entrega documental autorizada nesta conversa.
Executar o mestre futuramente apenas propõe o plano em chat. Executar um cartão
operacional exige escolha explícita da tarefa e cumprimento das dependências.

## Informações que ainda condicionam implementação

- Framework Python e ferramentas; identidade; academia única ou múltipla.
- Banco vetorial e forma local de executar os serviços antes do Docker.
- Modelo de LLM, embeddings, corpus selecionado e regras acadêmicas de triagem
  documentadas pelo responsável, sem aprovação médica ou jurídica externa.
- Regras de acesso/manual, reservas opcionais e integração de pagamentos.
- Política Git para as próximas implementações.

Essas informações não impedem escrever cartões condicionais agora. FND-02A/B e
os gates registram as escolhas antes das tarefas afetadas. Cartões revisam seus
caminhos, schemas e comandos com base nos ADRs aceitos antes de executar.
