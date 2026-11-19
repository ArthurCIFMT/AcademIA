# Catálogo para demonstração acadêmica

O arquivo [catalogo-demonstracao-v1.json](catalogo-demonstracao-v1.json) contém
16 equipamentos e 30 exercícios sintéticos em português, com combinações
obrigatórias/alternativas de recursos e dispensa explícita para peso corporal.
Serve para testar cadastro, disponibilidade, editor manual e candidatos da IA.
Não contém pessoas, senhas, fichas prontas ou recomendações clínicas.
As descrições não integram o corpus RAG e não são evidências bibliográficas.

Na pasta `backend/`, com PostgreSQL aberto e migrations aplicadas:

```powershell
uv run --locked --env-file ../.env python -m scripts.seed_catalog --actor UUID_DO_ADMINISTRADOR_ATIVO
```

O UUID é o identificador do administrador autenticado, obtido por
`GET /api/v1/auth/session`. O comando exige um administrador ativo,
usa exclusivamente `academia_dev` e aplica tudo em uma transação.
Ele não altera schema nem depende do LLM, do banco vetorial ou do SMTP.
Não execute o SQL de teste abaixo no desenvolvimento para obter a carga.

- Não apaga ou atualiza cadastros existentes, inclusive inativos/indisponíveis.
- Reutiliza equipamentos e exercícios encontrados por nome normalizado.
- Equipamentos da própria carga têm UUID estável, preservando edições de nome.
- Repetir sem renomear exercícios não duplica registros; renomear um exercício
  torna seu nome original livre para um novo cadastro da carga.
- Usa os serviços de equipamentos/exercícios e registra a autoria na auditoria.
- Relata quantos registros criou e quantos preservou; não é executado no startup.
- A disponibilidade real é revalidada normalmente: recurso preservado e
  indisponível continua tornando dependentes inelegíveis.

O arquivo [catalogo_exercicios_sintetico.sql](catalogo_exercicios_sintetico.sql)
é uma fixture anterior exclusiva de `academia_test`. As integrações da carga nova
também usam esse banco isolado e revertem suas transações.
