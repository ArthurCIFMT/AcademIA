import { fileURLToPath } from "node:url";
import { defineConfig } from "@playwright/test";

const origin = process.env.ACADEMIA_E2E_ORIGIN;
const output = process.env.ACADEMIA_E2E_OUTPUT;
if (!origin || !output || !process.env.ACADEMIA_E2E_FIXTURE || !process.env.ACADEMIA_E2E_API) {
  throw new Error("Inicie pelo runner backend/tests/acceptance; não usar ambiente de desenvolvimento.");
}
const url = new URL(origin);
if (url.hostname !== "127.0.0.1" || url.protocol !== "http:") throw new Error("E2E somente local.");
export default defineConfig({
  testDir: ".", testMatch: "mvp.spec.ts", fullyParallel: false, workers: 1,
  retries: 0, timeout: 120_000, expect: { timeout: 12_000 },
  reporter: [["list"], ["json", { outputFile: output + "/playwright.json" }]],
  outputDir: output + "/artefatos-privados",
  use: { baseURL: origin, browserName: "chromium",
    channel: process.env.ACADEMIA_E2E_CHANNEL === "chromium" ? undefined : "msedge",
    actionTimeout: 10_000, navigationTimeout: 15_000,
    viewport: { width: 1280, height: 800 }, locale: "pt-BR",
    screenshot: "only-on-failure", trace: "off", video: "off" },
  webServer: {
    cwd: fileURLToPath(new URL("../../", import.meta.url)),
    command: "node node_modules/vite/bin/vite.js --host 127.0.0.1 --port " + url.port + " --strictPort",
    url: origin, reuseExistingServer: false, timeout: 30_000,
    env: { ACADEMIA_API_PROXY_TARGET: process.env.ACADEMIA_E2E_API },
  },
});
