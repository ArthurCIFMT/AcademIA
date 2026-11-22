/* Capturas e verificações locais, usando Playwright já instalado no frontend. */
const assert = require("node:assert/strict");
const http = require("node:http");
const fs = require("node:fs/promises");
const path = require("node:path");
const { once } = require("node:events");

const root = path.resolve(__dirname, "../..");
const { chromium } = require(path.join(root, "frontend/node_modules/playwright"));
const [dist, output] = process.argv.slice(2).map(value => path.resolve(value));
const proto = path.join(__dirname, "prototipo");
const time = "2026-11-11T12:00:00Z";
const requestId = "11111111-1111-4111-8111-111111111111";
const person = { id: "cliente", nome: "Cliente de exemplo", email: "cliente@example.test",
  idade: 32, ativo: true, estado_conta: "ATIVO", revisao: 1 };
const form = { altura_cm: 172, peso_kg: 74, objetivo_principal: "FORCA",
  experiencia: "INICIANTE", nivel_atividade: "LEVE", dias_semana: 3, duracao_sessao_min: 45,
  possui_condicoes_saude: "NAO", condicoes_saude: [], usa_medicamentos: "NAO_SEI",
  medicamentos: [], possui_dor_lesao_limitacao: "NAO", limitacoes: [],
  restricao_exercicio_declarada: "NAO", evento_saude_importante_recente: "NAO", observacoes: "" };
const meta = { id: "ficha", numero: 2, origem: "MANUAL", autor_id: "instrutor",
  onboarding_id: "onboarding", revisao: 1, estado_publicacao: "PUBLICADO", vigente: true,
  motivo_exclusao: null, publicada_em: time, parecer_estado: "PENDENTE" };
const movements = ["Agachamento livre", "Remada com halteres", "Elevação de panturrilha"];
const workout = {
  ficha: { ...meta, dias: [{ titulo: "Dia 1", itens: movements.map((nome, index) => ({
    series: 2, repeticoes: index === 2 ? "12" : "10", carga_kg: null, cadencia: null,
    intervalo_segundos: index === 2 ? 45 : 60, observacoes: null,
    exercicio_id: "exercicio-" + index, equipamento_ids: index === 1 ? ["haltere"] : [],
    exercicio_snapshot: { nome, descricao: "Exercício de exemplo", grupo_muscular: "Força geral", dispensa_equipamento: index !== 1 },
  })) }] },
  parecer: { id: null, estado: "PENDENTE", motivo: null, instrutor_id: null, criado_em: null },
  equipamentos: [{ id: "haltere", nome: "Halteres", disponivel: true }],
  validacao: null, schema_version: 1, consultado_em: time,
};
const paginate = itens => ({ itens, pagina: 1, limite: 20, total: itens.length });
const fixtures = {
  "/api/v1/onboarding/meu": { rascunho: { id: "rascunho", numero: 1, revisao: 1, dados: form }, concluido: null },
  "/api/v1/ia/chat": [{ solicitacao_id: requestId, criada_em: time, finalidade: "DUVIDA",
    pergunta: "A atividade aeróbica precisa ser igual todos os dias?", estado: "ABSTENCAO",
    motivo: "RESPOSTA_VALIDADA", resposta: null, fontes: [], versao_publicada_id: null }],
  ["/api/v1/ia/fichas/execucoes/" + requestId + "/acompanhamento"]: {
    execucao: { solicitacao_id: requestId, estado: "FALHA", motivo: "QUOTA_EXCEDIDA", versao_publicada_id: null }, geracao: null,
  },
  "/api/v1/treinos/clientes/cliente/publicadas": { schema_version: 1, versao_vigente_id: "ficha", itens: [meta] },
  "/api/v1/treinos/clientes/cliente/publicadas/ficha/ficha": workout,
  "/api/v1/treinos/clientes/cliente/contexto": { cliente_nome: person.nome },
  "/api/v1/treinos/clientes/cliente/versoes/ficha/revisao": workout,
  "/api/v1/clientes": paginate([person]),
};
const cases = [
  ["entrada", "/login", [], "E-mail", "login"],
  ["onboarding", "/area/cliente/onboarding", ["CLIENTE"], "Altura", "fisico"],
  ["duvida", "/area/cliente/assistente", ["CLIENTE"], "As fontes consultadas não sustentaram", "evidencia"],
  ["quota", "/area/cliente/treino-ia?solicitacao=" + requestId, ["CLIENTE"], "O limite de uso da IA gratuita", "quota"],
  ["ficha", "/area/cliente/treinos", ["CLIENTE"], movements[2], "treinos"],
  ["parecer", "/area/instrutor/clientes/cliente/treinos/ficha/revisao", ["INSTRUTOR"], movements[2], "parecer"],
  ["cadastro", "/area/administracao/clientes", ["ADMINISTRADOR", "ATENDENTE"], person.email, "clientes"],
];

