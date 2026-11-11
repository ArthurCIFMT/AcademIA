# Amostras sintéticas de extração

Arquivos artificiais exclusivos dos testes; não compõem literatura ou evidência
científica. Gerados com ReportLab/DejaVu Sans e pypdf, sem dados reais.
expectativas.json contém as frases/símbolos conferidos visualmente na amostra.

| Arquivo | Finalidade |
|---|---|
| simbolos.pdf | Duas páginas, marcadores, >=, <=, ≥, ≤, %, °C, µg e negações; tabela sintética |
| simbolos.txt | UTF-8, cabeçalhos e linhas, com os mesmos símbolos |
| escaneado.pdf | Página somente em imagem; requer OCR, que não é implementado |
| misto.pdf | Página textual, página em imagem e página em branco; não aceitar documento parcialmente legível como concluído |
| vazio.pdf | Página vazia; nenhum conteúdo textual útil |
| protegido.pdf | Cópia sintética criptografada; rejeitada sem tentar senha ou descriptografia |

As saídas de renderização e o gerador usado na preparação são temporários,
fora do repositório. Não é necessário ReportLab para executar os testes: os PDFs
já estão versionados. O extrator usa pypdf travado no lockfile e o processo isolado.

.gitattributes classifica estes PDFs como binários para preservar bytes e offsets
PDF, evitando normalização automática de quebras de linha em clones Windows/Linux.
