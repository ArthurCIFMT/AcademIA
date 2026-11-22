/* Navegação e conteúdo de demonstração. Todos os dados abaixo são fixos e sintéticos. */
const areas = {
  cliente: { nome: "Cliente", inicio: "treinos", itens: [
    ["treinos", "Meus treinos"], ["duvidas", "Assistente"], ["onboarding", "Meus dados de treino"], ["equipamentos", "Equipamentos"],
  ] },
  instrutor: { nome: "Instrutor", inicio: "meus-clientes", itens: [
    ["meus-clientes", "Meus clientes"], ["revisoes", "Revisões pendentes"], ["exercicios-instrutor", "Exercícios"],
  ] },
  administracao: { nome: "Administração", inicio: "clientes", itens: [
    ["clientes", "Clientes"], ["funcionarios", "Funcionários"], ["designacoes", "Designações"],
    ["inventario", "Equipamentos"], ["exercicios-admin", "Exercícios"],
  ] },
  atendimento: { nome: "Atendimento", inicio: "atendimento", itens: [["atendimento", "Clientes e convites"]] },
};

const link = (target, label, variant = "button") => `<a class="${variant}" href="#${target}">${label}</a>`;
const header = (tag, title, description) => `<div class="page-head">
  <p class="eyebrow">${tag}</p><h1 id="titulo" tabindex="-1">${title}</h1><p>${description}</p></div>`;
const notice = (type, title, description) => `<aside class="notice ${type}"><strong>${title}</strong><p>${description}</p></aside>`;
const tablist = (label, items, selected, css = "tabs") => `<nav class="${css}" aria-label="${label}">
  ${items.map(([id, name]) => `<a href="#${id}" ${id === selected ? 'aria-current="page"' : ""}>${name}</a>`).join("")}
</nav>`;

const day = () => `<dl>
  <div class="exercise"><dt>Agachamento livre</dt><dd>2 × 10 · 60 s<br>Sem equipamento</dd></div>
  <div class="exercise"><dt>Remada com halteres</dt><dd>2 × 10 · 60 s<br>Halteres</dd></div>
  <div class="exercise"><dt>Elevação de panturrilha</dt><dd>2 × 12 · 45 s<br>Sem equipamento</dd></div>
</dl>`;

function training(previous = false) {
  const title = previous ? "Histórico de fichas" : "Meus treinos";
  return header("Meu treino", title, previous
    ? "Consulte as versões retidas e os pareceres associados."
    : "Consulte sua ficha vigente e o parecer do instrutor.") + `
  <section class="hero"><p class="eyebrow">${previous ? "Versão anterior · Ficha 01" : "Ficha vigente · Versão 02"}</p>
    <h2>Treino de força</h2><p>Prescrição de exemplo organizada por dia.</p>
    ${link(previous ? "treinos" : "historico", previous ? "Voltar à ficha vigente" : "Consultar histórico")}
  </section>
  <div class="stack columns">
    <section class="card"><div class="panel-head"><div class="stack"><h2>Dia 1</h2><p class="subtle">Força geral</p></div><span class="pill">3 exercícios</span></div>
      ${day()}
    </section>
    <section class="card"><h2>Parecer do instrutor</h2>
      <span class="pill warn">${previous ? "Rejeitado" : "Pendente"}</span>
      <p>${previous ? "O conteúdo desta versão retida permanece consultável." : "A ficha já está disponível. O instrutor pode avaliá-la depois."}</p>
      ${link("duvidas", "Abrir assistente", "text-link")}
    </section>
  </div>`;
}

const stepLinks = [
  ["onboarding", "Objetivos e rotina"], ["fisico", "Dados físicos"], ["saude", "Saúde"], ["confirmacao", "Revisão"],
];
const inviteSteps = [["convite", "Objetivos e rotina"], ...stepLinks.slice(1).map(([id, name]) => ["convite-" + id, name])];
const selectField = (label, text) => `<label class="field">${label}<select><option>${text}</option></select></label>`;

