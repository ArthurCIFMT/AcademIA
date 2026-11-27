# 08 — Foto privada no perfil

**Estado da entrega: CONCLUÍDO.** Miniatura privada entregue. O armazenamento privado é definido na migration `0029`.

Ao reusar o cartão, execute primeiro a verificação focal. A correção fica limitada aos caminhos abaixo e depende de uma regressão reproduzida.

## Tarefa

Exibir ao titular uma miniatura associada ao cadastro facial confirmado na matrícula. Separar a imagem para exibição da referência técnica e das capturas de chegada.

## Escopo permitido

- `frontend/src/features/profile/` e processamento do cadastro confirmado em `frontend/src/features/biometrics/` se pertinente.
- `backend/app/modules/people/own_profile.py` apenas para a leitura privada. Em `backend/app/main.py`, ajuste somente a ligação dessa leitura ao perfil.
- `backend/app/modules/access/biometrics/{images.py,models.py,service.py}` para redução, coluna `biometria.foto_perfil` e ciclo de vida. Preserve a migration aplicada `0029_private_profile_photo.py`. Se houver regressão de schema demonstrada, use migration nova, dicionário e contrato afetados.
- `backend/tests/access/test_facial_reference.py`, `backend/tests/people/test_clients.py` e testes da exibição no perfil.

Mantenha armazenamento bruto do CompreFace e capturas de chegada segundo o GATE-08. A feature não cria consulta pública, não habilita foto em relatório e não fornece imagem à IA.

## Contexto e execução

Depende de 01, 03 e 04. Leia RN-05/10/23/34, ACS-01, GATE-08 e a documentação de perfil. A miniatura reduzida é gravada após cadastro confirmado. A referência anterior à migration pode não ter miniatura. A rota própria valida a sessão e lê somente a referência ativa do titular.

Gere uma cópia reduzida apenas da foto de referência cadastrada. Publique a miniatura privada quando a referência correspondente estiver ativa. Use rota autenticada do titular, sem cache público, sem ID externo do provedor e sem caminho livre de arquivo. Guarde os bytes fora das pastas públicas e fora do Git. Preveja substituição e limpeza coerentes com a referência. Trate interrupção de forma idempotente, sem registrar nova biometria em duplicidade para recuperar miniatura. Contas sem miniatura, inclusive referências antigas, exibem iniciais ou indicador de estado.

## Critérios de aceite

- Titular vê a miniatura após cadastro novo confirmado e recarga. Outros usuários, inclusive administradores, não consultam esse arquivo pela API de perfil.
- Troca confirmada atualiza a miniatura. Falha antes da confirmação mantém a exibição coerente com a referência ainda ativa. Referência excluída não deixa imagem consultável.
- Cadastros antigos funcionam sem miniatura. Fotografias de chegada, arquivos inválidos e imagens de tentativa não aparecem no perfil.
- Nenhuma foto, código externo ou caminho interno aparece em log, sessão, resposta administrativa ou relatório.

## Testes e entrega

Em `backend/` com PostgreSQL isolado e em `frontend/`, respectivamente:

```powershell
uv run --locked pytest -o addopts='' 'tests/access/test_facial_reference.py::test_register_replace_and_preserve_consistency[double]' tests/people/test_clients.py::test_own_address_is_optional_and_private
npm test -- tests/auth/session.test.tsx src/features/biometrics/ClientBiometrics.test.tsx
```

Confira a miniatura pelo titular após recarga, a recusa para outra conta, a substituição confirmada e a preservação anterior quando o envio falhar. Com conta sem miniatura, confira o indicador ou iniciais. Faça a inspeção em **Meu perfil** com um cliente sintético. Uma captura de chegada deve seguir o fluxo de identificação e deixar a imagem do perfil intacta. Para mudanças no cadastro biométrico, repita o ensaio real do 04 antes do aceite.
