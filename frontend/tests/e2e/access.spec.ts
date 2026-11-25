import { randomUUID } from "node:crypto";
import { expect, request, test, type Page } from "@playwright/test";

import { fixture, signIn } from "./helpers";

const name = "Cliente seguranca";
const plan = "Plano experimental";
const person = fixture.usuarios.seguranca;

async function menu(page: Page, name: string) {
  const disclosure = page.locator(".site-mobile-menu summary");
  if (await disclosure.isVisible()) await disclosure.click();
  await page.getByRole("navigation", { name: "Seções da área", exact: true })
    .getByRole("link", { name, exact: true }).click();
}

async function authorize(page: Page, direction: "ENTRADA" | "SAIDA") {
  await page.getByRole("combobox", { name: "Direção", exact: true }).selectOption(direction);
  await page.getByLabel("Selecionar foto", { exact: true }).setInputFiles(process.env.ACADEMIA_E2E_ACCESS_PHOTO!);
  await page.getByRole("button", { name: "Identificar cliente" }).click();
  await expect(page.getByText("Cliente identificado.", { exact: true })).toBeVisible();
  const authorized = page.waitForResponse(response =>
    response.url().endsWith("/autorizacao") && response.request().method() === "POST");
  await page.getByRole("button", { name: "Solicitar autorização" }).click();
  const response = await authorized;
  expect(response.status()).toBe(201);
  const decision = await response.json();
  expect(decision.resultado).toBe("ALLOW");
  await expect(page.getByText("Comando aceito. Aguardando a passagem simulada.", { exact: true })).toBeVisible();
  return decision.comando.request_id as string;
}

