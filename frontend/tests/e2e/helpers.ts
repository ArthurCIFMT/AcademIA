import { readFileSync } from "node:fs";
import { expect, request, type Page } from "@playwright/test";

export const origin = process.env.ACADEMIA_E2E_ORIGIN!;
export const password = process.env.ACADEMIA_E2E_PASSWORD!;
export const fixture = JSON.parse(readFileSync(process.env.ACADEMIA_E2E_FIXTURE!, "utf8")) as {
  usuarios: Record<string, { id: string; email: string; onboarding_id?: string }>;
  sufixo: string;
};
export async function signIn(page: Page, email: string, secret = password) {
  await page.goto("/login");
  await page.getByLabel("E-mail", { exact: true }).fill(email);
  await page.getByLabel("Senha", { exact: true }).fill(secret);
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("button", { name: "Sair", exact: true })).toBeVisible();
}
export async function signOut(page: Page) {
  await page.getByRole("button", { name: "Sair", exact: true }).click();
  await expect(page.getByLabel("E-mail", { exact: true })).toBeVisible();
}
export async function session(page: Page) {
  const response = await page.request.get("/api/v1/auth/session");
  expect(response.status()).toBe(200);
  return await response.json() as { user_id: string; csrf_token: string; roles: string[] };
}
export async function mutate(page: Page, path: string, data: object, method = "POST") {
  const auth = await session(page);
  return page.request.fetch("/api" + path, { method, data,
    headers: { Origin: origin, "X-CSRF-Token": auth.csrf_token } });
}
export async function mailLink(email: string, pathname: string) {
  const mailbox = await request.newContext();
  let found = "";
  try {
    await expect.poll(async () => {
      const reply = await mailbox.get("http://127.0.0.1:8025/api/v1/search?query=" + encodeURIComponent("to:" + email));
      expect(reply.ok()).toBeTruthy();
      const body = await reply.json() as { messages: { ID: string }[] };
      for (const item of body.messages) {
        const detail = await (await mailbox.get("http://127.0.0.1:8025/api/v1/message/" + item.ID)).json() as { Text: string };
        for (const match of detail.Text.matchAll(/https?:\/\/[^\s<>"']+/g)) {
          const url = new URL(match[0]);
          if (url.origin === origin && url.pathname === pathname) { found = url.href; return true; }
        }
      }
      return false;
    }, { timeout: 15_000, intervals: [100, 300, 500] }).toBe(true);
  } finally { await mailbox.dispose(); }
  return found;
}
export async function firstAccess(page: Page, email: string) {
  await page.goto(await mailLink(email, "/primeiro-acesso"));
  await page.getByLabel("Nova senha", { exact: true }).fill(password);
  await page.getByLabel("Confirme a nova senha").fill(password);
  await page.getByRole("button", { name: "Definir senha", exact: true }).click();
  await expect(page.getByText("Senha definida. Entre com sua senha.", { exact: true })).toBeVisible();
  expect(page.url()).not.toContain("token=");
}
export async function completeOnboarding(page: Page) {
  await page.getByLabel("Altura (cm)", { exact: true }).fill("170");
  await page.getByLabel("Peso (kg)", { exact: true }).fill("70");
  await page.getByLabel("Objetivo principal").selectOption("CONDICIONAMENTO");
  await page.getByLabel("Experiência com exercícios").selectOption("INICIANTE");
  await page.getByLabel("Nível de atividade atual").selectOption("LEVE");
  await page.getByLabel("Dias disponíveis por semana").fill("3");
  await page.getByLabel("Tempo por sessão (minutos)").fill("45");
  for (const label of ["Possui alguma condição de saúde?", "Usa medicamentos?",
    "Possui dor, lesão ou limitação?", "Já recebeu alguma orientação para restringir exercícios?",
    "Teve algum evento de saúde importante recentemente?"]) {
    await page.getByLabel(label, { exact: true }).selectOption("NAO");
  }
  await page.getByRole("button", { name: "Salvar rascunho", exact: true }).click();
  await expect(page.getByText("Rascunho salvo.", { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByLabel("Peso (kg)", { exact: true })).toHaveValue("70");
  await page.getByRole("button", { name: "Concluir onboarding", exact: true }).click();
}
export async function generate(page: Page) {
  await page.goto("/area/cliente/treino-ia");
  const reply = page.waitForResponse(r => r.url().endsWith("/api/v1/ia/fichas/execucoes") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Solicitar geração", exact: true }).click();
  const response = await reply;
  expect(response.status()).toBe(200);
  return await response.json() as { solicitacao_id: string; estado: string; versao_publicada_id: string | null };
}
export async function manualEditor(page: Page, clientId: string, exercise = "Agachamento E2E") {
  await page.goto("/area/instrutor/clientes/" + clientId + "/treinos");
  await page.getByRole("button", { name: "Novo rascunho manual", exact: true }).click();
  await page.getByLabel("Onboarding de referência").selectOption({ index: 1 });
  await page.getByRole("button", { name: "Adicionar dia", exact: true }).click();
  await page.getByLabel("Título do dia").fill("Dia de força");
  await page.getByRole("button", { name: "Adicionar exercício", exact: true }).click();
  await page.getByLabel("Exercício", { exact: true }).selectOption({ label: exercise });
  await page.getByLabel("Séries", { exact: true }).fill("2");
  await page.getByLabel("Repetições", { exact: true }).fill("8-12");
  await page.getByLabel("Intervalo (segundos)").fill("60");
  await page.getByRole("button", { name: "Salvar rascunho", exact: true }).click();
  await expect(page.getByText("Rascunho salvo.", { exact: true })).toBeVisible();
  await page.getByRole("link", { name: "Publicar ou avaliar a versão salva", exact: true }).click();
  await page.getByLabel("Conferi as restrições e o conteúdo salvo desta versão").check();
}
export async function publishManual(page: Page) {
  const reply = page.waitForResponse(r => r.url().endsWith("/publicacao") && r.request().method() === "POST");
  await page.getByRole("button", { name: "Publicar versão salva", exact: true }).click();
  const response = await reply;
  expect(response.status()).toBe(200);
  return await response.json();
}
export async function review(page: Page, client: string, version: string, decision: string) {
  await page.goto("/area/instrutor/clientes/" + client + "/treinos/" + version + "/revisao");
  await page.getByLabel("Decisão", { exact: true }).selectOption(decision);
  await page.getByLabel("Motivo do parecer").fill("Parecer sintético do cenário E2E.");
  await page.getByRole("button", { name: "Registrar parecer", exact: true }).click();
  await expect(page.getByText("Parecer " + decision, { exact: true })).toBeVisible();
}
