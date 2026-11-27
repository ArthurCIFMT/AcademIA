# Checklist da revisão manual final do AcademIA

## Preparação

- Abra [Iniciar AcademIA.cmd](../../Iniciar%20AcademIA.cmd) com dois cliques e aguarde **Sistema pronto**. O [guia do iniciador](../instalacao/iniciar-com-dois-cliques.md) mostra como abrir o site, o Mailpit e encerrar os serviços.
- Use contas de teste para administrador, atendente, instrutor e dois clientes. Faça os cadastros, fichas e simulações com dados fictícios. Para o teste facial, use as amostras sintéticas preparadas no ambiente de teste.
- Separe as sessões com perfis de navegador diferentes ou use uma janela normal e outra anônima. Janelas normais do mesmo perfil compartilham a sessão.
- Marque cada item como **Passou**, **Falhou** ou **Pendente**. Se houver falha, anote papel, tela, passos, resultado observado e horário. Use capturas sem senha, cookie, token, foto ou dado de saúde.

## Jornada principal

| Item | Ação no site | Resultado esperado | Resultado |
|---|---|---|---|
| M01 · Sessão | Em janela anônima, abra `/area/administracao/clientes`. Teste uma senha incorreta, entre com uma conta de teste, saia e reabra a URL. | A rota protegida pede login sem sessão válida. A senha errada não abre a área. Depois de sair, a URL continua protegida. | ☐ |
| M02 · Papéis | Entre como administrador e abra **Painel**. Entre como cliente em outra janela e tente abrir a mesma área administrativa pela URL. | O administrador vê o painel. O cliente recebe acesso não permitido e os dados administrativos não aparecem. | ☐ |
| M03 · Cadastro e e-mail | Como atendente, em **Clientes e convites**, cadastre um cliente de teste. Use **Abrir e-mails de teste** no iniciador, abra o link de primeiro acesso e defina a senha. | O cliente consegue entrar. A mensagem chega ao Mailpit local, e o link consumido não permite repetir a ativação. | ☐ |
| M04 · Meu perfil | Como cliente A, salve um endereço fictício em **Meu perfil** e recarregue a página. Entre como cliente B em outra janela e abra o próprio perfil. | O endereço de A persiste e B vê apenas seu próprio cadastro. | ☐ |
| M05 · Onboarding | Envie o convite de onboarding ao cliente de teste. Abra o link do Mailpit, confira a idade antes de concluir e salve um rascunho. Reabra e tente finalizar com campos obrigatórios faltando. Depois complete e consulte a versão concluída. | A idade vem do cadastro. O rascunho reaparece, campos obrigatórios são validados e a idade na conclusão fica registrada. | ☐ |
| M06 · Ficha manual e parecer | Como administrador, designe um instrutor. Como instrutor designado, abra **Meus clientes**, monte uma ficha com exercício ativo e publique. Como cliente, abra **Meus treinos**. Depois registre um parecer com o instrutor. | A ficha aparece antes do parecer e continua consultável depois. Um instrutor sem designação não edita esse cliente. | ☐ |
| M07 · Assistente e geração | Como cliente, abra **Assistente**, faça uma dúvida simples sobre exercício e confira a resposta e a fonte. Em **Gerar ficha**, use um onboarding concluído e elegível. | O chat responde em português com fonte ou informa falta de suporte. A ficha gerada usa exercícios elegíveis da academia. Quota ou indisponibilidade deve aparecer como erro controlado. | ☐ |
| M08 · Matrícula e foto | Como atendente, abra **Clientes e convites → Matrícula e acesso** e matricule sem compra confirmada. Cadastre a referência sintética, recarregue e abra **Meu perfil** como o próprio cliente. | A matrícula é registrada sem pagamento. A foto mostra seleção e confirmação, e a miniatura só aparece ao cliente dono da referência. Se o CompreFace estiver indisponível, marque o teste facial como pendente. | ☐ |
| M09 · Entrada e frequência | Na área do atendente, faça a nova captura em **Reconhecimento facial**, identifique o cliente e solicite autorização. Confira **Lotação atual**. Se for testar a passagem, use o [guia do simulador de catraca](../instalacao/catraca-ficticia.md#ensaio-http-e-retorno) e consulte frequência após a confirmação. | O comando pode ficar aguardando a passagem. A lotação só muda com passagem simulada confirmada. | ☐ |
| M10 · Celular e teclado | Em janela estreita ou no modo responsivo do navegador, navegue por **Meus treinos**, **Assistente** e **Equipamentos disponíveis**. Use Tab e Enter para acessar ações. | Texto e botões são legíveis, o foco fica visível e as ações cabem na tela. | ☐ |

## Conferências de segurança

- [ ] Na aba **Rede** do navegador, confira apenas os nomes dos campos das respostas de login e perfil. Senha, hash de senha e chave de provedor ficam ausentes do corpo. Evite copiar cabeçalhos, cookies ou valores.
- [ ] Abra um recurso de B enquanto estiver autenticado como A, usando apenas os dois cadastros de teste. A tela deve negar o acesso ou indicar que o recurso não existe, sem exibir detalhes de B.
- [ ] Verifique que mensagens de erro na interface são compreensíveis e não mostram caminhos, SQL ou stack trace. A falha controlada de banco e o Git são verificados no [cartão 12](../prompts/revisao-manual/12-seguranca-basica.md).

Se o resultado de IA ou CompreFace depender de um serviço indisponível, registre
qual serviço e a mensagem exibida. Para conferir a triagem, use um caso sintético
com informação essencial desconhecida. A tela deve indicar o campo pendente e
preservar a ficha vigente. O desconhecimento isolado sobre medicação pode seguir
para análise quando as demais respostas essenciais forem negativas e não houver
observações.

Ao terminar, use **Encerrar sistema** no painel ou
[Encerrar AcademIA.cmd](../../Encerrar%20AcademIA.cmd).