test("cliente móvel, atendente e administrador conferem matrícula, passagem e frequência", async ({ browser, baseURL }) => {
  const adminContext = await browser.newContext({ baseURL });
  const staffContext = await browser.newContext({ baseURL });
  const clientContext = await browser.newContext({
    baseURL, viewport: { width: 375, height: 812 }, isMobile: true, hasTouch: true,
  });
  const simulator = await request.newContext({
    baseURL: process.env.ACADEMIA_E2E_ACCESS_SIMULATOR,
    extraHTTPHeaders: { Authorization: "Bearer " + process.env.ACADEMIA_E2E_ACCESS_TOKEN },
  });
  const admin = await adminContext.newPage();
  const staff = await staffContext.newPage();
  const client = await clientContext.newPage();
  const today = new Intl.DateTimeFormat("sv-SE", { timeZone: "America/Sao_Paulo" }).format(new Date());
  try {
    await signIn(admin, fixture.usuarios.admin.email);
    await expect(admin.getByRole("heading", { name: "Indicadores da academia" })).toBeVisible();
    const metric = (label: string) => admin.locator(".dashboard-metric").filter({ hasText: label }).locator("dd");
    await expect(metric("Pessoas presentes agora")).toHaveText("0");
    await menu(admin, "Gerenciar planos");
    await admin.getByRole("button", { name: "Novo plano" }).click();
    await admin.getByLabel("Nome", { exact: true }).fill(plan);
    await admin.getByLabel("Modalidade", { exact: true }).fill("Musculação");
    await admin.getByLabel("Duração em dias").fill("30");
    await admin.getByLabel("Entradas por dia").fill("1");
    await admin.getByLabel("Preço simulado em reais").fill("129,90");
    await admin.getByRole("button", { name: "Salvar plano" }).click();
    await expect(admin.getByText("Plano salvo.", { exact: true })).toBeVisible();

    await signIn(staff, fixture.usuarios.atendente.email);
    await menu(staff, "Clientes e convites");
    await staff.getByRole("button", { name: "Matrícula e acesso de " + name, exact: true }).click();
    await expect(staff.getByText(/Nenhuma compra simulada registrada/)).toBeVisible();
    const planSelect = staff.getByRole("combobox", { name: "Plano", exact: true });
    await planSelect.selectOption({ label: plan + " · Musculação" });
    await staff.getByLabel("Início", { exact: true }).fill(today);
    await staff.getByRole("button", { name: "Registrar matrícula" }).click();
    await expect(staff.getByText(/Matrícula registrada até/)).toBeVisible();

    await signIn(client, person.email);
    await menu(client, "Minha frequência");
    await expect(client.getByText("Nenhuma visita registrada neste período.")).toBeVisible();
    await menu(client, "Lotação atual");
    await expect(client.getByRole("status")).toHaveText("0 pessoas presentes");
    expect(await client.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

    await menu(staff, "Reconhecimento facial");
    const entry = await authorize(staff, "ENTRADA");
    await client.getByRole("button", { name: "Atualizar lotação" }).click();
    await expect(client.getByRole("status")).toHaveText("0 pessoas presentes");
    const payload = { schema_version: 1, event_id: randomUUID() };
    expect((await simulator.post("/commands/" + entry + "/passages", { data: payload })).status()).toBe(201);
    expect((await simulator.post("/commands/" + entry + "/passages", { data: payload })).status()).toBe(200);
    await client.getByRole("button", { name: "Atualizar lotação" }).click();
    await expect(client.getByRole("status")).toHaveText("1 pessoa presente");
    const aggregate = await client.request.get("/api/v1/acesso/lotacao");
    expect(await aggregate.json()).toEqual({ total_presentes: 1 });
    await staff.getByRole("button", { name: "Consultar passagem" }).click();
    await expect(staff.getByText("Passagem simulada confirmada.", { exact: true })).toBeVisible();
    await menu(client, "Minha frequência");
    await expect(client.getByText("Sem saída confirmada")).toBeVisible();
    expect(await client.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

    await menu(admin, "Painel");
    await expect(metric("Clientes com matrícula vigente")).toHaveText("1");
    await expect(metric("Pessoas presentes agora")).toHaveText("1");
    await expect(admin.getByRole("list", { name: "Visitas por semana" }).getByRole("listitem").last().locator("strong")).toHaveText("1");
    await menu(admin, "Gerenciar clientes");
    await admin.getByRole("link", { name: "Frequência de " + name, exact: true }).click();
    await expect(admin.getByRole("heading", { name })).toBeVisible();
    await expect(admin.getByText("Sem saída confirmada")).toBeVisible();
    await client.goto("/area/administracao/clientes/frequencia/" + person.id);
    await expect(client.getByRole("heading", { name: "Acesso não permitido" })).toBeVisible();
    expect((await client.request.get("/api/v1/clientes/" + fixture.usuarios.manual.id + "/frequencia")).status()).toBe(403);

    const exit = await authorize(staff, "SAIDA");
    expect((await simulator.post("/commands/" + exit + "/passages", {
      data: { schema_version: 1, event_id: randomUUID() },
    })).status()).toBe(201);
    await menu(staff, "Clientes e convites");
    await staff.getByRole("link", { name: "Frequência de " + name, exact: true }).click();
    const visits = staff.getByRole("list", { name: "Visitas confirmadas" });
    await expect(visits.getByRole("listitem")).toHaveCount(1);
    await expect(visits.locator("time")).toHaveCount(2);
    await admin.getByRole("button", { name: "Consultar frequência" }).click();
    await expect(admin.getByRole("list", { name: "Visitas confirmadas" }).locator("time")).toHaveCount(2);
    await menu(admin, "Lotação atual");
    await expect(admin.getByRole("status")).toHaveText("0 pessoas presentes");
    await menu(admin, "Painel");
    await expect(metric("Pessoas presentes agora")).toHaveText("0");
    await admin.setViewportSize({ width: 375, height: 812 });
    await expect(admin.getByRole("combobox", { name: "Dia para detalhar" })).toBeVisible();
    expect(await admin.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);

    await menu(admin, "Gerenciar clientes");
    await admin.getByRole("link", { name: "Pagamentos de " + name, exact: true }).click();
    await admin.getByRole("button", { name: "Registrar pagamento" }).click();
    await admin.getByLabel("Valor em reais", { exact: true }).fill("149,90");
    await admin.getByLabel("Data do pagamento", { exact: true }).fill(today);
    await admin.getByRole("combobox", { name: "Forma de pagamento" }).selectOption("PIX");
    await admin.getByLabel("Referência fictícia do pagamento", { exact: true }).fill("MEM00-EXEMPLO-EDGE");
    await admin.getByRole("button", { name: "Salvar registro" }).click();
    await expect(admin.getByText("Pagamento registrado.", { exact: true })).toBeVisible();
    await expect(admin.getByText("Confirmado", { exact: true })).toBeVisible();

    await admin.getByRole("button", { name: "Corrigir", exact: true }).click();
    await admin.getByLabel("Valor em reais", { exact: true }).fill("129,90");
    await admin.getByLabel("Motivo", { exact: true }).fill("Correção de valor de teste.");
    await admin.getByRole("button", { name: "Salvar registro" }).click();
    await expect(admin.getByText("Correção registrada. O pagamento anterior permanece no histórico.")).toBeVisible();
    await expect(admin.getByText("Anulado", { exact: true })).toHaveCount(1);

    await admin.getByRole("button", { name: "Anular", exact: true }).click();
    await admin.getByLabel("Motivo", { exact: true }).fill("Anulação de teste.");
    await admin.getByRole("button", { name: "Confirmar anulação" }).click();
    await expect(admin.getByText("Anulado", { exact: true })).toHaveCount(2);

    await menu(admin, "Gerenciar clientes");
    await admin.getByRole("link", { name: "Cobranças de " + name, exact: true }).click();
    await admin.getByRole("button", { name: "Nova cobrança" }).click();
    await admin.getByLabel("Competência", { exact: true }).fill(today.slice(0, 7));
    await admin.getByLabel("Vencimento", { exact: true }).fill(today);
    await admin.getByLabel("Valor em reais", { exact: true }).fill("95,50");
    const membership = admin.getByRole("combobox", { name: /Matrícula vinculada/ });
    await expect(membership.getByRole("option", { name: /Musculação/ })).toBeAttached();
    await membership.selectOption({ index: 1 });
    await admin.getByRole("button", { name: "Salvar cobrança" }).click();
    await expect(admin.getByText("Cobrança salva.", { exact: true })).toBeVisible();

    await client.goto("/area/cliente");
    await expect(client.getByRole("heading", { name: "Área do cliente" })).toBeVisible();
    await menu(client, "Minhas cobranças");
    await expect(client.getByText("Em aberto", { exact: true })).toBeVisible();
    await expect(client.getByRole("button", { name: "Editar" })).toHaveCount(0);
    await admin.getByRole("link", { name: "Registrar pagamento", exact: true }).click();
    await admin.getByLabel("Valor em reais", { exact: true }).fill("95,50");
    await admin.getByRole("combobox", { name: "Forma de pagamento" }).selectOption("PIX");
    await admin.getByLabel("Referência fictícia do pagamento", { exact: true }).fill("FIN01-EXEMPLO-EDGE");
    await admin.getByRole("button", { name: "Salvar registro" }).click();
    await expect(admin.getByText("Pagamento registrado.", { exact: true })).toBeVisible();
    await admin.getByRole("link", { name: "Voltar às cobranças", exact: true }).click();
    await expect(admin.getByText("Quitada", { exact: true })).toBeVisible();
    await client.reload();
    await expect(client.getByText("Quitada", { exact: true })).toBeVisible();

    await menu(client, "Simular compra de plano");
    await expect(client.getByRole("heading", { name: "Compra simulada de plano" })).toBeVisible();
    await expect(client.getByText(/Os valores são fictícios/)).toBeVisible();
    const purchasePlan = client.getByRole("combobox", { name: "Plano", exact: true });
    await expect(purchasePlan.getByRole("option", { name: /Plano experimental/ })).toBeAttached();
    await purchasePlan.selectOption({ index: 1 });
    await client.getByRole("combobox", { name: "Resultado da simulação" }).selectOption("CONFIRMADO");
    await client.getByRole("button", { name: "Registrar simulação" }).click();
    const receipt = client.getByRole("list", { name: "Compras simuladas" }).getByRole("listitem");
    await expect(receipt.getByRole("heading", { name: plan })).toBeVisible();
    await expect(receipt.getByText(/Valor simulado.*129,90/)).toBeVisible();
    await client.reload();
    await expect(receipt.getByText("Confirmado", { exact: true })).toBeVisible();
    const purchaseSummary = "/api/v1/atendimento/clientes/" + person.id + "/ultima-compra-simulada";
    expect((await client.request.get(purchaseSummary)).status()).toBe(403);
    await menu(staff, "Clientes e convites");
    await staff.getByRole("searchbox", { name: "Nome ou e-mail" }).fill(person.email);
    await staff.getByRole("button", { name: "Pesquisar" }).click();
    await staff.getByRole("button", { name: "Matrícula e acesso de " + name, exact: true }).click();
    await expect(staff.getByText(/Plano experimental · Confirmada/)).toBeVisible();
    await staff.getByRole("link", { name: "Frequência", exact: true }).click();
    await expect(staff.getByRole("list", { name: "Visitas confirmadas" }).locator("time")).toHaveCount(2);
    await staff.getByRole("link", { name: "Voltar à lista de clientes" }).click();
    await expect(staff.getByRole("heading", { name: "Matrícula e acesso" })).toBeVisible();
    await staff.getByRole("button", { name: "Voltar à lista", exact: true }).click();
    await staff.reload();
    await expect(staff.getByRole("searchbox", { name: "Nome ou e-mail" })).toHaveValue(person.email);
    await menu(admin, "Painel");
    await expect(admin.getByRole("heading", { name: "Financeiro simulado" })).toBeVisible();
  } finally {
    await simulator.dispose();
    await Promise.all([adminContext.close(), staffContext.close(), clientContext.close()]);
  }
});
