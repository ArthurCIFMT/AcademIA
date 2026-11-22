# Experiência, navegação e qualidade visual

Status: [aceite visual das telas existentes concluído em UX-09](../testes/ux09-aceite-visual.md),
com [referência visual](../interface/README.md) definida em UX-01.
A [base visual foi aplicada em UX-02](../interface/componentes.md) e a
[navegação por perfil e telas de acesso em UX-03](../interface/navegacao-e-acesso.md).
Solicitação do responsável em
2026-11-19, após a revisão manual do MVP. Complementa RNF-14, RNF-19 e RNF-20.

## Objetivo e limites

Entregar um site de academia com aparência consistente, legível e organizada,
adequado a clientes no celular e às operações de instrutores e funcionários.
O fluxo deve explicar o próximo passo e preservar os controles de segurança.
O caráter acadêmico não dispensa qualidade de apresentação ou clareza de uso.

A reformulação é incremental, com React/TypeScript/Vite e contratos existentes.
Não muda schema, backend, permissões, triagem, prompts internos da IA, modelos,
corpus, publicação, parecer posterior, retenção ou quantidade de chamadas.
Editar o próprio perfil é capacidade funcional separada, ainda não especificada
por este trabalho; não criar botão sem função, API imaginária ou formulário falso.
Matrícula, biometria, agenda, dashboard e financeiro só ganham navegação quando
suas funcionalidades existirem. Dados demonstrativos vêm de fixtures sintéticas,
com origem identificável; não mostrar estatísticas, fotos ou progresso fictícios.

## Direção visual e arquitetura de informação

Adotar inicialmente tema claro, superfícies neutras, textos escuros e acentos
em azul-petróleo/verde. UX-01 define cores concretas com contraste medido,
tipografia, escala de espaçamento, bordas, estados e componentes. Preferir fontes
do sistema e CSS existente; novos pacotes ou recursos externos exigem justificativa.
Não carregar rastreadores, fontes remotas ou conteúdo de terceiros no onboarding.
A direção pode ser refinada pela revisão, mantendo uma única referência visual.

No desktop, usar estrutura com navegação lateral, cabeçalho discreto e conteúdo
principal; no celular, navegação compacta acessível sem cobrir conteúdo/ações.
A navegação informa seção ativa, rótulos em português e caminho de retorno.
Papéis acumuláveis mantêm suas permissões reais: alternar a área de trabalho não
altera papéis. Links de acesso direto continuam funcionando. Não tratar menu
oculto como autorização. A curadoria técnica RAG permanece oculta por padrão.

| Área | Organização proposta, somente para capacidades existentes |
|---|---|
| Cliente | Meus treinos; Assistente; Meus dados de treino (onboarding); conta/sair. |
| Instrutor | Meus clientes; fichas e editor manual; revisões pendentes; avaliações; catálogo autorizado. |
| Atendente | Clientes e convites; outras operações apenas quando seus módulos forem entregues. |
| Administrador | Clientes; funcionários; designações; equipamentos; exercícios. Indicadores somente com DSH-01 entregue. |

Os rótulos podem ficar mais naturais, sem prometer alteração de dados inexistente.
O formulário de convite já pode abrir em página dedicada fora dos menus da conta,
na mesma aplicação. Não migrar dados de saúde para Google Forms ou outro provedor.

## Fluxos prioritários

Onboarding: etapas identificáveis de objetivos/rotina, dados físicos, saúde e
revisão; salvar/retomar e navegar sem descartar campos. Preservar a distinção
entre ausente, null, negativa explícita e desconhecido, os campos condicionais e
a confirmação de atualização. Um passo visual não equivale à conclusão no servidor.
Não salvar dados clínicos em localStorage, URL, analytics ou capturas com dados reais.

Assistente: uma entrada de navegação com ações identificáveis para tirar dúvidas,
gerar treino e solicitar adaptação. A apresentação pode reunir as telas, mas chat
informativo, geração e adaptação continuam usando seus contratos separados.
Chat usa RAG e resposta limitada às evidências; a ficha vem do LLM com validação
do backend. Conversar não dispara treino. Geração/adaptação exigem ação explícita,
onboarding pertinente e confirmação já prevista no fluxo. Não acrescentar chamadas
de LLM por navegação, abertura de tela, atualização, render ou efeito React.

