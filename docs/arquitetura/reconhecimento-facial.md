# Captura e identificação facial — ACS-02

Em **Atendimento → Reconhecimento facial**, o atendente escolhe a direção da
tentativa e tira uma nova foto ou seleciona um arquivo. A tela exibe a
identificação e a similaridade, quando disponível. O motor de autorização
consome o resultado em etapa própria. [Fluxo de acesso](fluxos-atualizados.md).

## Processamento

1. Exigir sessão de atendente e CSRF. Validar e limpar a imagem como no
   [cadastro da referência](biometria.md).
2. O detector do CompreFace deve confirmar exatamente um rosto no limiar de
   detecção de 0,8. A chamada de reconhecimento pede até dois candidatos por
   rosto (prediction_count=2) e mantém a contagem de rostos sem limite (limit=0).
   O backend usa `subjects[].similarity` (0–1) para comparar a identidade.
   [API do CompreFace 1.2.0](https://github.com/exadel-inc/CompreFace/blob/v1.2.0/docs/Rest-API-description.md#recognize-faces-from-a-given-image).
3. É preciso uma única correspondência acima ou igual ao limiar inicial de
   0,95 e um vínculo facial ativo. Duas identidades acima do limiar retornam
   `AMBIGUO`. Nenhum candidato ou vínculo ativo retorna `DESCONHECIDO`.
   Pontuação abaixo do limiar retorna `PONTUACAO_BAIXA`. Quantidade ou
   detecção inadequada de rostos retorna `CAPTURA_INVALIDA`. Erros e
   timeouts retornam `FALHA_PROVEDOR`.

Endereço e chaves do CompreFace ficam no backend.
`ACADEMIA_ACCESS_SIMILARITY_THRESHOLD` controla o limiar de correspondência
separadamente da detecção. A comparação de fotografias fica limitada ao
reconhecimento. Prova de vida e aferição de acurácia exigem ensaios próprios.

## REST e reenvio

| Rota | Controle | Entrada |
|---|---|---|
| `POST /api/v1/atendimento/reconhecimento` | Sessão de atendente e CSRF | `evento_id` UUID, `direcao`, `imagem_base64` |
| `POST /api/v1/acesso/identificacoes` | Bearer de integração facial | Evento normalizado de origem confiável |

Exemplo externo:

```json
{
  "schema_version": 1,
  "evento_id": "51d2000a-b5a4-41a6-83b9-a9e4cda5bcec",
  "ocorrido_em": "2026-11-24T12:00:00Z",
  "direcao": "ENTRADA",
  "resultado": "CORRESPONDENCIA",
  "subject": "304f294f-6358-4749-893a-b226dae22779",
  "similaridade": 0.972
}
```

Configure um token exclusivo da integração em `ACADEMIA_ACCESS_IDENTIFICATION_TOKEN`
no ambiente privado. A rota externa exige essa configuração. As direções são
`ENTRADA` ou `SAIDA`. O resultado `CORRESPONDENCIA` requer `subject` e
`similaridade`. Para `DESCONHECIDO`, `AMBIGUO`, `CAPTURA_INVALIDA` e
`FALHA_PROVEDOR`, esses campos ficam ausentes. O backend atribui a origem e
revalida limiar e vínculo. O cliente interno é determinado pelo AcademIA.

O recibo contém versão, ID interno, ID do evento de origem, origem, horário,
direção, resultado, similaridade e cliente quando identificado. A resposta
ao atendente acrescenta o nome cadastral. O navegador envia apenas a foto,
a direção e o ID do evento. HTTP 201 confirma o primeiro registro. HTTP 200
devolve o registro anterior quando o conteúdo coincide. Mesmo ID com
conteúdo divergente retorna 409. Formato inválido, campos extras e credenciais
inválidas seguem os erros definidos para a API.

A migration 0021 guarda a tentativa em `evento_acesso`. A chave é origem e
ID externo. Um lock transacional por chave serializa reenvios concorrentes.
O banco guarda o resumo criptográfico usado para deduplicar e o resultado
normalizado, sem foto, vetores, sujeito do provedor ou credenciais.
Autorização, passagem e contagem de frequência ou lotação são etapas próprias.
