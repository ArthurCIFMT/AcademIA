# FND-01 — Validar fontes de verdade e glossário

## Metadados

- Fase: Fundação documental
- Estado inicial: CONCLUIDO — preparação documental delegada em 2026-11-04.
- Dependências: P00
- Requisitos: RF-01–RF-38, RN-01–RN-39, RNF-01–RNF-18, MRF01–MRF15
- Módulos: MOD-00–MOD-12
- Próximo prompt desbloqueado: FND-02A

## Objetivo

Revisar e consolidar o contexto, requisitos, regras, macrorequisitos, glossário e
rastreabilidade antes de qualquer scaffold de aplicação.

## Contexto obrigatório

- `AGENTS.md`
- `docs/prompts/00-contexto-de-execucao.md`
- `docs/prompts/00-contrato-operacional.md`
- `docs/testes/estrategia.md`
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
- `docs/testes/comandos.md`
- `scripts/verificar_documentacao.py`

## Fora do escopo

- Criar frontend, backend, banco ou migrations.
- Escolher silenciosamente tecnologias ainda abertas.
- Inventar literatura, critérios de triagem da demonstração ou regras de pagamento.
- Renumerar IDs existentes sem mapa de migração explícito.

## Contratos e invariantes

- RFs usam títulos canônicos; RN/RNF/MRF usam linhas das respectivas tabelas.
  Referências em matrizes podem repetir IDs legitimamente; não contá-las como definição.
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

- Nenhum ID é removido sem mapa de mudança; os MRFs agentivos retirados estão registrados no histórico.
- RF-34–RF-37 e as mudanças em publicação/parecer, matrícula e biometria possuem
  origem explícita nas solicitações do responsável.
- MRF01–MRF15 e seus 67 critérios refletem orquestrador semântico, triagem resumida
  e geração LLM; MRF16–MRF19 estão retirados com mapa no registro de mudança.
  Escolhas clínicas/técnicas ainda abertas permanecem explícitas.
- Restrições técnicas, testes e firewall estão representados como RNFs.
- Pagamento e Docker estão corretamente posicionados em fases tardias.
- Rastreabilidade aponta módulo para cada grupo de requisitos.
- Documentos não contêm contradições conhecidas sem observação.

## Testes obrigatórios

- `rg -n "^### RF-[0-9]{2}" docs/requisitos/requisitos-funcionais.md`
- `rg -n "^\| RN-[0-9]{2}" docs/requisitos/regras-de-negocio.md`
- `rg -n "^\| RNF-[0-9]{2}" docs/requisitos/requisitos-nao-funcionais.md`
- `rg -n "^\| MRF[0-9]{2} \|" docs/requisitos/macrorequisitos-ia-rag.md`
- `python scripts/verificar_documentacao.py` (Python 3 disponível no ambiente).
- Conferir também sentido das referências e lacunas de domínio; links existentes
  não comprovam aprovação do conteúdo nem adequação clínica.
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

## Evidência de execução documental

Executado por delegação expressa do responsável. Consultar
[prontidão](../../arquitetura/preparacao-implementacao.md) para ADRs, contratos,
modelo, verificações e próximos prompts. Não solicitar novamente as escolhas
registradas como aceitas. Não confundir esta conclusão com código/serviços funcionando.