function onboarding(id, invited = false) {
  const steps = invited ? inviteSteps : stepLinks;
  const index = steps.findIndex(([step]) => step === id);
  const step = steps[index][1];
  const fields = [
    `<div class="form-grid">${selectField("Objetivo principal", "Força")}${selectField("Experiência", "Iniciante")}
      ${selectField("Nível de atividade", "Leve")}${selectField("Dias por semana", "3")}${selectField("Duração da sessão", "45 minutos")}</div>`,
    `<div class="form-grid"><label class="field">Altura (cm)<input type="number" value="172"></label>
      <label class="field">Peso (kg)<input type="number" value="74"></label></div>
      <p class="subtle">Na conclusão, a idade é calculada a partir do cadastro.</p>`,
    `<div class="form-grid">${selectField("Condições de saúde", "Não")}${selectField("Uso de medicamentos", "Não sei")}
      ${selectField("Dor, lesão ou limitação", "Não")}${selectField("Restrição de exercício declarada", "Não")}
      ${selectField("Evento de saúde recente", "Não")}</div>
      <label class="field">Observações<textarea rows="2"></textarea></label>
      <p class="subtle">Respostas “Não sei” continuam explícitas na triagem.</p>`,
    `<div class="record"><strong>Objetivos e rotina</strong><p>Força · Iniciante · 3 dias por semana</p></div>
     <div class="record"><strong>Dados físicos</strong><p>172 cm · 74 kg</p></div>
     <div class="record"><strong>Saúde</strong><p>Uso de medicamentos: Não sei</p></div>
     ${notice("info", "Confirmação da versão", "A ação de concluir ou confirmar grava uma versão no aplicativo. A idade é preenchida nessa etapa.")}`,
  ];
  return header(invited ? "Convite" : "Meu treino", invited ? "Preencher onboarding" : "Meus dados de treino",
    "Informe sua rotina, seus dados físicos e suas respostas de saúde.") +
    tablist("Etapas do formulário", steps, id, "steps") +
    `<div class="columns"><section class="card"><h2>${step}</h2>${fields[index]}
      <div class="actions">${index > 0 ? link(steps[index - 1][0], "Voltar", "button secondary") : ""}
      ${index < 3 ? link(steps[index + 1][0], "Continuar") : link(invited ? "convite-concluido" : "onboarding-concluido", "Ver conclusão de exemplo")}</div>
    </section><aside class="card"><h2>Seu rascunho</h2><p>No aplicativo, você pode salvar e retomar o que já preencheu.</p>
      ${link(invited ? "convite-rascunho" : "rascunho", "Ver estado salvo", "text-link")}</aside></div>`;
}

const assistModes = [["duvidas", "Tirar dúvida"], ["gerar", "Gerar ficha"], ["adaptar", "Adaptar um dia"]];
function assistant(id) {
  const examples = {
    evidencia: ["warn", "Evidência insuficiente", "As fontes consultadas não sustentaram uma resposta para esta pergunta."],
    quota: ["warn", "Limite do provedor atingido", "Aguarde antes de preparar outra solicitação. Você ainda pode consultar a ficha atual."],
    bloqueio: ["danger", "Geração bloqueada pela triagem", "Confira os dados do onboarding. A ficha anterior continua disponível."],
    dados: ["warn", "Onboarding precisa de conferência", "Complete ou revise os dados para preparar outra solicitação."],
    falha: ["danger", "Falha do serviço", "Consulte o estado salvo antes de uma nova tentativa."],
  };
  const mode = id === "resposta" || id === "evidencia" ? "duvidas" : Object.hasOwn(examples, id) ? "gerar" : id;
  let content;
  if (mode === "duvidas") content = `<section class="card"><h2>Dúvidas sobre exercícios</h2>
    <label class="field">Sua pergunta<textarea rows="3">A atividade aeróbica precisa ser igual todos os dias?</textarea></label>
    ${link("resposta", "Ver resposta de exemplo")}${id === "resposta" ? `
      <article class="record"><h3>Resposta do assistente</h3><p>O guia apresenta recomendações semanais. A distribuição pelos dias pode variar.</p>
      <p><strong>Fonte:</strong> Guia de Atividade Física para a População Brasileira · p. 24–25</p></article>` : ""}</section>`;
  else if (mode === "adaptar") content = `<section class="card"><h2>Adaptar um dia da ficha</h2>
    ${selectField("Dia a revisar", "Dia 1")}${link("onboarding", "Conferir meu onboarding", "text-link")}
    <label><input type="checkbox" class="inline-check"> Conferi os dados relevantes para a adaptação.</label>
    <label class="field">Motivo da adaptação<textarea rows="2"></textarea></label></section>`;
  else content = `<section class="card"><h2>Gerar uma ficha</h2>
    <p>A solicitação usa o onboarding concluído e os exercícios disponíveis na academia.</p>
    ${link("onboarding", "Conferir meus dados", "text-link")}${link("quota", "Ver exemplo de solicitação salva")}</section>`;
  return header("Assistente", "Assistente de treino", "Escolha entre perguntar sobre atividade física, gerar uma ficha ou adaptar um dia da ficha vigente.") +
    tablist("Ações do assistente", assistModes, mode) + `<div class="columns"><div class="stack">
    ${examples[id] ? notice(...examples[id]) : ""}${content}</div>
    <aside class="card"><h2>Estados de exemplo</h2>${Object.entries(examples).map(([key, [, name]]) => link(key, name, "text-link")).join("")}</aside></div>`;
}

