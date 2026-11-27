# 04 — Envio e reconhecimento facial

## Tarefa

Reproduzir e corrigir a falha percebida no envio de foto, distinguindo seleção, registro da referência, nova captura e disponibilidade do CompreFace.

## Escopo permitido

- `frontend/src/features/biometrics/`, `backend/app/modules/access/biometrics/` e código de integração direta de reconhecimento em `backend/app/modules/access/`.
- Testes focais em `backend/tests/access/`, testes de componentes e `frontend/tests/e2e/access.spec.ts`. Documentação de biometria, CompreFace e comandos de teste afetados.
- Verificar impacto no iniciador conforme AGENTS.md. Uma mudança estritamente necessária ao preparo local pertence ao escopo transversal. Preserve os serviços e configurações do usuário.

Deixe a reorganização da ficha do cliente para 05 e a foto no perfil para 08. Mantenha regras de autorização/ocupação, limiar e modo de armazenamento biométrico já aprovados.

## Contexto e execução

Depende de 01. Leia RF-20/21/22/36/37, RN-06–RN-10, ACS-01/02 e GATE-08. A interface limpa o seletor ao ler a foto e deve comunicar que conseguiu selecionar o arquivo. Verifique a resposta real da API e a prontidão do CompreFace dedicado em loopback. Diferencie CompreFace configurado de serviço pronto.

Mostre nome e, se apropriado, uma prévia local temporária antes do envio. Use estados claros para seleção, envio, cadastro confirmado e erro. Trate rejeição por tipo, tamanho, dimensões, ausência de rosto e falha do provedor. Após o cadastro, confirme o estado da referência e a data após recarga. Nova captura para reconhecimento é uma ação própria. Um resultado positivo inicia a autorização de acesso existente. Preserve idempotência, troca de referência e confirmação manual auditada.

## Critérios de aceite

- Uma foto válida selecionada tem indicação clara, pode ser enviada e tem confirmação persistida. A prévia é descartada ao terminar a operação.
- O erro é observável e compreensível para foto inválida, CompreFace indisponível e referência pendente. Uma falha na substituição preserva a referência confirmada anterior.
- Com CompreFace real em ambiente isolado, o cadastro confirmado é seguido de reconhecimento por outra captura da mesma identidade. Registre separadamente os ensaios com respostas controladas. Preserve fronteiras de sessão, matrícula e autorização.

## Testes e entrega

FE de seleção, envio e erros. Contrato e integração de `test_facial_reference.py` e testes focais de identificação. Use o ensaio real de ACS-01/02 em coleção de teste sintética e o Edge/Playwright previsto em `docs/testes/comandos.md`. Se o provedor estiver indisponível, registre o bloqueio e o restante que passou. O aceite real habilita 05 e 08 conforme suas dependências.