Mostrar mensagem do cliente/resposta, fontes legíveis com título/página, estado
salvo e distinção entre insuficiência, bloqueio, falta de evidência, quota e falha.
Usar somente estados reais: sem progresso percentual ou etapas inventadas.
Consultar estado não é reenviar pedido. Nova tentativa é explícita, com nova chave;
mesma solicitação preserva o resultado anterior. Arquivos, hashes e termos de
infraestrutura ficam fora do fluxo comum, salvo detalhe necessário ao usuário.

Treinos: organização por dia, exercício, recurso, séries, repetições e descanso;
histórico e parecer legíveis no celular. Ficha PENDENTE ou REJEITADA permanece
consultável conforme o domínio; expurgo, recursos indisponíveis e fontes revogadas
não são escondidos nem restaurados visualmente. Instrutor conserva criação manual,
revisão posterior, autoria, confirmação de publicação e tratamento de conflitos.

## Critérios verificáveis de qualidade

| Critério | Aceite esperado |
|---|---|
| Consistência | Mesmos tokens e componentes para botões, campos, avisos, cards e navegação; sem estilos locais contraditórios ou links repetidos substituindo estrutura. |
| Hierarquia | Título e finalidade claros, ação principal identificável e ações destrutivas diferenciadas; rótulos descrevem o efeito da ação. |
| Responsividade | Conferir larguras 320, 390, 768 e 1440 CSS px; sem perda de conteúdo/ações ou rolagem horizontal da página. Tabela genuinamente bidimensional pode usar região própria com acesso por teclado. |
| Ampliação | Texto ampliado a 200% permanece utilizável; verificar também redistribuição a 320 CSS px. Não alegar que zoom 200% sozinho comprova reflow. |
| Contraste | Texto comum pelo menos 4,5:1; texto grande pelo menos 3:1. Estados não dependem só de cor e são identificáveis por texto/ícone acessível. |
| Toque | Ações principais com alvo de pelo menos 44×44 CSS px, meta do projeto; outros controles respeitam 24×24 ou as exceções/espaçamentos da WCAG. Não confundir os dois critérios. |
| Teclado | Ordem coerente, foco visível, rótulos associados, link para conteúdo; menus e diálogos fecham adequadamente e devolvem foco, sem aprisionamento indevido. |
| Formulários | Obrigatoriedade e erros ligados ao campo; resumo de erro quando necessário; erro de rede preserva edição e não comunica gravação sem confirmação. |
| Estados | Carregamento, vazio, sucesso, falha, falta de permissão e conflito são distinguíveis; ações duplicadas não surgem por interação repetida. |
| Privacidade | Detalhes de saúde restritos ao fluxo autorizado; nomes de exemplo nas capturas. Logout/inativação não deixam conteúdo protegido exposto por navegação. |
| Conteúdo | Português consistente, sem IDs técnicos como título principal e sem indicadores ou funcionalidades simulados apresentados como reais. |
| Evidência visual | Capturas reais antes/depois, viewport, rota, perfil e cenário documentados; verificação em navegador com fixtures. Testes de DOM e imagens geradas não substituem inspeção do aplicativo. |

Critérios selecionados com referência à WCAG 2.2; não constituem declaração de
conformidade integral, certificação ou exigência jurídica externa para o projeto.
Fontes: [contraste](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html),
[reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) e
[alvos](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum.html).

## Execução e manutenção

UX-01 a UX-09 estão no [manifesto](../prompts/README.md). Executar um cartão por
vez, começando por UX-01. Esta evolução pode preceder os demais módulos pós-MVP;
não depende de Docker, biometria, pagamentos ou contratação de ferramenta visual.
Cada novo módulo posteriormente entregue aplica os mesmos componentes e critérios.
UX-09 verifica o conjunto atual; módulos posteriores ainda exigem seus próprios
testes e revisão visual. A validação final do projeto considera esse acabamento.

[Plano de testes](../testes/reformulacao-visual.md). Consulte os
[protótipos e a linha de base de UX-01](../testes/ux01-referencia-visual.md).
Atualizações entram nesta fonte, nos cartões afetados e no SPEC gerado,
preservando RF/RN/MRF e o MER.
