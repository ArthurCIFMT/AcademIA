# Otimização da modelagem, backup e regressão — 2026-11-19

## Resultado e escopo

Revisão 0016 aplicada ao banco de desenvolvimento depois do backup conferido,
ensaio com rollback e regressão do MVP. Fontes e schema são compatíveis e os
dados fora das duplicações aprovadas foram preservados por comparação de todas
as tabelas antes/depois. A [ADR-013](../arquitetura/decisoes/ADR-013-normalizacao-persistencia-ia-chat.md)
explica as fontes canônicas. Contratos REST/JSON, permissões, triagem, versões,
parecer, equipamentos e prompts enviados ao LLM continuam com as mesmas regras.

| Retrato | Entidades/tabelas | Colunas | FKs físicas |
|---|---:|---:|---:|
| MER original | 18 entidades conceituais | Não equivalem diretamente a colunas | Não comparadas |
| MVP antes | 32 | 262 | 53 |
| MVP otimizado | 31 | 258 | 51 |
| Modelo lógico completo atual | 42 | 331 | Inclui 11 tabelas futuras |

O [painel visual](../arquitetura/modelo-de-dados/visualizacao-otimizada/index.html)
e o [diagrama editável](../arquitetura/modelo-de-dados/visualizacao-otimizada/fisico-final.drawio)
mostram todas as tabelas/colunas/relações físicas, incluindo FKs compostas.
O [MER original](../arquitetura/modelo-de-dados/original/MER_Academia_Completo_v4.drawio.png)
foi preservado. A análise anterior permanece histórica; não foi reescrita como
se a otimização já tivesse sido aplicada naquela revisão.

## O que foi simplificado

- Removido conversa, marcador 1:1 que apenas repetia o ID do cliente. Mensagem
  usa cliente_id diretamente, com índice/unicidade e FK composta de titularidade.
- Removida a FK simples de contexto redundante; a composta continua protegendo
  existência e dono, inclusive aceitando contexto nulo antes da primeira ficha.
- Removida mensagem.pergunta física; a propriedade/DTO lê pedido.mensagem.
  Pedido congelado, janela histórica e hashes permanecem intactos.
- Removido triagem.resumo duplicado; resumo completo continua em
  execucao_ia.resultado.triagem. Metadados/decisões da triagem permanecem auditáveis.
- Removidos etapa_ia.dados e resultado.consumo duplicados. Consumo é projetado
  das colunas de etapa, com soma de tokens derivada. Ausente continua desconhecido;
  zero explicitamente reportado continua zero. Restrição SQL exige o par coerente.

Foram removidas uma tabela e quatro colunas; duas FKs deixaram de ser necessárias.
No pequeno banco local havia 7.533 bytes de representações UTF-8 dos conteúdos
duplicados removidos (399 pergunta, 3.573 triagem, 3.539 etapa e 22 consumo).
Esse valor mede texto lógico, não páginas liberadas no disco: sem VACUUM FULL,
ensaio de escala, EXPLAIN ou promessa de desempenho. A principal vantagem é
evitar divergências de cópias e reduzir dados privados repetidos.

Manter o restante do schema foi uma decisão: identidade, histórico, recursos
alternativos, parecer, validação, literatura e auditoria possuem responsabilidades
distintas. Voltar a 18 tabelas só para igualar o MER conceitual removeria detalhes
necessários. Onze tabelas de matrícula/acesso/financeiro/agenda/configuração ainda
são futuras; não foram antecipadas por esta otimização.

## Backup e aplicação segura

Backup local privado em Documents/Codex/academia-otimizacao-modelagem-20261119/backup-antes:
ZIP dos 694 fontes versionados, MER, SPEC, DBML/JSON; bundle do histórico Git;
dumps custom de academia_dev/academia_test; Qdrant e corpus locais. ZIP relido
por hash e bundle verificado. Credenciais/.env, dependências e backups não entram
no Git. O guia LEIA-ME.txt e os manifestos da pasta registram a recuperação.

O dump de desenvolvimento foi restaurado efetivamente em academia_test vazio,
numa transação revertida, comparando contagens/hashes de todas as 32 tabelas.
A comparação inicial diferiu na representação temporal; padronizado UTC/ISO,
a segunda passou. O banco de testes voltou vazio. Antes da aplicação, migration
também foi ensaiada em transação de desenvolvimento e revertida, preservando
o estado bruto anterior e a revisão 0015.

