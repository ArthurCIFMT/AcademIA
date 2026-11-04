# Materiais iniciais para o RAG do AcademIA

Coleta realizada em 3 de novembro de 2026, a pedido do responsável.
Esta pasta reúne **7 PDFs originais em português, com 326 páginas PDF**.
São candidatos a uma futura base de consulta; nenhum foi aprovado, indexado
ou usado para treinar/ajustar um modelo nesta entrega. Prompts e especificações
do sistema não foram alterados.

RAG usa documentos como fontes de consulta. Reunir estes arquivos é a coleta
bibliográfica, não o treinamento da IA nem a implementação do pipeline.

## Arquivos

| ID | Material e edição | Papel na coleção | Licença identificada |
|---|---|---|---|
| BR-MS-001 | [Guia de Atividade Física para a População Brasileira](documentos/ms-guia-atividade-fisica-2021.pdf) (2021) | Recomendações populacionais e contexto brasileiro. | CC-BY-NC-SA-4.0 |
| BR-MS-002 | [Guia de Atividade Física para a População Brasileira: recomendações para gestores e profissionais de saúde](documentos/ms-recomendacoes-gestores-profissionais-2021.pdf) (2021) | Apoio à comunicação e promoção de atividade física. | CC-BY-NC-SA-4.0 |
| BR-RBAFS-001 | [Atividade física para adultos: Guia de Atividade Física para a População Brasileira](documentos/rbafs-atividade-fisica-adultos-2021.pdf) (2021) | Fundamentação e metodologia das recomendações para adultos. | CC-BY-4.0 |
| BR-RBAFS-002 | [Atividade física para idosos: Guia de Atividade Física para a População Brasileira](documentos/rbafs-atividade-fisica-idosos-2021.pdf) (2021) | Contexto populacional e fundamentação das recomendações para idosos. | CC-BY-4.0 |
| BR-RBCM-001 | [Variáveis da prescrição de treinamento resistido aplicadas a hipertrofia muscular: uma revisão narrativa](documentos/rbcm-variaveis-treinamento-resistido-2022.pdf) (2022; publicação online em 2023) | Material complementar em português sobre variáveis da prescrição. | CC-BY-NC-4.0 |
| BR-SBC-001 | [Diretriz Brasileira de Hipertensão Arterial – 2025](documentos/sbc-hipertensao-arterial-2025.pdf) (2025) | Referência clínica para futura seleção de trechos sobre exercício e risco. | CC-BY-4.0 |
| BR-SBC-002 | [Diretriz Brasileira de Reabilitação Cardiovascular – 2020](documentos/sbc-reabilitacao-cardiovascular-2020.pdf) (2020) | Referência de avaliação e limites em contexto de reabilitação. | CC-BY-4.0 |

[Catálogo completo](catalogo.json): autoria, edição, DOI/ISBN, URLs de origem e de
download, licença/evidência, idioma, tamanho, número de páginas, SHA-256 e limitações.
[Referências complementares e lacunas](referencias-complementares.md): outras fontes
localizadas e temas que ainda precisam ser cobertos.

## Proveniência e reprodução

Os PDFs estão completos, sem tradução, edição, recorte ou conversão. O nome local
foi simplificado; direitos e avisos dos autores/editoras permanecem nos arquivos.
As cópias vêm da BVS do Ministério da Saúde, dos periódicos e da SciELO.

Cada obra mantém sua própria licença. Os dois guias do Ministério da Saúde usam
[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/);
a revisão da RBCM usa [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/).
As demais licenças e uma divergência de rotulagem no portal SciELO da diretriz de
reabilitação estão registradas no catálogo. Esta coleção é acadêmica e não comercial.
A organização da pasta não altera a licença de nenhuma obra nem atribui endosso
dos autores ao sistema.

## O que foi conferido nesta coleta

- Sete arquivos com assinatura PDF válida e abertura pelo leitor de PDF.
- Contagem de páginas, tamanho e SHA-256 de cada arquivo.
- Títulos e capas renderizadas, além de amostras de texto/expediente/licenças.
- Texto extraível nas amostras; isso não certifica extração fiel de todas as tabelas.
- Links bibliográficos e indicação expressa de licença nas fontes consultadas.

Os guias do Ministério possuem contagem física diferente da ficha catalográfica:
52 versus 54 e 20 versus 18 páginas. O catálogo registra as contagens reais dos
arquivos recebidos; isso não foi tratado como autorização para editar os PDFs.
A RBCM usa fascículo de 2022 e registra publicação online em 2023.

## Limites desta seleção

A seleção ainda não foi revisada integralmente por um profissional de Educação
Física/saúde. Os documentos têm públicos e níveis de evidência diferentes.
Uma revisão narrativa não tem o mesmo papel de uma diretriz. Os artigos da RBAFS
fundamentam o guia brasileiro e não são evidências totalmente independentes dele.

Há cobertura inicial de atividade física, adultos/idosos, variáveis de treinamento
resistido e contexto cardiovascular. Ainda faltam materiais específicos suficientes
para lesões articulares, adaptações por exercício e critérios operacionais de casos
graves, além de conferir atualizações e conflitos entre fontes. As diretrizes
clínicas incluem temas de diagnóstico/medicação que não se confundem com orientação
de treino de academia.

O catálogo mantém todos os itens em COLETADO_PENDENTE_REVISAO e aprovado_para_rag=false.
A presença no GitHub não significa aprovação para uso nas respostas do sistema.
