# FND-01 — Validar fontes de verdade e glossário

## Metadados

- Fase: Fundação documental
- Estado inicial: PRONTO
- Dependências: P00
- Requisitos: RF-01–RF-35, RN-01–RN-36, RNF-01–RNF-17, MRF01–MRF15
- Módulos: MOD-00–MOD-12
- Próximo prompt desbloqueado: FND-02A

## Objetivo

Revisar e consolidar o contexto, requisitos, regras, macrorequisitos, glossário e
rastreabilidade antes de qualquer scaffold de aplicação.

## Contexto obrigatório

- `AGENTS.md`
- `docs/prompts/00-prompt-mestre.md`
- todo o conteúdo de `docs/requisitos/`
- `docs/arquitetura/modulos.md`
- `docs/arquitetura/rastreabilidade.md`

## Pré-condições

- Repositório sincronizado e P00 concluído.
- Materiais fornecidos pelo responsável acessíveis.

## Escopo permitido

- `docs/requisitos/**`
- `docs/arquitetura/modulos.md`
- `docs/arquitetura/rastreabilidade.md`
- `docs/prompts/README.md`

## Fora do escopo

- Criar frontend, backend, banco ou migrations.
- Escolher silenciosamente tecnologias ainda abertas.
- Inventar literatura, critérios clínicos ou regras de pagamento.
- Renumerar IDs existentes sem mapa de migração explícito.

## Contratos e invariantes

- Headings canônicos são a fonte para contagem de RF/MRF; referências em matrizes
  podem repetir IDs legitimamente.
- Requisito derivado ou normalizado precisa ter proveniência registrada.

## Implementação obrigatória

1. Verificar que todos os RF, RN e MRF fornecidos estão representados.
2. Separar requisitos fornecidos, derivados e ainda propostos.
3. Identificar sobreposições e normalizações sem apagar os IDs originais.
4. Normalizar os termos cliente/aluno, instrutor/treinador, ficha/proposta e
   assinatura/matrícula.
5. Confirmar cobertura inicial por módulo.
6. Registrar lacunas que exigem decisão, sem resolvê-las por suposição.
7. Atualizar o estado do prompt no manifesto.

## Critérios de aceite

- Nenhum ID fornecido desaparece.
- RF-34 e RF-35 possuem origem explícita.
- MRF08–MRF15 permanecem identificados como derivados até validação.
- Restrições técnicas, testes e firewall estão representados como RNFs.
- Pagamento e Docker estão corretamente posicionados em fases tardias.
- Rastreabilidade aponta módulo para cada grupo de requisitos.
- Documentos não contêm contradições conhecidas sem observação.

## Testes obrigatórios

- `rg -n "^### RF-[0-9]{2}" docs/requisitos/requisitos-funcionais.md`
- `rg -n "^\| RN-[0-9]{2}" docs/requisitos/regras-de-negocio.md`
- `rg -n "^\| RNF-[0-9]{2}" docs/requisitos/requisitos-nao-funcionais.md`
- `rg -n "^### MRF[0-9]{2}" docs/requisitos/macrorequisitos-ia-rag.md`
- Confirmar manualmente que links relativos apontam para arquivos existentes.
- `git diff --check`.

## Entregáveis

- Fontes de verdade revisadas.
- Registro de normalização e lacunas.
- Rastreabilidade/manifesto atualizados.

## Condições de interrupção

Interrompa somente se a fonte original necessária não estiver disponível ou se
duas decisões explícitas do responsável forem materialmente incompatíveis.

## Git

- Commit sugerido: `docs: consolidate project requirements`
- Push permitido somente conforme a política vigente e autorização do responsável.

## Relatório final

Informe documentos revisados, IDs preservados, lacunas, validações executadas e
se FND-02A foi desbloqueado.