Na aplicação definitiva, uma transação comparou novamente o conteúdo canônico
de todas as tabelas; somente representações duplicadas/marcadores foram retirados.
Dados cadastrais, contas, fichas, onboarding, literatura, pedidos, hashes, recibos,
eventos e autoria não foram substituídos por fixtures ou apagados por limpeza.
Nenhuma migration já aplicada foi editada. O banco de desenvolvimento está em0016;
academia_test conserva o rollback dos ensaios. API/frontend de uso manual não
foram ligados para usuários; o E2E usou servidores temporários próprios.

Upgrade aborta antes do DDL se encontrar cópias privadas divergentes. Downgrade
0015 recompõe as colunas removidas e conversas de clientes com mensagens a partir
dos valores canônicos; marcadores vazios sem semântica independente só são
recuperados exatamente pelo dump. Não executar código antigo sobre banco novo.
Ver o [guia do banco](../../database/README.md#backup-e-restauração-da-revisão-0016).

## Testes executados

| Verificação atual | Resultado |
|---|---|
| Backend completo unitários/contratos | 359 aprovados |
| Backend completo integração/banco | 187 aprovados; 3 opt-in de LLM real ignorados |
| Frontend completo | 94 aprovados em 20 arquivos |
| E2E navegador/API/PG/SMTP | 8 jornadas aprovadas, uma tentativa cada; migration0016 e rollback confirmado |
| Estático backend | Ruff/formato, mypy 238 fontes aprovados |
| Estático frontend | Lint, tipos e build aprovados |

Casos novos verificam fonte única, desconhecido/zero conhecido, reserva/despacho/
cancelamento/releitura, ida/volta0015↔0016, mensagens legadas, replay sem nova
chamada, abortar legado divergente sem migration parcial, JSON/pergunta inválidos,
cliente inexistente/contexto alheio e par de tokens. Os 16 focais aprovados na
primeira rodada e cinco focais na repetição não são somados aos comandos completos.
Dois focais novos falharam inicialmente por um UPDATE que não alcançava linhas
e um literal JSON interpretado como bind SQLAlchemy; os testes foram corrigidos,
mantendo todas as guardas. A repetição completa passou. Lint inicial das linhas
SQL também foi corrigido sem alterar os comandos executados.

Os oito E2E exercitam cadastro/convite/onboarding/treino manual, duas sessões/CSRF,
triagem grave/ausente, geração/adaptação, retenção/rejeição/exportação, equipamentos,
indisponibilidade da IA e recuperação/perfis. A [captura sintética de celular](otimizacao-modelagem-20261119-celular.png)
mostra a ficha consultável; logs brutos ficam na saída local do E2E. Nenhuma
conta de desenvolvimento aparece na captura.
PostgreSQL/Qdrant/E5/Mailpit reais na integração; LLM controlado. Nenhuma chamada
externa nova, retry ou contratação de plano pago. Os três testes ignorados exigem
ativação explícita de LLM real e não são aprovação por herança.
Os relatórios AI-06/TST-01 antigos conservam a identidade originalmente exercitada.

## Reprodução

Usar os [comandos existentes](comandos.md) em ambiente isolado e uma pasta nova
de saída, mantendo chaves LLM removidas do processo. Pesos E5 locais e Mailpit
ativos para seus ensaios. Os wrappers temporários desta execução ficam fora do
Git; não foram adicionados scripts pontuais de migração/manutenção ao projeto.

```powershell
# backend/, depois de carregar configuração de teste sem chaves LLM
uv run --locked pytest -q
uv run --locked pytest -o addopts='' -m 'integration or database' -q
uv run --locked pytest -o addopts='' tests/ai/test_normalized_migration.py tests/ai/test_persistence_projection.py
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked mypy
```

Na integração definir ACADEMIA_TEST_MAILPIT=1 e ACADEMIA_TEST_EMBEDDINGS_REAL=1,
ACADEMIA_AI_REAL=0 e perfil principal; usar academia_test vazio e pesos locais.
Para E2E definir ACADEMIA_E2E=1 e executar python -m tests.acceptance --output
data/e2e/rodada-N com Node24/Edge conforme o guia existente. No frontend executar
npm test -- --run --maxWorkers=1, npm run lint, npm run typecheck e npm run build.
Na raiz verificar documentação/SPEC com os comandos de AGENTS.md.

[Recibo estruturado](otimizacao-modelagem-20261119.json): contagens, hashes dos
relatórios/fontes, limites e backup sem conteúdo privado. Artefatos brutos,
dumps, pesos, chaves, logs e scripts temporários continuam fora do Git.
