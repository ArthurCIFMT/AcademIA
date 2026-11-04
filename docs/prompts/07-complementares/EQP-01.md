# EQP-01 — Equipamentos administrativos e catálogo público

## Metadados

- Fase: MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-05, IAM-03, IAM-04.
- Requisitos: RF-15, RF-19, RF-32, RF-33, RF-38; RN-04, RN-33, RN-37; RNF-14.
- Módulos: MOD-10.

## Objetivo e contexto

Entregar equipamentos administrativos e catálogo público, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/equipment/**`
- `backend/tests/equipment/**`
- `frontend/src/features/equipment/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Implementar API e telas de cadastro, consulta, disponibilidade operacional e
   inativação mantidas por administrador autorizado.
2. Validar imagem opcional e registrar arquivo/referência por adapter configurável.
3. Expor consulta de disponíveis para visitante/cliente e contrato de recursos
   atuais para MOD-04/MOD-06; não depender de busca vetorial para disponibilidade.
4. Manter referência estável de equipamento e distinguir recurso indisponível de
   ocupado no instante; não implementar reserva/ocupação em tempo real.
5. Na implementação, fixtures/seeds sintéticos identificados podem representar
   equipamentos para testes. Nenhum dado de exemplo é criado nesta revisão documental.

## Critérios de aceite

- Nome/situação obrigatórios inválidos impedem cadastro.
- Equipamento inativado some da oferta, mas registro/histórico permanece.
- Listagem móvel mostra nome e imagem quando houver; manutenção exige papel de administrador.
- Serviço recusa recurso ausente/inativo/indisponível para nova prescrição;
  alteração é refletida na revalidação antes de publicar.
- TRN-01 consome o contrato para relacionar requisitos de exercícios sem acesso
  direto ao repositório interno de MOD-10.

## Testes obrigatórios

BE; INT; API; FE; DB.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Compras, estoque de peças e manutenção preditiva.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