const type = { ".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8" };
const server = http.createServer(async (request, response) => {
  try {
    const url = new URL(request.url, "http://127.0.0.1");
    const isPrototype = url.pathname.startsWith("/prototipo/");
    const base = isPrototype ? proto : dist;
    const prefix = isPrototype ? "/prototipo/" : "/";
    const file = path.resolve(base, path.extname(url.pathname) ? url.pathname.slice(prefix.length) : "index.html");
    if (!file.startsWith(base + path.sep)) return response.writeHead(404).end();
    const body = await fs.readFile(file);
    response.writeHead(200, {
      "Content-Type": type[path.extname(file)] ?? "application/octet-stream",
      "Content-Security-Policy": "default-src 'self'; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'",
    }).end(body);
  } catch {
    response.writeHead(404).end();
  }
});

async function capture(browser, origin, width, stage, sample) {
  const [name, route, roles, expected, example] = sample;
  const page = await browser.newPage({ viewport: { width, height: width === 390 ? 844 : 1000 }, deviceScaleFactor: 1 });
  const unexpected = [];
  page.on("pageerror", error => unexpected.push(error.message));
  await page.route("**/*", async request => {
    const url = new URL(request.request().url());
    if (url.origin !== origin) {
      // Este Windows pode inserir uma URL do antivírus no HTML servido.
      // Qualquer tentativa externa é bloqueada; só as do aplicativo falham o teste.
      if (url.hostname !== "me.kis.v2.scr.kaspersky-labs.com") unexpected.push(url.origin);
      return request.abort();
    }
    if (!url.pathname.startsWith("/api/")) return request.continue();
    if (stage !== "antes") {
      unexpected.push(url.pathname);
      return request.abort();
    }
    if (url.pathname === "/api/v1/auth/session") return roles.length
      ? request.fulfill({ json: { user_id: "cliente", roles, csrf_token: "sintetico", expires_at: "2099-01-01T00:00:00Z" } })
      : request.fulfill({ status: 401, json: {} });
    if (Object.hasOwn(fixtures, url.pathname)) return request.fulfill({ json: fixtures[url.pathname] });
    unexpected.push(url.pathname);
    return request.fulfill({ status: 404, json: {} });
  });
  try {
    await page.goto(origin + (stage === "antes" ? route : "/prototipo/#" + example));
    if (stage === "antes") {
      const marker = name === "entrada" ? page.getByLabel(expected, { exact: true }) : name === "onboarding"
        ? page.getByLabel(/Altura/) : page.getByText(expected).first();
      await marker.waitFor({ timeout: 8000 });
      // A faixa marca a própria captura da UI atual, sem mudar o arquivo do aplicativo.
      await page.evaluate(() => {
        const label = document.createElement("p");
        label.textContent = "Linha de base do MVP · Dados sintéticos";
        label.style.cssText = "padding:.5rem 1rem;margin:0;background:#142c30;color:white;font:14px system-ui";
        document.body.prepend(label);
      });
    } else await page.getByRole("heading", { level: 1 }).waitFor({ timeout: 8000 });
    assert.deepEqual(unexpected, [], `Requisição ou erro inesperado em ${stage}/${name}`);
    await page.screenshot({ path: path.join(output, stage, name + "-" + width + ".png"), fullPage: true });
  } finally {
    await page.close();
  }
}

function luminance(color) {
  const channels = color.match(/[0-9a-f]{2}/gi).map(value => parseInt(value, 16) / 255);
  return channels.map(x => x <= .04045 ? x / 12.92 : ((x + .055) / 1.055) ** 2.4)
    .reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
}

