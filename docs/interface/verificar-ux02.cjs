/* Abre a SPA e o mostruário React com fixtures, sem iniciar backend ou LLM. */
const assert = require("node:assert/strict");
const fs = require("node:fs/promises");
const http = require("node:http");
const path = require("node:path");
const { once } = require("node:events");
const { pathToFileURL } = require("node:url");
const { fixtures, cases } = require("./verificar-ux01.cjs");

const frontend = path.resolve(__dirname, "../../frontend");
const deps = path.join(frontend, "node_modules");
const { chromium } = require(path.join(deps, "playwright"));
const [dist, output] = process.argv.slice(2).map(value => path.resolve(value));
const preview = "/src/ui/preview/index.html";
const widths = [320, 390, 768, 1440];
const mime = { ".html": "text/html", ".js": "text/javascript", ".css": "text/css" };
const samples = [...cases, ["atendimento", "/area/atendimento/clientes", ["ATENDENTE"], "cliente@example.test"]];
const actions = {
  entrada: "Entrar", onboarding: "Concluir onboarding", duvida: "Enviar dúvida",
  quota: "Consultar estado salvo", ficha: "Exportar ficha em JSON", parecer: "Registrar parecer",
  cadastro: "Cadastrar cliente", atendimento: "Cadastrar cliente",
};

async function build() {
  process.env.VITE_API_BASE_URL = "/api";
  process.env.VITE_CORPUS_MAINTENANCE_ENABLED = "false";
  const vite = await import(pathToFileURL(require.resolve("vite", { paths: [frontend] })).href);
  await vite.build({
    root: frontend, configFile: path.join(frontend, "vite.config.ts"),
    build: { outDir: dist, emptyOutDir: false, rollupOptions: {
      input: { app: path.join(frontend, "index.html"), preview: path.join(frontend, preview.slice(1)) },
    } },
  });
}

function serve() {
  return http.createServer(async (request, response) => {
    try {
      const { pathname } = new URL(request.url, "http://127.0.0.1");
      const file = path.resolve(dist, path.extname(pathname) ? pathname.slice(1) : "index.html");
      if (!file.startsWith(dist + path.sep)) return response.writeHead(404).end();
      const content = await fs.readFile(file);
      response.writeHead(200, {
        "Content-Type": (mime[path.extname(file)] ?? "application/octet-stream") + "; charset=utf-8",
        "Content-Security-Policy": "default-src 'self'; style-src 'self'; frame-ancestors 'none'",
      }).end(content);
    } catch {
      if (!response.headersSent) response.writeHead(404);
      response.end();
    }
  });
}

async function withPage(browser, origin, width, roles, inspect) {
  const page = await browser.newPage({ viewport: { width, height: width <= 390 ? 844 : 1000 },
    hasTouch: width <= 390, deviceScaleFactor: 1 });
  const unexpected = [];
  page.on("pageerror", error => unexpected.push(error.message));
  await page.route("**/*", async route => {
    const { pathname, origin: target, hostname } = new URL(route.request().url());
    if (target !== origin) {
      if (hostname !== "me.kis.v2.scr.kaspersky-labs.com") unexpected.push(target);
      return route.abort();
    }
    if (!pathname.startsWith("/api/")) return route.continue();
    if (roles === null || route.request().method() !== "GET") {
      unexpected.push(pathname);
      return route.abort();
    }
    if (pathname === "/api/v1/auth/session") return roles.length
      ? route.fulfill({ json: { user_id: "cliente", roles, csrf_token: "sintetico", expires_at: "2099-01-01T00:00:00Z" } })
      : route.fulfill({ status: 401, json: {} });
    if (Object.hasOwn(fixtures, pathname)) return route.fulfill({ json: fixtures[pathname] });
    unexpected.push(pathname);
    return route.fulfill({ status: 404, json: {} });
  });
  try {
    const result = await inspect(page);
    assert.deepEqual(unexpected, [], `Conexão ou erro inesperado: ${page.url()}`);
    return result;
  } finally {
    await page.close();
  }
}

