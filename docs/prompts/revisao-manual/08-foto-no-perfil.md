# 08 — Foto privada no perfil

## Tarefa

Exibir ao titular uma miniatura associada ao cadastro facial confirmado na matrícula. Separar a imagem para exibição da referência técnica e das capturas de chegada.

## Escopo permitido

- `frontend/src/features/profile/` e processamento do cadastro confirmado em `frontend/src/features/biometrics/` se pertinente.
- Contrato de perfil próprio em `backend/app/modules/people/`, serviço de cadastro em `backend/app/modules/access/biometrics/`, composição e armazenamento privado diretamente relacionados.
- Migration nova se a associação ao arquivo precisar de persistência, documentação de biometria/armazenamento e testes de titularidade, substituição e falha.

Mantenha armazenamento bruto do CompreFace e capturas de chegada segundo o GATE-08. A feature não cria consulta pública, não habilita foto em relatório e não fornece imagem à IA.

## Contexto e execução

Depende de 01, 03 e 04. Leia RN-05/10/23/34, ACS-01, GATE-08 e a documentação de perfil. Atualmente, a imagem bruta anterior não fica disponível para consulta. Ao executar este cartão, use a decisão registrada de guardar uma miniatura reduzida local após cadastro confirmado. Se essa decisão ainda estiver em aberto, preserve o indicador de referência e registre a parte dependente sem habilitar armazenamento novo.

Gere uma cópia reduzida apenas da foto de referência cadastrada. Publique a miniatura privada quando a referência correspondente estiver ativa. Use rota autenticada do titular, sem cache público, sem ID externo do provedor e sem caminho livre de arquivo. Guarde os bytes fora das pastas públicas e fora do Git. Preveja substituição e limpeza coerentes com a referência. Trate interrupção de forma idempotente, sem registrar nova biometria em duplicidade para recuperar miniatura. Contas sem miniatura, inclusive referências antigas, exibem iniciais ou indicador de estado.

## Critérios de aceite

- Titular vê a miniatura após cadastro novo confirmado e recarga. Outros usuários, inclusive administradores, não consultam esse arquivo pela API de perfil.
- Troca confirmada atualiza a miniatura. Falha antes da confirmação mantém a exibição coerente com a referência ainda ativa. Referência excluída não deixa imagem consultável.
- Cadastros antigos funcionam sem miniatura. Fotografias de chegada, arquivos inválidos e imagens de tentativa não aparecem no perfil.
- Nenhuma foto, código externo ou caminho interno aparece em log, sessão, resposta administrativa ou relatório.

## Testes e entrega

INT da persistência, substituição/falha e rota protegida, contratos API, FE do indicador e verificação no Edge com fixtures sintéticas. Verificar o comportamento com CompreFace real quando a mudança afetar seu cadastro. Rode as suites e verificações documentais conforme `docs/testes/comandos.md`. Próximo 09.