async function inspectPrototype(browser, origin) {
  const page = await browser.newPage();
  const base = origin + "/prototipo/";
  const widths = [320, 390, 768, 1440];
  try {
    await page.goto(base);
    const visited = new Set();
    const checks = [];
    for (const width of widths) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(base + "#treinos");
      const pages = width === 320 ? ["treinos"] : [...visited];
      for (const id of pages) {
        if (width === 320 && visited.has(id)) continue;
        await page.goto(base + "#" + id);
        await page.waitForFunction(expected => document.querySelector("main")?.dataset.view === expected, id, { timeout: 3000 });
        const data = await page.evaluate(() => ({
          width: document.documentElement.scrollWidth,
          title: document.querySelector("h1").textContent,
          links: [...document.querySelectorAll("a[href^='#'], #perfil option")].map(element =>
            element.tagName === "A" ? element.hash.slice(1) : element.value).filter(value => value && value !== "conteudo"),
          actions: [...document.querySelectorAll(".button")].map(element => element.getBoundingClientRect().height),
        }));
        assert.ok(data.width <= width, `Overflow em ${id} a ${width}px`);
        assert.ok(data.actions.every(height => height >= 44), `Alvo pequeno em ${id}`);
        if (width === 320) {
          assert.ok(id === "treinos" || data.title !== "Meus treinos", `Link não resolvido: ${id}`);
          visited.add(id);
          for (const target of data.links) if (!visited.has(target) && !pages.includes(target)) pages.push(target);
        }
      }
      checks.push({ largura_px: width, telas: visited.size });
    }
    await page.setViewportSize({ width: 390, height: 844 });
    await page.goto(base + "?teclado=1");
    await page.keyboard.press("Tab");
    assert.equal(await page.locator(":focus").textContent(), "Ir para o conteúdo");
    await page.keyboard.press("Enter");
    assert.equal(await page.locator(":focus").getAttribute("id"), "conteudo");
    await page.locator(".mobile-menu summary").focus();
    await page.keyboard.press("Enter");
    assert.ok(await page.locator(".mobile-menu").evaluate(el => el.open));
    const assist = page.getByRole("navigation", { name: "Menu de Cliente" }).getByRole("link", { name: "Assistente" });
    await assist.focus();
    assert.equal(await assist.evaluate(el => getComputedStyle(el).outlineStyle), "solid");
    await page.keyboard.press("Enter");
    await page.waitForFunction(() => document.activeElement?.id === "titulo");
    assert.ok(!(await page.locator(".mobile-menu").evaluate(el => el.open)));
    await page.getByLabel("Área", { exact: true }).selectOption({ label: "Instrutor" });
    await page.getByRole("heading", { name: "Meus clientes", exact: true }).waitFor();
    await page.goto(base + "#convite");
    await page.getByRole("link", { name: "Continuar" }).click();
    await page.waitForURL("**/#convite-fisico");
    assert.equal(await page.locator(".sidebar").count(), 0);
    await page.evaluate(() => document.documentElement.style.fontSize = "200%");
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth));
    await page.getByRole("link", { name: "Continuar" }).focus();
    await page.keyboard.press("Enter");
    await page.waitForURL("**/#convite-saude");
    const pairs = [
      ["Texto e fundo", "--texto", "--fundo", 4.5], ["Texto secundário e fundo", "--secundario", "--fundo", 4.5],
      ["Branco no botão", "#ffffff", "--marca", 4.5], ["Branco na capa", "#ffffff", "#164e4d", 4.5],
      ["Texto de aviso", "--aviso-texto", "--aviso-fundo", 4.5], ["Texto de erro", "--erro-texto", "--erro-fundo", 4.5],
      ["Texto de informação", "--marca", "--marca-clara", 4.5], ["Borda de campo", "--controle", "#ffffff", 3],
      ["Foco na superfície", "--foco", "#ffffff", 3], ["Foco no fundo", "--foco", "--fundo", 3],
      ["Foco no ativo", "--foco", "--marca-clara", 3],
    ];
    const colors = await page.evaluate(values => {
      const css = getComputedStyle(document.documentElement);
      return values.map(([name, a, b, min]) => [name, ...[a, b].map(key => key.startsWith("--") ? css.getPropertyValue(key).trim() : key), min]);
    }, pairs);
    const contrast = colors.map(([par, a, b, minimo]) => {
      const levels = [luminance(a), luminance(b)].sort((x, y) => y - x);
      const ratio = (levels[0] + .05) / (levels[1] + .05);
      assert.ok(ratio >= minimo, `Contraste insuficiente: ${par}`);
      return { par, cores: [a, b], razao: Number(ratio.toFixed(2)), minimo };
    });
    return { telas_por_largura: checks, teclado: "OK", texto_200_pct: "390 px · passo físico do convite", contraste: contrast };
  } finally {
    await page.close();
  }
}

async function main() {
  assert.ok(dist && output, "Informe o build do MVP e uma pasta nova para as capturas.");
  await fs.mkdir(output);
  await Promise.all(["antes", "prototipo"].map(dir => fs.mkdir(path.join(output, dir))));
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const origin = "http://127.0.0.1:" + server.address().port;
  try {
    const browser = await chromium.launch({ channel: "msedge" });
    try {
      const observed = await inspectPrototype(browser, origin);
      for (const width of [390, 1440]) for (const sample of cases) for (const stage of ["antes", "prototipo"])
        await capture(browser, origin, width, stage, sample);
      const report = { navegador: "Microsoft Edge " + browser.version(), ...observed,
        capturas: { total: cases.length * 4, alturas_viewport_px: { 390: 844, 1440: 1000 },
          cenarios: cases.map(([arquivo, rota, papeis, , exemplo]) => ({ arquivo, rota, papeis, exemplo })) } };
      await fs.writeFile(path.join(output, "resultado.json"), JSON.stringify(report, null, 2) + "\n");
      console.log(JSON.stringify(report, null, 2));
    } finally {
      await browser.close();
    }
  } finally {
    server.close();
  }
}

if (require.main === module) {
  main().catch(error => { console.error(error); process.exitCode = 1; });
}

module.exports = { fixtures, cases };
