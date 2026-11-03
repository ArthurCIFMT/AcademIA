# Contexto, escopo e glossário

## Estado do documento

- Versão: 0.1
- Data de consolidação: 2026-11-03
- Origem: descrição, MER e decisões fornecidas pelo responsável do projeto.
- Situação: base para revisão antes da implementação.

## Contexto

| Item | Definição |
|---|---|
| Problema | Pouca eficiência na criação de treinos específicos para cada cliente e pouco controle das atividades administrativas do estabelecimento. |
| Domínio | Academia fitness. |
| Atores | Clientes, atendentes, administradores e instrutores. |
| Objetivo | Centralizar e automatizar operações administrativas, de atendimento, treinamento, acesso e acompanhamento da academia. |

## Natureza e prioridades

- O projeto é acadêmico, não um produto comercial em produção.
- O MVP deve priorizar usuários, clientes, funcionários, designação de instrutor,
  onboarding, exercícios, fichas manuais, IA/RAG e aprovação profissional.
- Cobrança e integração automática de pagamentos ficam para fase tardia.
- Dockerfiles e Docker Compose ficam para depois do MVP e da maioria dos módulos.
- O código deve permanecer executável localmente antes da containerização.
- Toda implementação deve existir localmente e no repositório GitHub configurado.

## Identidade e papéis

Uma identidade de usuário pode acumular os papéis:

- `CLIENTE`;
- `ADMINISTRADOR`;
- `ATENDENTE`;
- `INSTRUTOR`.

Cliente e funcionário são perfis de domínio vinculados ao usuário. Administrador,
atendente e instrutor são papéis operacionais. Uma pessoa pode, se necessário,
possuir simultaneamente perfil de cliente e perfil de funcionário.

## Fluxo essencial do MVP

1. Um usuário autorizado cadastra o cliente.
2. Um instrutor responsável é designado ao cliente, preservando o histórico.
3. O cliente recebe convite e conclui o onboarding.
4. O instrutor pode criar uma ficha manualmente.
5. O RAG recupera conhecimento de uma base documental aprovada.
6. A IA analisa o onboarding, aplica a triagem e cria apenas uma proposta.
7. O instrutor designado revisa, modifica, aprova ou rejeita a proposta.
8. Somente uma versão aprovada pode se tornar a ficha vigente do cliente.
9. Alterações posteriores, inclusive pelo chat, criam nova proposta/versão.

## Fora do MVP inicial

- Pagamento automático, estornos e conciliação financeira.
- Implantação comercial, alta disponibilidade e escalabilidade distribuída.
- Containerização completa da aplicação.
- Diagnóstico médico realizado pela IA.
- Reconhecimento facial implementado pela própria aplicação; o reconhecimento é
  responsabilidade de um serviço externo.

## Glossário

| Termo | Significado no projeto |
|---|---|
| Usuário | Identidade autenticável com um ou mais papéis. |
| Cliente/aluno | Perfil que recebe atendimento, onboarding e ficha de treino. |
| Funcionário | Perfil operacional da academia. |
| Instrutor | Funcionário autorizado a prescrever, revisar e aprovar fichas. |
| Onboarding | Coleta inicial de dados físicos, funcionais e de saúde informados. |
| Avaliação | Registro datado e atribuível que acompanha a evolução do cliente. |
| Ficha | Plano de treino versionado composto por itens de exercício. |
| Proposta de IA | Versão não ativa, sujeita a validações e aprovação do instrutor. |
| RAG | Recuperação de evidências documentais para contextualizar a geração. |
| Corpus | Conjunto versionado de documentos autorizados para o RAG. |
| Matrícula | Vínculo vigente entre cliente e plano; independe do mecanismo de pagamento. |
| Reconhecimento | Associação facial produzida por serviço externo. |
| Autorização de acesso | Decisão do sistema após identidade, matrícula e regras de acesso. |

## Decisões ainda abertas

As decisões abaixo não impedem esta documentação, mas impedem os respectivos
scaffolds ou módulos até serem registradas em ADR:

- framework Python definitivo;
- Keycloak/OIDC ou autenticação integrada ao backend;
- banco vetorial especializado definitivo;
- academia única ou multiacademia;
- provedor de LLM e embeddings;
- corpus inicial e responsável por aprová-lo;
- critérios operacionais para casos de saúde graves;
- política Git por branches/PRs ou commits diretos;
- forma de executar PostgreSQL, identidade e banco vetorial antes do Docker.