const catalogItems = {
  equipamentos: ["Equipamentos disponíveis", "Halteres", "Banco regulável"],
  inventario: ["Equipamentos", "Halteres · Operacional", "Banco regulável · Operacional"],
  funcionarios: ["Funcionários", "Instrutor de exemplo · Ativo", "Atendente de exemplo · Ativo"],
  designacoes: ["Designações", "Cliente de exemplo", "Instrutor de exemplo · Responsável atual"],
  "exercicios-admin": ["Exercícios", "Agachamento livre · Sem equipamento", "Remada · Halteres"],
  "exercicios-instrutor": ["Exercícios", "Agachamento livre · Sem equipamento", "Remada · Halteres"],
};

function directory(id) {
  const admin = id === "clientes";
  const detail = id === "cadastro";
  return header(admin || detail ? "Administração" : "Atendimento", detail ? "Cadastro de cliente" : "Clientes",
    detail ? "Dados cadastrais e situação do convite." : "Consulte cadastros, perfis e convites de primeiro acesso.") + `
    <section class="card"><div class="panel-head"><h2>${detail ? "Cliente de exemplo" : "Cadastros"}</h2><span class="pill">Perfil ativo</span></div>
    ${detail ? `<p>Idade atual · 32 anos</p><p>cliente@example.test</p><p>Convite enviado à caixa de teste.</p>
      ${link("clientes", "Voltar à lista", "text-link")}` : `
      <label class="field">Nome ou e-mail<input type="search" placeholder="Buscar no cadastro"></label>
      <div class="record"><strong>Cliente de exemplo</strong><p>32 anos · cliente@example.test</p>
      ${link(admin ? "cadastro" : "convite", admin ? "Consultar cadastro de exemplo" : "Ver formulário por convite", "button secondary")}</div>`}
    </section>`;
}

function instructor(id) {
  const titles = { "meus-clientes": "Meus clientes", revisoes: "Revisões pendentes", editor: "Preparar ficha manual", parecer: "Revisar ficha publicada", avaliacao: "Avaliação do cliente" };
  const heading = header("Instrutor", titles[id], "Acompanhe o cliente sob sua designação.");
  if (id === "editor") return heading + `<section class="card"><h2>Cliente de exemplo</h2><span class="pill">Rascunho manual</span>
    <div class="form-grid"><label class="field">Título do dia<input value="Dia 1"></label>${selectField("Exercício", "Agachamento livre")}</div>
    ${day()}${link("parecer", "Ver versão publicada de exemplo")}</section>`;
  if (id === "parecer") return heading + `<div class="columns"><section class="card"><h2>Ficha 02 · Cliente de exemplo</h2>
    <span class="pill">Ficha vigente</span>${day()}</section><section class="card"><h2>Parecer</h2>
    <span class="pill warn">Pendente</span><p>Registre sua decisão para esta versão. O cliente já pode consultar a ficha.</p>
    <label class="field">Decisão<select><option>Aceitar</option><option>Rejeitar</option></select></label>
    <label class="field">Motivo do parecer<textarea rows="2"></textarea></label>
    ${link("revisoes", "Voltar à fila", "text-link")}</section></div>`;
  if (id === "avaliacao") return heading + `<section class="card"><h2>Onboarding concluído · Versão 1</h2>
    <label class="field">Observação da avaliação<textarea rows="3"></textarea></label>
    ${link("meus-clientes", "Voltar para meus clientes", "text-link")}</section>`;
  return heading + `<section class="card"><h2>Cliente de exemplo</h2>
    <p>${id === "revisoes" ? "Ficha 02 · Parecer pendente" : "Designação vigente · Onboarding concluído"}</p>
    <div class="actions">${link(id === "revisoes" ? "parecer" : "editor", id === "revisoes" ? "Abrir ficha 02" : "Abrir fichas")}
    ${id === "meus-clientes" ? link("avaliacao", "Consultar avaliação", "button secondary") : ""}</div></section>`;
}

