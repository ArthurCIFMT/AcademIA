# ACS-02 — Captura facial e integração real de reconhecimento

## Metadados

- Fase: Pós-MVP.
- Estado de execução inicial: BLOQUEADO até concluir dependências.
- Dependências: FND-06, ACS-01.
- Requisitos: RF-20, RF-21, RF-36; RN-06, RN-07; RNF-04, RNF-17.
- Módulos: MOD-07.

## Objetivo e contexto

Entregar captura facial e integração real de reconhecimento, respeitando os critérios abaixo.
Leia o [contexto de execução](../00-contexto-de-execucao.md) e o
[contrato operacional](../00-contrato-operacional.md), que integram este prompt.
Consulte também requisitos citados, modelo lógico e ADRs aceitos.
A redação deste cartão não fecha gates nem autoriza escolher tecnologia pendente.

## Escopo permitido

- `backend/app/modules/access/events/**`
- `backend/app/modules/access/biometrics/**`
- `frontend/src/features/biometrics/**`
- `backend/tests/access/**`
- `database/**`

Documentação, migrations e caminhos equivalentes seguem o contrato comum.

## Implementação e entregáveis

1. Capturar nova imagem e enviá-la pelo backend à API facial real para busca
   entre referências cadastradas; resolver identidade externa no vínculo local.
2. Definir JSON normalizado: evento, origem, identidade, pontuação de correspondência,
   instante e direção. Separar score de identificação, detecção e qualidade da foto.
3. Autenticar origem, validar payload/replays e persistir recebimento idempotente.
4. Resultado confiável vem do adapter ou origem externa autenticada; não confiar
   em client_id/score declarados pelo navegador. Separar reconhecimento de autorização.

## Critérios de aceite

- JSON malformado ou credencial inválida não processa evento.
- Mesmo evento recebido duas vezes não duplica registro.
- Identidade desconhecida, ambígua ou pontuação abaixo do limiar inicial de 95
  não vira reconhecimento positivo; erro do provedor falha de forma controlada.
- Nova foto do cliente cadastrado é comparada realmente; rosto diferente e imagem
  sem rosto são cobertos. Teste com mock não encerra o aceite biométrico.

## Testes obrigatórios

API com exemplos contratados; BE; INT incluindo duplicidade/concorrência; FE;
ensaio real do provedor com referências e capturas separadas, sem divulgar fotos.

Resolva as suites em [comandos reais](../../testes/comandos.md) antes de executá-las.
A [estratégia de testes](../../testes/estrategia.md) define ambiente, dados e evidências.
Execute também lint/tipos/build afetados e `git diff --check`.

## Fora do escopo e interrupção

Liberar catraca apenas porque rosto foi reconhecido.
Dependência/gate aberto ou contrato material ausente impede executar a parte afetada.
Informe a informação que falta; não improvise dados para obter aceite.

## Git e relatório

Siga GATE-05 e autorização vigente; registre evidência em
[manifesto](../README.md). Informe arquivos, comandos reais, resultados, pendências
e próximo ID liberado. Texto criado não significa código implementado.
