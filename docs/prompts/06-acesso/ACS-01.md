# ACS-01 — Cadastro e substituição da referência biométrica

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: PES-02, IAM-04, NTF-01, GATE-08.
- Requisitos: RF-03, RF-22; RN-10, RN-26, RN-34.
- Módulos: MOD-07.

## Objetivo e contexto

Entregar cadastro e substituição da referência biométrica, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/biometrics/**`
- `backend/tests/access/**`
- `frontend/src/features/biometrics/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Definir contrato com serviço facial e critérios de qualidade antes de aceitar foto.
2. Criar upload protegido/referência externa, substituição atômica e descarte conforme regra aprovada.
3. Registrar autor e aviso sem copiar imagem em auditoria.

## Critérios de aceite

- Funcionário autorizado cadastra; cliente não substitui referência própria pela API.
- Nova foto válida substitui a antiga; falha externa mantém referência anterior consistente.
- Conteúdo biométrico não é público nem aparece em relatórios comuns.

## Testes obrigatórios

BE; INT; API; FE com serviço simulado e contrato externo.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Construir reconhecimento facial ou inventar métrica de qualidade.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
