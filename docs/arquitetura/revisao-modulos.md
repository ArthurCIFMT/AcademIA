# Revisão da cobertura dos módulos

## Resultado

Os 13 módulos MOD-00 a MOD-12 são suficientes para o escopo atual do AcademIA.
A revisão considera RF-01–RF-37, RN-01–RN-39, RNF-01–RNF-17 e MRF01–MRF19
com 110 critérios. Agentic RAG foi autorizado funcionalmente; políticas clínicas,
provedores/parâmetros e reservas condicionais continuam nas decisões pertinentes.
Cobertura de planejamento não é evidência de implementação.

## Cobertura e refinamentos

| Módulo | Cobertura principal | Refinamento necessário |
|---|---|---|
| MOD-00 | Configuração, arquitetura, contratos, testes, infraestrutura | Incluir adapter de arquivos; testes e ambiente local precedem Docker |
| MOD-01 | RF-01–RF-08, identidades, clientes e funcionários | Bootstrap do administrador e primeiro acesso sem duplicar identidade |
| MOD-02 | RF-34 e colaboração na revisão | Somente designação e responsabilidade vigente/histórica |
| MOD-03 | RF-09–RF-14, RN-21 e MRF03 | Convite, avaliação e snapshot; não limitar evolução a um formulário mutável |
| MOD-04 | RF-16/RF-17/RF-35, catálogo e ficha manual | Dono da publicação, versão e parecer posterior; consulta/chat independem de aceite |
| MOD-05 | MRF01/MRF02, evidências e ferramentas de conhecimento | Aprovação, reindexação e recuperação/contexto verificáveis para pesquisa agentiva |
| MOD-06 | RF-15/RF-18/RF-19, MRF16–MRF19 | Planejamento/pesquisa, executor/orçamento, suficiência, triagem, geração/chat e publicação por MOD-04 |
| MOD-07 | RF-20–RF-25/RF-36/RF-37 e RN-06–RN-10/RN-35/RN-36 | API facial real; decisão separada e passagem em catraca fictícia |
| MOD-08 | RF-26/RF-27/RF-31 | Matrícula pelo atendente sem pagamento obrigatório; financeiro tardio |
| MOD-09 | RF-30 e RN-25 condicional | Aula e ocorrência; reserva só após aceite do requisito complementar |
| MOD-10 | RF-32/RF-33 e RN-37 | MVP: cadastro administrativo e disponibilidade obrigatória na seleção/validação de novas prescrições |
| MOD-11 | RF-28/RF-29 | Indicadores por contratos; financeiro disponível depois, sem cálculo de lucro |
| MOD-12 | RN-23/RN-26/RN-27 e suporte aos fluxos | Aviso/auditoria desde cedo; não possuir as fichas nem todas as exportações |

Não é necessário criar módulos autônomos para cada agente, formato de arquivo,
tabela ou mecanismo de segurança. Subcomponentes cabem nas responsabilidades acima.

## Lacunas operacionais identificadas e correções documentais

### Bootstrap e primeiro acesso

IAM-02 precisa explicar como a instalação vazia ganha seu primeiro administrador.
PES-01/PES-02 precisam fechar o vínculo entre cadastro e credencial/convite inicial.
O mecanismo depende de GATE-02; não se presume senha temporária fixa nem conta
duplicada. Esses itens são refinamentos para tornar RF-01/RF-04/RF-07 executáveis,
e não funcionalidades comerciais adicionais.

### Atualidade do contexto antes da publicação

Uma proposta pode estar correta para o snapshot usado e ficar desatualizada quando
o onboarding muda. TRN-03/AI-04 devem verificar versão-base e restrições antes de
publicar; o parecer posterior identifica a versão e o instrutor designado.
O tratamento exato de alteração relevante é uma política
a definir; simples igualdade do JSON não é critério clínico.
Não se presume suspensão automática da ficha já ativa por qualquer edição cadastral.

### Dependência da interface de notificações

NTF-01 inclui frontend e exige sessão, mas originalmente só dependia de FND-08 e
IAM-02. Acrescentar IAM-04 fecha a dependência sem introduzir ciclo.

### Grafo e ownership

MOD-12 é transversal e começa em FND-08/NTF-01. Não deve aparecer no grafo como
dependente da conclusão de todos os módulos. A fonte das decisões é:
MOD-02 para designação, MOD-03 para avaliação, MOD-04 para publicação/parecer, MOD-05 para
corpus, MOD-06 para execução da IA e MOD-12 para entrega do aviso/auditoria.
Exportação autorizada permanece no módulo dono do recurso.

## MVP e fases

O MVP proposto é amplo, mas coerente com a IA como objetivo acadêmico central.
Seus marcos são fundação → identidade/designação → onboarding → treino manual →
RAG/geração → publicação e chat → parecer posterior e aceite E2E. Esta revisão não retirou
chat nem qualquer requisito do MVP silenciosamente.

Equipamentos pertencem ao MVP. Matrícula/catraca, aulas e dashboard são extensões planejadas.
Pagamento automático continua tardio e Docker depende de MVP e maioria dos módulos.
Reserva, multiacademia e sessão executada de treino exigem escopo confirmado.

## Melhorias propostas, sem inclusão automática

- Registrar sessão executada/repetições realizadas, além da ficha prescrita.
- Expandir relatórios ou regras financeiras além do controle básico.
- Introduzir múltiplos instrutores principais ou escala de substituição.

Essas opções podem ser úteis, mas não são pré-condições para o núcleo pedido.
A próxima modelagem deve priorizar dados necessários a designação, avaliação,
proposta, revisão e RAG antes de criar migrations.

A revisão posterior incorporou as correções do responsável em
[fluxos atualizados](fluxos-atualizados.md), sem criar módulos adicionais.
Foram acrescentados os cartões MEM-00 (registro financeiro opcional e tardio) e
ACS-07 (catraca fictícia). MEM-01 não depende de MEM-00 nem de pagamento.

## Decisões adicionais incorporadas

Equipamentos no MVP e restrição ao gerador foram confirmados pelo responsável;
EQP-01 precede TRN-01/AI-01 e TST-01. Retenção de 15 versões publicadas completas
pertence a MOD-04 (RF-17/RN-38), sem novo módulo. Saída em português com fontes
estrangeiras permitidas pertence a MOD-05/MOD-06/MOD-04 (RN-39).
