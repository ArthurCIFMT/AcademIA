# Comparação e diagrama da modelagem após a revisão 0016

O [painel navegável](index.html) separa o modelo conceitual original, o físico do
MVP antes/depois da normalização e o escopo lógico completo. A comparação não
regrava o [MER original em PNG](../original/MER_Academia_Completo_v4.drawio.png).

| Retrato | Tabelas/entidades | Colunas | FKs físicas |
|---|---:|---:|---:|
| MER original fornecido pelo responsável | 18 entidades conceituais | Não comparadas a colunas físicas | Não comparadas a FKs físicas |
| MVP físico antes da revisão 0016 | 32 tabelas | 262 | 53 |
| MVP físico após a revisão 0016 | 31 tabelas | 258 | 51 |
| Modelo lógico completo após a revisão | 42 tabelas | 331 | Inclui capacidades futuras; não é contagem física instalada |

As onze tabelas futuras são academia, plano, matricula, cobranca, pagamento,
biometria, evento_acesso, decisao_acesso, catraca_comando, presenca e aula_ocorrencia.
Academia é configuração singleton planejada; as outras pertencem às extensões
de matrícula/acesso, financeiro e agenda. Não foram criadas antecipadamente.

## Ver o resultado

- [Imagem comparativa](comparacao-modelagem.png), para apresentação acadêmica.
- [Diagrama físico completo em SVG](fisico-final-diagrama-completo.svg), ampliável
  sem perder definição, com as 31 tabelas, 258 colunas e 51 FKs.
- [Diagrama editável no draw.io](fisico-final.drawio), gerado do mesmo retrato físico.
- [Modelo lógico completo DBML](../modelo-logico.dbml), [JSON](../modelo-logico.json)
  e [dicionário](../dicionario.md), incluindo o escopo futuro.

O diagrama físico usa metadados do ORM SQLAlchemy vigente, comparados com as
migrations nos testes. É a representação das colunas/FKs implementadas; uma FK
composta é uma única constraint com vários pares de colunas. Referências simples
do DBML lógico não substituem essas proteções de titularidade. Qdrant é um banco
vetorial separado e não aparece como tabela PostgreSQL adicional.

O crescimento em relação às 18 entidades originais decorre de concretização:
papéis e credenciais, versões/dias/itens, recursos alternativos, pareceres,
curadoria/ingestão, execução da IA e auditoria possuem estruturas próprias.
Uma entidade conceitual pode originar várias tabelas; essas contagens não são
uma comparação de memória ou desempenho. A redução aplicada foi uma tabela,
quatro colunas e duas FKs, além de cópias JSON internas removidas.

## Escopo e evidências

A [ADR-013](../../decisoes/ADR-013-normalizacao-persistencia-ia-chat.md) descreve
as fontes canônicas e o que foi preservado. O [relatório de backup, migração e
regressão](../../../testes/otimizacao-modelagem-20261119.md) registra os resultados
desta versão. Backups privados e bancos ficam fora do Git. Testes históricos
mantêm seus hashes e não são apresentados como reexecução da versão atual.
Não há promessa de redução de bytes ou latência sem medição própria.
