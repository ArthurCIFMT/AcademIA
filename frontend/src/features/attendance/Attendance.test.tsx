import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { AttendancePage } from "./api";

const visit = { id: "visita", entrada_em: "2026-11-24T02:30:00Z", saida_em: null };
const clientId = "71e3b580-e600-4d65-b00b-80b48d16b4e5";
const staffPath = "/area/atendimento/clientes/frequencia/" + clientId;
const ownPath = "/area/cliente/frequencia";
const occupancyPath = "/area/cliente/lotacao";

function session(role: string) {
  return Response.json({
    roles: [role], user_id: "usuario-de-teste", csrf_token: "csrf-demo",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
  });
}

function history(items: AttendancePage["itens"]) {
  return Response.json({ itens: items, cliente_nome: "Cliente sintético",
    de: "2026-11-23", ate: "2026-11-24", pagina: 1, limite: 20, total: items.length });
}

function mount(path: string) {
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("cliente pesquisa o próprio histórico por data e vê o horário da academia", async () => {
  const fetch = vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return session("CLIENTE");
    if (url.includes("/v1/cliente/frequencia?")) return history(url.includes("de=2026-11-23") ? [visit] : []);
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", fetch);
  mount(ownPath);
  expect(await screen.findByText("Nenhuma visita registrada neste período.")).toBeTruthy();
  const change = (label: string, value: string) =>
    fireEvent.change(screen.getByLabelText(label), { target: { value } });
  change("Data inicial", "2026-11-25");
  change("Data final", "2026-11-24");
  const submit = screen.getByRole("button", { name: "Consultar frequência" });
  fireEvent.click(submit);
  expect(screen.getByRole("alert").textContent).toContain("igual ou anterior");
  expect(fetch.mock.calls.filter(([url]) => url.includes("/frequencia?"))).toHaveLength(1);
  change("Data inicial", "2026-11-23");
  fireEvent.click(submit);
  expect(await screen.findByText("Sem saída confirmada")).toBeTruthy();
  expect(screen.getByText(/23\/11\/2026.*23:30/)).toBeTruthy();
});

test("rotas de frequência de terceiros são restritas na interface", async () => {
  const fetch = vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return session("CLIENTE");
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", fetch);
  mount(staffPath);
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(fetch.mock.calls.some(([url]) => url.includes("/frequencia?"))).toBe(false);
});

test("atendente consulta o histórico de um cliente", async () => {
  vi.stubGlobal("fetch", vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return session("ATENDENTE");
    if (url.includes("/v1/clientes/" + clientId + "/frequencia?")) return history([visit]);
    throw new Error("Rota inesperada: " + url);
  }));
  mount(staffPath);
  expect(await screen.findByRole("heading", { name: "Cliente sintético" })).toBeTruthy();
  expect(screen.getByRole("link", { name: "Voltar à lista de clientes" }).getAttribute("href")).toBe("/area/atendimento/clientes");
});

test("lotação mostra zero, permite atualizar, trata falha e recupera", async () => {
  let next = 0;
  vi.stubGlobal("fetch", vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return session("CLIENTE");
    if (url.endsWith("/v1/acesso/lotacao")) {
      if (next === 1) return new Response(null, { status: 503 });
      return Response.json({ total_presentes: next });
    }
    throw new Error("Rota inesperada: " + url);
  }));
  mount(occupancyPath);
  const update = await screen.findByRole("button", { name: "Atualizar lotação" });
  expect((await screen.findByText("pessoas presentes", { exact: true })).textContent).toBe("0 pessoas presentes");
  next = 1;
  fireEvent.click(update);
  expect(await screen.findByRole("alert")).toBeTruthy();
  next = 3;
  fireEvent.click(update);
  expect((await screen.findByText("pessoas presentes", { exact: true })).textContent).toBe("3 pessoas presentes");
});