async function assertReflow(page, width, scenario) {
  const metrics = await page.evaluate(() => ({
    scroll: document.documentElement.scrollWidth, viewport: innerWidth,
  }));
  assert.equal(metrics.viewport, width);
  assert.ok(metrics.scroll <= width, `Rolagem da página: ${scenario} (${width} → ${metrics.scroll} px)`);
}

async function capture(page, name, files) {
  await page.screenshot({ path: path.join(output, name), fullPage: true });
  files.push(name);
}

async function inspectApp(browser, origin, width, sample, files) {
  const [name, url, roles, marker] = sample;
  await withPage(browser, origin, width, roles, async page => {
    await page.goto(origin + url);
    if (name === "onboarding") {
      const physical = page.getByRole("button", { name: "Dados físicos", exact: true });
      const height = page.getByLabel("Altura (cm)", { exact: true });
      await physical.or(height).waitFor({ timeout: 8000 });
      if (await physical.isVisible()) {
        await physical.press("Enter");
        await height.waitFor();
        await assertReflow(page, width, "onboarding em edição");
        await page.getByRole("button", { name: "Revisão", exact: true }).press("Enter");
      }
    }
    const content = name === "entrada" ? page.getByLabel(marker, { exact: true }) : name === "onboarding"
      ? page.getByText("Altura (cm)", { exact: true }) : page.getByText(marker).first();
    await content.waitFor({ timeout: 8000 });
    const action = page.getByRole("button", { name: actions[name], exact: true });
    await action.waitFor({ timeout: 3000 });
    const bounds = await action.boundingBox();
    assert.ok(bounds.width >= 44 && bounds.height >= 44, `Alvo principal menor que 44 px em ${name}`);
    await assertReflow(page, width, name);
    if (name === "cadastro" || name === "atendimento") {
      await action.click();
      await page.getByLabel("Data de nascimento").waitFor();
      await page.getByRole("button", { name: "Salvar cadastro" }).waitFor();
      await assertReflow(page, width, name + " aberto");
    }
    if ((width === 390 && ["entrada", "cadastro", "onboarding"].includes(name))
      || (width === 1440 && name === "parecer")) await capture(page, name + "-" + width + ".png", files);
  });
}

async function checkContrast(page) {
  const pairs = [
    ["Texto principal", "h1", "color", "body", "backgroundColor", 4.5],
    ["Texto secundário", ".preview-header p", "color", "body", "backgroundColor", 4.5],
    ["Botão principal", "button[type=submit]", "color", "button[type=submit]", "backgroundColor", 4.5],
    ["Botão secundário", "[data-variant=secondary]", "color", "[data-variant=secondary]", "backgroundColor", 4.5],
    ["Campo", ".ac-field-control", "borderTopColor", ".ac-field-control", "backgroundColor", 3],
    ["Foco", ":focus-visible", "outlineColor", "body", "backgroundColor", 3],
    ["Desabilitado", "button:disabled", "color", "button:disabled", "backgroundColor", 4.5],
    ...["success", "conflict", "error"].map(state =>
      [state, `[data-state=${state}]`, "color", `[data-state=${state}]`, "backgroundColor", 4.5]),
  ];
  const colors = await page.evaluate(pairs => pairs.map(([name, first, firstProperty, second, secondProperty, minimum]) =>
    ({ par: name, cores: [getComputedStyle(document.querySelector(first))[firstProperty],
      getComputedStyle(document.querySelector(second))[secondProperty]], minimo: minimum })), pairs);
  const luminance = color => color.match(/\d+/g).slice(0, 3)
    .map(channel => Number(channel) / 255)
    .map(channel => channel <= .04045 ? channel / 12.92 : ((channel + .055) / 1.055) ** 2.4)
    .reduce((sum, value, index) => sum + value * [.2126, .7152, .0722][index], 0);
  return colors.map(pair => {
    const [high, low] = pair.cores.map(luminance).sort((a, b) => b - a);
    const ratio = (high + .05) / (low + .05);
    assert.ok(ratio >= pair.minimo, `Contraste insuficiente: ${pair.par}`);
    return { ...pair, razao: Number(ratio.toFixed(2)) };
  });
}

