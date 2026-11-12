# ADR-010 — Amostra acadêmica reduzida e avaliação estável

Status: ACEITA por autorização expressa do responsável em 2026-11-12.

O responsável autorizou demonstrações menos complexas, com menos séries, campos
opcionais a definir e menos retrabalho. Aplicar o [escopo didático](../../requisitos/escopo-ia-academico.md)
a uma nova amostra v3, mantendo todos os casos críticos e critérios de qualidade.
V2 e seus resultados não são apagados nem reaproveitados como aceite da amostra nova.

Não alterar API, banco, equipamento, campos de saúde ou prompts de produção.
O pedido sintético fornece limites de até dois exercícios/dia e duas séries;
o avaliador confere o resultado publicado. Séries, repetições, IDs e recursos
continuam obrigatórios. Carga/cadência null são explícitos, sem dado inventado.
Mudar a ficha-base de adaptação do teste para uma/duas séries e substituir a
progressão 3→4 por 1→2, preservando a demonstração de incremento/decremento.
Não converter ausência de saúde em elegibilidade, nem dispensar evidências.

A amostra é preparada antes do ensaio e fixa os mesmos 27 IDs/30 cenários.
O avaliador também entra na identidade das partes; não editar arquivos que
afetam seu hash enquanto o ensaio está em execução. Atualizar apenas resultados
e documentação depois, sem mudar código/casos para reinterpretar a saída.
Lotes/retomadas preservam a versão e recusam selecionar melhores respostas.
Lotes não aumentam quota diária; apenas evitam repetir casos concluídos.

Não exigir ampla periodização, cargas individuais, rotina avançada ou cobertura
clínica de todas as doenças como condição da demonstração reduzida. Esses limites
são declarados; não significam aprovação universal do modelo ou do treino.
Continuam qualidade/latência reais, JSON, isolamento, segurança e equipamentos.
Sem disponibilidade do provedor, registrar pendência de AI-06, não um sucesso.
