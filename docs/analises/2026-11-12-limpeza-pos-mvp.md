# Auditoria de limpeza após o MVP — 2026-11-12

Base: 79cee39263b33514f34492b87b24063d5b9ac67e. Escopo solicitado: limpeza e
referências, preservando implementação, prompts e material útil à avaliação.

## Inventário e decisão

Foram inventariados 653 arquivos versionados, com hashes antes da limpeza.
Existem somente três scripts avulsos, todos necessários e mantidos:

| Arquivo | Uso confirmado |
|---|---|
| [Gerador da SPEC](../../scripts/gerar_spec.py) | Compila/verifica as fontes do SPEC; exigido pelo fluxo documental. |
| [Verificador documental](../../scripts/verificar_documentacao.py) | Confere referências, requisitos, rastreabilidade, MER e catálogo. |
| [Bootstrap](../../backend/scripts/bootstrap_admin.py) | Instala o primeiro administrador; necessário para iniciar a revisão manual. |

Não foi localizado script de alteração pontual descartável versionado. CLIs
em módulos Python e runners de testes são ferramentas reutilizáveis, não restos
de edição. Migrations aplicam-se uma vez por banco, mas são essenciais para
reconstrução; não foram removidas. Helpers locais de entregas anteriores ficam
fora deste repositório e não fazem parte desta limpeza.

A única duplicação documental exata detectada foi o relatório E2E em
ai06-gemini/e2e-controlado.json e tst01-resultado.json. Ambos permanecem: um
preserva a evidência da integração Gemini e o outro é o insumo do aceite atual.
Uma evolução futura pode substituir o insumo vigente sem apagar aquela origem.

## Referências corrigidas

- [Preparação AI-06](../testes/preparacao-ai06.md): separação do histórico v2 e
  referência à amostra vigente v4; 27 casos continuam identificados como passado.
- [Demonstração v3](../testes/ai06-academico.md): rótulo de amostra histórica.
- [Reserva](../testes/ai06-reserva.md), [correção anterior](../testes/ai06-correcao-fundamentacao.md)
  e [Gemini](../testes/ai06-gemini.md): referências atuais e indicação de que
  pendências antigas não são o estado do MVP. A reserva permanece não qualificada.
- [Tabela de comandos](../testes/comandos.md): E2E vinculado ao aceite concluído;
  infraestrutura final segue seus próprios gates. Registros datados não foram apagados.
- [Guia do backend](../../backend/README.md): integrações já entregues e avaliação
  real de IA referenciadas no presente; comandos e comportamento permanecem iguais.

A SPEC foi apenas recompilada das fontes corrigidas. Não se redefiniram
requisitos, decisões, critérios, tecnologias ou escopo de implementação.

## Caches locais

O levantamento identificou 42 diretórios __pycache__, .mypy_cache, .ruff_cache
e .pytest_cache fora das dependências, com cerca de 135 MiB mensuráveis. Um
.pytest_cache possui leitura restrita no Windows. A retirada local usa quarentena
fora do projeto, preservando possibilidade de restauração; não é alteração Git.
A relação de caminhos e o resultado ficam na área local desta auditoria.

Não retirar ambientes Python, node_modules, build de preview, modelos E5,
.env, uploads, bancos, diretórios de dados ou recibos privados de avaliação.
Esses itens podem ser necessários ao uso local ou à reprodução das evidências.
Nenhum arquivo privado foi incorporado ao relatório ou ao Git.

## Verificação e limites

Prompts (67 arquivos), código, três scripts, lockfiles, migrations (15), JSONs de
requisitos/evidências, MER, PDFs (24), testes e configurações são preservados byte
a byte. Hashes das fontes modificadas restringem-se aos sete guias e à cópia
gerada da SPEC, além deste registro de auditoria.

As verificações abrangem referências documentais, compilação da SPEC,
preservação dos arquivos protegidos e reprodução da consolidação aprovada do
MVP. Não executar LLM, alterar banco ou repetir E2E/regressão funcional para uma
limpeza documental. O aceite continua registrado no
[relatório TST-01](../testes/tst01-consolidacao.json).

Análises, ADRs substituídos, amostras antigas, ensaios recusados e fontes de
reserva permanecem como histórico acadêmico. Não confundir um resultado antigo
com uma referência vigente, nem apagar falha ou material para reduzir o volume.

## Observação sobre cópias e finais de linha

A cópia obtida por git archive neste ambiente aplicou CRLF a arquivos que estão
em LF no checkout. Isso altera hashes auxiliares por byte do verificador, embora
os critérios e o hash normalizado do runtime continuem aprovados. Para conferir
a igualdade exata do recibo, a auditoria usou os bytes originais dos arquivos
protegidos. Nenhum final de linha do projeto foi alterado por esta limpeza.

A verificação de referências é local. URLs externas não foram consultadas nesta
limpeza; não se alteraram fontes ou citações bibliográficas.
