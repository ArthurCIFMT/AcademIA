# FND-03 — Revisar MER e modelo lógico

## Metadados

- Fase: Fundação de dados
- Estado inicial: BLOQUEADO até FND-02B
- Dependências: FND-01, FND-02B
- Requisitos: RF-01–RF-35, RN-01–RN-36, MRF03–MRF12
- Módulos: MOD-01–MOD-12
- Próximo prompt desbloqueado: FND-04 e FND-07

## Objetivo

Transformar o MER inicial em modelo lógico consistente com requisitos, papéis,
designação de instrutor, versionamento, IA/RAG e controle de acesso.

## Contexto obrigatório

- `AGENTS.md`
- `docs/prompts/00-prompt-mestre.md`
- todos os requisitos e ADRs aceitos
- `docs/arquitetura/modelo-de-dados/original/MER_Academia_Completo_v4.drawio.png`
- `docs/arquitetura/modulos.md`

## Pré-condições

- FND-02B concluído.
- Gates de stack, tenancy e Git fechados.
- MER original versionado e legível.

## Escopo permitido

- `docs/arquitetura/modelo-de-dados/**`
- `docs/arquitetura/modulos.md`
- `docs/arquitetura/rastreabilidade.md`
- `docs/prompts/README.md`

## Invariantes obrigatórias

- Usuário possui papéis acumuláveis.
- Cliente e funcionário são perfis vinculados à identidade.
- Designação cliente–instrutor preserva histórico.
- Estados de conta, matrícula, biometria e elegibilidade são distintos.
- Onboarding/avaliações e fichas possuem versionamento necessário.
- Ficha aprovada não é modificada retroativamente.
- `EXERCICIO` não armazena séries/carga específicas de prescrição.
- Proposta de IA, revisão profissional e ficha ativa são estados distinguíveis.
- Reconhecimento externo e decisão de acesso são registros separados.
- Cobrança pode possuir múltiplas tentativas de pagamento.
- Corpus vetorial referencia fontes; dados pessoais permanecem operacionais.

## Fora do escopo

- Criar migration ou schema físico.
- Implementar ORM, API ou interface.
- Detalhar tabelas de pagamento além do necessário para coerência futura.
- Inventar campos clínicos não aprovados.

## Implementação obrigatória

1. Catalogar entidades, atributos conceituais e ownership por módulo.
2. Corrigir cardinalidades e duplicações do MER inicial.
3. Documentar chaves, unicidades e invariantes importantes.
4. Descrever máquinas de estado de onboarding, ficha, matrícula e acesso.
5. Manter um dicionário de dados conceitual.
6. Produzir obrigatoriamente representação textual versionável em Mermaid ou DBML,
   além do dicionário de dados; artefato visual adicional é opcional.
7. Atualizar a rastreabilidade e o manifesto.

## Critérios de aceite

- Cada RF que persiste dados encontra entidade responsável.
- Relações N:N usam entidade associativa quando possuem histórico/atributos.
- Um instrutor principal vigente pode ser garantido sem perder vínculos antigos.
- Uma única ficha vigente por cliente pode ser garantida.
- Idempotência de eventos externos possui chave identificável.
- O modelo não exige pagamento automático para matrícula manual.
- Pontos ainda desconhecidos estão marcados, não inventados.

## Testes obrigatórios

- Revisão cruzada do modelo contra RF/RN/MRF.
- Verificação de cardinalidades e ciclos de dependência entre módulos.
- Validar a sintaxe do Mermaid/DBML com a ferramenta adotada no repositório.
- `git diff --check`.

## Entregáveis

- Modelo textual versionável.
- Dicionário de dados e máquinas de estado.
- Registro das diferenças em relação ao MER original.
- Rastreabilidade e manifesto atualizados.

## Condições de interrupção

Pare se ADR de tenancy, identidade ou aprovação de ficha continuar aberto, pois
essas decisões alteram materialmente o modelo.

## Git

- Commit sugerido: `docs: revise logical data model`
- Siga a política Git aceita em FND-02B.

## Relatório final

Resuma entidades, principais correções ao MER, validações, decisões pendentes e
prompts de scaffold desbloqueados.
