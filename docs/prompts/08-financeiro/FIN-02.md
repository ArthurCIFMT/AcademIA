# FIN-02 — Simulação local de compra de plano

## Metadados

- Fase: Financeiro tardio.
- Estado de execução: consulte o manifesto.
- Dependências: FIN-01, GATE-09.
- Requisitos: RF-31; RN-22, RN-24, RN-35; RNF-17.
- Módulos: MOD-08.

## Objetivo e contexto

Entregar compra e confirmação simuladas, usando registros financeiros locais.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/billing/payments/**`
- `backend/tests/billing/**`
- `frontend/src/features/checkout/**`
- `database/**`
- Contrato de plano e cadastro administrativo para expor o preço simulado já
  previsto no banco. Composição da API e navegação do cliente para ligar a tela.

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Exibir simulação de compra para o próprio cliente autenticado, usando plano
   ativo, preço calculado no backend e identificador local da operação.
2. Oferecer cenários sintéticos confirmado, pendente e recusado. Persistir o
   resultado com idempotência e preservar valor e plano no histórico.
3. Usar o mesmo registro financeiro e preservar a consulta às cobranças
   administrativas. Uma simulação gera seu próprio recibo local. Matrícula e
   renovação continuam ações independentes do atendente.

## Critérios de aceite

- Cobrir CA-31.7–CA-31.9. Plano inativo fica indisponível e cada cliente consulta
  somente a própria operação simulada.
- Reenvio idêntico devolve o resultado salvo. Reutilizar o ID com outros dados
  é rejeitado sem alterar o registro.
- Pendência ou recusa não conta como recebimento. Confirmação atualiza apenas o
  financeiro e a interface identifica o valor como simulado.

## Testes obrigatórios

BE; INT; API; FE. Usar PostgreSQL de teste e cenários sintéticos locais.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Cobrança real, gateway, webhook, cartão, chave Pix e dados bancários.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
