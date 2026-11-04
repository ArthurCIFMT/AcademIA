# TRN-02 — Ficha manual e versões imutáveis

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: TRN-01, ONB-02, PES-03.
- Requisitos: RF-17; RN-14, RN-18, RN-19, RN-20, RN-31, RN-33, RN-37, RN-38.
- Módulos: MOD-04.

## Objetivo e contexto

Entregar ficha manual e versões imutáveis, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/training/**`
- `backend/tests/training/**`
- `frontend/src/features/training-editor/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Permitir ao instrutor designado montar rascunho por dias/itens com catálogo, séries, repetições, cadência e intervalo.
2. Criar versionamento, referência à avaliação/onboarding e autoria por versão.
3. Oferecer editor e publicação com validações de domínio; edição de versão publicada gera novo rascunho.
4. Separar conteúdo publicado imutável do parecer profissional por versão.
5. Prever a exclusão de conteúdo da rejeitada anterior em RF-35, sem quebrar
   auditoria, numeração de versões ou snapshots de treinos executados.
6. Suportar retenção de 15 versões publicadas completas por cliente (inclui vigente),
   removendo conteúdo excedente mais antigo sem quebrar referências de auditoria
   ou snapshots de execuções. Rascunhos/tentativas não contam como ficha disponível.

## Critérios de aceite

- Ficha manual pode ser criada com provedor de IA indisponível.
- Nova versão não muda itens, autoria e prescrição histórica.
- Não aceitar item inexistente/inativo, recursos indisponíveis em nova ficha nem alteração por outro cliente.
- Retenção não reutiliza números de versão; snapshots de execuções não são
  reexpostos como fichas completas fora do limite.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Geração automática por IA ou aceite profissional obrigatório para o cliente consultar treino.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
