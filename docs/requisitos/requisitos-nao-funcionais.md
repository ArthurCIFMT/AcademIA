# Requisitos não funcionais e restrições técnicas

## Situação

Este documento consolida tecnologias preferenciais/obrigatórias e requisitos
transversais fornecidos para o projeto. Escolhas entre alternativas continuam
sujeitas aos ADRs e ao checkpoint FND-02B.

| ID | Requisito |
|---|---|
| RNF-01 | O frontend deve usar React, TypeScript e Vite. |
| RNF-02 | O backend deve ser implementado em Python com arquitetura modular. |
| RNF-03 | A persistência relacional deve usar PostgreSQL. |
| RNF-04 | A API deve usar REST, JSON e documentação OpenAPI. |
| RNF-05 | O RAG deve utilizar banco vetorial especializado e adaptadores que evitem acoplamento desnecessário a um provedor. |
| RNF-06 | JSON é obrigatório nas fronteiras REST, eventos e integrações; chamadas internas usam tipos adequados da linguagem. |
| RNF-07 | O sistema deve possuir testes unitários, de integração e de contrato da API, com atenção especial à IA e ao evento facial externo. |
| RNF-08 | Configurações e segredos devem vir de ambiente, sem valores sensíveis versionados. |
| RNF-09 | Convites e recuperação devem usar adaptador de SMTP ou API de provedor de e-mail. |
| RNF-10 | A aplicação deve funcionar localmente antes de ser containerizada. |
| RNF-11 | Dockerfiles e Docker Compose devem ser implementados somente após o MVP e a maioria dos módulos. |
| RNF-12 | A fase final de infraestrutura deve definir firewall/restrição de rede, exposição mínima de portas e isolamento dos serviços internos. |
| RNF-13 | A busca vetorial deve alcançar latência p95 de até dois segundos no ambiente e volume de teste documentados. |
| RNF-14 | Interfaces destinadas ao cliente devem ser responsivas para uso em celular. |
| RNF-15 | Logs não devem expor credenciais, onboarding completo, informações médicas ou dados biométricos desnecessários. |
| RNF-16 | Timestamps devem ser armazenados em UTC e expostos em ISO 8601, com conversão de apresentação configurável. |
| RNF-17 | Integrações e eventos repetíveis devem possuir estratégia de idempotência. |
| RNF-18 | Orquestrador usa busca semântica fixa e contexto limitado; chat tem até uma geração, ficha tem até uma análise de triagem e uma geração, sem loops de pesquisa/reparo. Medir p50/p95 total por rota, chamadas/tokens e busca separada. Meta total, limites e provedor gratuito dependem de ADR/ensaio em GATE-04; RAG não garante acelerar uma API lenta. |


## Firewall

“Adicionar firewall” é tratado como requisito de infraestrutura, não como
responsabilidade exclusiva do backend. A solução concreta será decidida na fase
final e deve cobrir, no mínimo:

- somente endpoints necessários expostos externamente;
- PostgreSQL e banco vetorial em rede não pública;
- administração de identidade restrita;
- limites de origem, tamanho de requisição e taxa quando aplicáveis;
- documentação das regras para o ambiente acadêmico.
