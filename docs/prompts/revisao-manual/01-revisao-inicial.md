# 01 — Revisão inicial e reprodução

## Tarefa

Conferir os relatos da revisão manual e preparar os cartões de mudança. Classificar o que já é reproduzível, o que depende do ambiente e o que exige mudança de requisito.

## Escopo e contexto

- Revisão somente leitura dentro do repositório. Use o README local e o contrato operacional vigente. Consulte UX-03, MEM-01, ACS-01/02/03/04, ONB-02/03, AI-01/05, GATE-08 e VAL-01/02.
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

Registre os ensaios realmente executados e o perfil utilizado. Entregue a matriz dos relatos em texto e avance para 02 quando a revisão independente estiver concluída.
