# 01 — Revisão inicial e reprodução

**Estado da entrega: CONCLUÍDO.** Diagnóstico e reprodução registrados na revisão dos fluxos após VAL-01.

## Tarefa

Conferir os relatos da revisão manual e preparar os cartões de mudança. Classificar o que já é reproduzível, o que depende do ambiente e o que exige mudança de requisito.

## Escopo e contexto

- Revisão somente leitura dentro do repositório. Use o README deste pacote e o contrato operacional vigente. Consulte UX-03, MEM-01, ACS-01/02/03/04, ONB-02/03, AI-01/05, GATE-08 e VAL-01/02.
- É permitido reproduzir pelo harness isolado com dados sintéticos se houver ambiente de teste preparado. Preserve o banco e a configuração de desenvolvimento. Não altere arquivos, migrations, manifesto, firewall, papéis de usuários ou contratos.
- Consulte `docs/testes/comandos.md` para os comandos de cada ensaio. Inspecione código, evidências registradas e saídas sanitizadas. Não exponha fotos, dados de saúde, e-mails reais ou credenciais.

## Verificações

1. Percorra início da área, navegação entre tarefas, troca de papel, catálogo de equipamentos e retorno às listas. Conte interações num exemplo desktop e num móvel e aponte onde se perde contexto.
2. Localize cadastro de referência, seleção/envio de foto, status, captura posterior e início do CompreFace. Separe erro de estado visual, validação, comunicação e biometria. Reporte indisponibilidade apenas quando medida.
3. Localize matrícula e compra simulada, e confirme quem pode simular, matricular, liberar a passagem e registrar referência. Identifique por onde o atendente deve continuar trabalhando com o mesmo cliente selecionado.
4. Confira o DTO da sessão e campos de cliente e funcionário, armazenamento do endereço ainda inexistente e política de imagem atual. Confirme de onde vem a idade do onboarding e em quais telas já aparece.
5. Localize a decisão para `NAO_SEI`, o motivo público e os campos envolvidos. Reproduza com fixtures se necessário. Classifique separadamente o que precisa de uma decisão nas regras de triagem.

## Critérios de aceite

- Cada relato tem fluxo, evidência, impacto, etapas afetadas e um critério observável para regressão.
- Causas confirmadas, hipóteses e testes pendentes estão identificados. Revisar cenários de autorização de titular, perfis acumulados, idade e falhas de serviço.
- As mudanças de comportamento propostas estão associadas às fontes vigentes. Todo resultado aprovado aponta para uma evidência.

## Testes e entrega

Na interface, reproduza com contas sintéticas nos papéis envolvidos. Anote a revisão, o papel, a rota, o viewport e o resultado observado. Use os cartões 02 a 08 para selecionar a verificação focal do relato.

Como checagem inicial, rode apenas os seletores relacionados ao relato. Em `frontend/` e `backend/`, respectivamente:

```powershell
npm test -- tests/auth/session.test.tsx
uv run --locked pytest -o addopts='' tests/people/test_clients.py::test_own_address_is_optional_and_private tests/ai/test_triage.py
```

O primeiro verifica restauração de sessão, troca de papéis e perfil. O segundo verifica titularidade do endereço e decisões de triagem. Use PostgreSQL isolado para o teste de perfil. Registre separadamente cenário aprovado, falha reproduzida e dependência indisponível. Encaminhe cada falha ao cartão correspondente.
