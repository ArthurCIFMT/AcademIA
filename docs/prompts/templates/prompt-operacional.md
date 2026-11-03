# <ID> — <Título da entrega>

## Metadados

- Fase: `<fase>`
- Estado inicial: `PRONTO | BLOQUEADO`
- Dependências: `<IDs>`
- Requisitos: `<RF-*>`, `<RN-*>`, `<MRF*>`
- Módulos: `<MOD-*>`
- Próximo prompt desbloqueado: `<ID ou nenhum>`

## Objetivo

Descreva uma única capacidade coesa e verificável.

## Contexto obrigatório

- `AGENTS.md`
- `docs/prompts/00-prompt-mestre.md`
- `<requisitos, ADRs e contratos específicos>`

## Pré-condições

- Estado esperado do repositório.
- Dependências concluídas.
- Gates e decisões que precisam estar aprovados.

## Escopo permitido

- Arquivos ou diretórios que podem ser alterados.
- Entidades, endpoints, telas ou contratos pertencentes à entrega.

## Fora do escopo

- Capacidades explicitamente proibidas neste prompt.
- Módulos futuros que não devem ser antecipados.

## Contratos e invariantes

- Schemas JSON e estados relevantes.
- Regras de autorização.
- Ownership de dados e limites entre módulos.
- Requisitos de idempotência, versionamento ou auditoria.

## Implementação obrigatória

1. Passos objetivos da entrega.
2. Migration junto da capacidade, se aplicável.
3. Documentação e rastreabilidade afetadas.

## Critérios de aceite

- Cenários observáveis, preferencialmente Given/When/Then.
- Resultado esperado de API, interface e persistência.
- Casos de erro e autorização.

## Testes obrigatórios

- Comandos exatos já existentes no repositório.
- Testes unitários, integração, contrato ou interface necessários.
- Resultado mínimo esperado.

## Entregáveis

- Código, migrations, schemas, testes e documentação.

## Condições de interrupção

- Dependência ausente.
- Decisão não aprovada.
- Conflito com requisito ou alteração preexistente.
- Serviço externo necessário sem alternativa de teste.

## Git

- Branch esperada: `<definida no ADR de Git>`.
- Commit: `<mensagem sugerida>`.
- Push/PR: somente conforme autorização e política vigente.

## Relatório final

Siga `AGENTS.md` e o prompt mestre: resultado, arquivos, testes, riscos e próximo
prompt, sem ocultar falhas ou testes não executados.
