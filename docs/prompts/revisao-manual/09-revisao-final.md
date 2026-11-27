# 09 — Revisão final antes do VAL-02

**Estado da entrega: CONCLUÍDO.** Revisão executada. As falhas de integração apontadas depois foram corrigidas em 10 e 11.

## Tarefa

Conferir as correções entregues e produzir evidência suficiente para a regressão final do escopo vigente.

## Escopo e contexto

- Revisão de código, contratos e resultados, com execução de testes isolados. Mantenha os arquivos do projeto em leitura e encaminhe defeitos ao cartão responsável. Consulte VAL-01/02, manifesto, matriz de rastreabilidade e README deste pacote.
- Use `docs/testes/comandos.md`, `docs/testes/estrategia.md`, o guia visual e a documentação de CompreFace. Regressões encontradas retornam ao cartão de origem.
- A asserção legada de `0026` foi corrigida no 10. O cenário de matrícula em schema antigo foi corrigido no 11. A aceitação integral segue no VAL-02.

## Matriz mínima de revisão

1. Confira destino direto, celular, retorno, recarga, links antigos, seção ativa e teclado nos quatro papéis e em conta acumulada.
2. Confira dados próprios, endereço opcional para cadastros antigos, persistência da edição e permissão exclusiva do titular.
3. Confira seleção e confirmação da foto, preservação da referência em falha, miniatura privada, substituição e reconhecimento com CompreFace real. Identifique os ensaios que usaram dublês.
4. Confira continuidade da seleção do cliente, matrícula com ou sem pagamento, biometria pendente, contingência auditada e frequência após passagem simulada.
5. Confira idade derivada e snapshot histórico, dúvida complementar, dúvida essencial, bloqueio grave, preservação de chat/ficha e erro técnico controlado.

## Critérios de aceite

- Cada cenário indica requisito, ambiente, teste ou evidência manual, resultado e pendência.
- A revisão verifica links, SPEC, diff, migrations e compatibilidade do iniciador proporcionais ao impacto. Nenhum resultado controlado conta como evidência de provedor real.
- Registre o que está pronto para VAL-02 e o que ainda precisa de correção. Somente uma execução do VAL-02 pode registrar seu aceite.

## Testes e entrega

Selecione as linhas atingidas pela revisão. Os comandos focais estão nos cartões indicados. Execute uma vez cada seleção e anote resultado, revisão e dependências usadas.

| Cenário | Comando ou cartão | Resultado esperado |
|---|---|---|
| Navegação e perfil | FE dos cartões 02 e 03, E2E-08 e inspeção com quatro papéis | Destino correto, teclado, recarga e endereço privado |
| Biometria e matrícula | BE/INT dos cartões 04, 05, 08 e 11, e Edge de acesso | Foto confirmada, matrícula independente do pagamento e frequência só após passagem |
| Onboarding e triagem | BE/INT dos cartões 06 e 07, E2E-01, E2E-03 e E2E-04 | Idade atual e congelada, pendência específica e bloqueio grave |
| Schema e documentos | Cartão 10 e verificações abaixo | Ida e volta com head correto, sem divergência de metadados, e links válidos |

Na raiz do repositório:

```powershell
& ./backend/.venv/Scripts/python.exe scripts/verificar_documentacao.py
& ./backend/.venv/Scripts/python.exe scripts/gerar_spec.py --check
git diff --check
```

Use o runner do README para as jornadas do MVP. Confira o relatório de rollback. Separe CompreFace real, simulador de catraca e dublê. Para alteração que afete o iniciador, use o teste e o guia de ciclo real indicados no AGENTS.md. Registre falhas por cartão e preserve o estado de VAL-02.