async function inspectExamples(browser, origin, width, files) {
  return withPage(browser, origin, width, null, async page => {
    await page.goto(origin + preview);
    const submit = page.getByRole("button", { name: "Validar exemplo" });
    const field = page.getByRole("textbox", { name: "E-mail" });
    await submit.waitFor();
    await submit.click();
    assert.equal(await field.getAttribute("aria-invalid"), "true");
    assert.equal(await field.evaluate(el => el === document.activeElement), true);
    await field.fill("cliente@example.test");
    await field.press("Enter");
    await page.getByRole("status").filter({ hasText: "E-mail válido" }).waitFor();
    assert.equal(await field.getAttribute("aria-invalid"), null);

    const summary = page.locator(".ac-disclosure summary");
    await summary.focus();
    await page.keyboard.press("Enter");
    const link = page.getByRole("link", { name: "Formulário" });
    await link.waitFor();
    await link.focus();
    await page.keyboard.press("Escape");
    assert.equal(await summary.evaluate(el => el === document.activeElement), true);
    assert.equal(await link.isVisible(), false);
    if (width === 390) {
      await summary.tap();
      await link.waitFor();
      await summary.tap();
      assert.equal(await link.isVisible(), false);
    }
    await assertReflow(page, width, "mostruário");
    const table = page.getByRole("region", { name: "Equipamentos de exemplo" });
    await table.focus();
    if (width === 320) {
      assert.ok(await table.evaluate(el => el.scrollWidth > el.clientWidth));
      await page.keyboard.press("ArrowRight");
      await page.waitForFunction(() => document.querySelector(".ac-table-region").scrollLeft > 0, null, { timeout: 3000 });
      await table.evaluate(el => { el.scrollLeft = 0; });
    }
    const contrast = width === 390 ? await checkContrast(page) : null;
    if (width === 320 || width === 1440) await capture(page, "componentes-" + width + ".png", files);
    if (width === 390) {
      await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
      await assertReflow(page, width, "mostruário com texto ampliado");
    }
    return contrast;
  });
}

async function main() {
  assert.ok(dist && output, "Informe duas pastas novas: build e capturas.");
  await fs.mkdir(dist);
  await fs.mkdir(output);
  await build();
  const server = serve();
  server.listen(0, "127.0.0.1");
  await once(server, "listening");
  const origin = "http://127.0.0.1:" + server.address().port;
  try {
    const browser = await chromium.launch({ channel: "msedge" });
    const files = [];
    let contrast;
    try {
      for (const width of widths) {
        for (const sample of samples) await inspectApp(browser, origin, width, sample, files);
        contrast = (await inspectExamples(browser, origin, width, files)) ?? contrast;
      }
      const report = { navegador: "Microsoft Edge " + browser.version(), larguras_px: widths,
        rotas: samples.map(([nome, rota, papeis]) => ({ nome, rota, papeis })),
        interacoes: ["Validação e mensagens", "Abertura por teclado e toque", "Escape e devolução do foco",
          "Rolagem da tabela local por teclado a 320 px", "Texto a 200% em 390 px"],
        contraste: contrast, capturas: files };
      await fs.writeFile(path.join(output, "resultado.json"), JSON.stringify(report, null, 2) + "\n");
      console.log(JSON.stringify(report, null, 2));
    } finally {
      await browser.close();
    }
  } finally {
    server.close();
  }
}

main().catch(error => { console.error(error); process.exitCode = 1; });