const pages = Object.create(null);
const register = (role, nav, ids, render) => {
  ids.forEach(id => { pages[id] = { role, nav, render }; });
};
register("cliente", "treinos", ["treinos", "historico"], id => training(id === "historico"));
register("cliente", "onboarding", stepLinks.map(([step]) => step), onboarding);
register("cliente", "onboarding", ["rascunho", "onboarding-concluido"], id =>
  header("Meu treino", "Meus dados de treino", "Consulte o estado do seu onboarding.") +
  `<section class="card"><h2>${id === "rascunho" ? "Rascunho salvo" : "Versão concluída"}</h2>
  <p>${id === "rascunho" ? "Exemplo de rascunho disponível para retomar." : "Idade na conclusão · 32 anos"}</p>
  ${link("onboarding", id === "rascunho" ? "Retomar formulário" : "Ver atualização do formulário")}</section>`);
register("cliente", "duvidas", ["duvidas", "resposta", "gerar", "adaptar", "evidencia", "quota", "bloqueio", "dados", "falha"], assistant);
register("administracao", "clientes", ["clientes", "cadastro"], directory);
register("atendimento", "atendimento", ["atendimento"], directory);
register("instrutor", "meus-clientes", ["meus-clientes", "editor", "avaliacao"], instructor);
register("instrutor", "revisoes", ["revisoes", "parecer"], instructor);
for (const [id, [title, ...items]] of Object.entries(catalogItems)) register(
  id === "equipamentos" ? "cliente" : id.endsWith("instrutor") ? "instrutor" : "administracao",
  id, [id], () => header("Catálogo e cadastros", title, "Lista de exemplo.") +
  `<section class="card"><h2>${title}</h2>${items.map(item => `<p class="record">${item}</p>`).join("")}</section>`,
);
register(null, null, inviteSteps.map(([step]) => step), id => onboarding(id, true));
register(null, null, ["convite-rascunho"], () => header("Convite", "Rascunho salvo", "Retome o formulário pelo convite ainda válido.") + link("convite", "Retomar formulário"));
register(null, null, ["convite-concluido"], () => header("Convite", "Onboarding concluído", "Abra sua conta para consultar os dados registrados.") + link("login", "Voltar ao acesso"));
register(null, null, ["login"], () => `<div class="login-layout">
  <section class="hero"><p class="eyebrow">AcademIA</p><h1 id="titulo" tabindex="-1">Seus treinos em um só lugar</h1>
    <p>Entre para consultar sua ficha e conversar com o assistente.</p></section>
  <section class="card"><h2>Entrar</h2>
    <label class="field">E-mail<input type="email" placeholder="cliente@example.test"></label>
    <label class="field">Senha<input type="password" autocomplete="off"></label>
    ${link("treinos", "Abrir área de exemplo")}${link("convite", "Ver formulário por convite", "text-link")}
  </section></div>`);

const app = document.getElementById("app");
function render(moveFocus = false) {
  const id = location.hash.slice(1);
  const page = pages[id] ?? pages.treinos;
  const role = page.role && areas[page.role];
  const top = `<header class="site-header"><a class="brand" href="#login"><span class="mark" aria-hidden="true">A</span>AcademIA</a>
    <div class="header-tools"><span class="prototype">Protótipo · Dados sintéticos</span>
    ${role ? `<div class="role-picker"><label for="perfil">Área</label><select id="perfil">${Object.entries(areas).map(([name, area]) =>
      `<option value="${area.inicio}" ${name === page.role ? "selected" : ""}>${area.nome}</option>`).join("")}</select></div>` : ""}
    </div></header>`;
  const menu = role ? `<nav aria-label="Menu de ${role.nome}"><ul class="nav">${role.itens.map(([item, name]) =>
      `<li><a href="#${item}" ${page.nav === item ? 'aria-current="location"' : ""}>${name}</a></li>`).join("")}
      <li>${link("login", "Sair da demonstração", "text-link")}</li></ul></nav>` : "";
  const current = role?.itens.find(([id]) => id === page.nav)?.[1];
  const sidebar = role ? `<aside class="sidebar">
    <div class="desktop-menu"><p class="eyebrow">${role.nome}</p>${menu}</div>
    <details class="mobile-menu"><summary>Menu <span>· ${current}</span></summary>${menu}</details>
  </aside>` : "";
  app.innerHTML = top + `<div ${role ? 'class="layout"' : ""}>${sidebar}
    <main class="content" id="conteudo" tabindex="-1" data-view="${pages[id] ? id : "treinos"}">${page.render(pages[id] ? id : "treinos")}</main></div>`;
  document.getElementById("perfil")?.addEventListener("change", event => { location.hash = event.target.value; });
  if (moveFocus) document.getElementById("titulo").focus();
}
window.addEventListener("hashchange", () => render(true));
document.querySelector(".skip").addEventListener("click", event => {
  event.preventDefault();
  document.getElementById("conteudo").focus();
});
render();
