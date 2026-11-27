# 04 — Envio e reconhecimento facial

**Estado da entrega: CONCLUÍDO.** Envio corrigido e cadastro e reconhecimento confirmados com CompreFace real.

Ao reusar o cartão, execute primeiro a verificação focal. A correção fica limitada aos caminhos abaixo e depende de uma regressão reproduzida.

## Tarefa

Reproduzir e corrigir a falha percebida no envio de foto, distinguindo seleção, registro da referência, nova captura e disponibilidade do CompreFace.

## Escopo permitido

- `frontend/src/features/biometrics/` e `backend/app/modules/access/biometrics/`. Em `backend/app/modules/access/events/{http.py,service.py}`, apenas a integração direta da captura e do resultado de identificação.
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

Em `backend/` com PostgreSQL isolado e em `frontend/`, respectivamente:

```powershell
uv run --locked pytest -o addopts='' tests/access/test_facial_reference.py tests/access/test_identification.py -k 'not real'
npm test -- src/features/biometrics/ClientBiometrics.test.tsx src/features/biometrics/FacialRecognition.test.tsx
```

Confira indicação da seleção, confirmação após recarga, recusa de imagem inválida, retomada de pendência e preservação da referência anterior quando a troca falhar. Para verificar o serviço real, prepare a coleção sintética isolada de ACS-01/02 conforme `docs/testes/comandos.md` e rode, em `backend/`:

```powershell
$env:ACADEMIA_TEST_COMPREFACE = '1'
uv run --locked pytest -o addopts='' 'tests/access/test_facial_reference.py::test_register_replace_and_preserve_consistency[real]' 'tests/access/test_identification.py::test_capture_and_authenticated_replay[real]'
```

Exija cadastro e reconhecimento com outra captura sintética, seguidos da limpeza prevista pelo ensaio. Se a instância de teste estiver indisponível, registre o motivo e separe esse resultado da prova com dublês. Para o fluxo visual com catraca simulada, use o comando Edge do cartão 05.
