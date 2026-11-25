import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { Receipt } from "./api";

const route = "/area/cliente/compra-simulada";
const api = "/api/v1/cliente/compra-simulada";
const plan = { id: "plano-sintetico", nome: "Plano mensal", modalidade: "Musculação", duracao_dias: 30, preco_base: "129.90" };

function session(role: string) {
  return Response.json({
    roles: [role], user_id: "sessao-teste", csrf_token: "csrf-demo",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
  });
}

function page<T>(items: T[]) {
  return Response.json({ itens: items, pagina: 1, limite: 20, total: items.length });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("simula a própria compra e reutiliza o ID se o primeiro recibo não chegar", async () => {
  const submitted: Record<string, unknown>[] = [];
  const history: Receipt[] = [];
  vi.stubGlobal("fetch", vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return session("CLIENTE");
    if (url.startsWith(api + "/planos?")) return page([plan]);
    if (url.startsWith(api + "?")) return page(history);
    if (url === api && options.method === "POST") {
      expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf-demo" });
      const request = JSON.parse(String(options.body));
      submitted.push(request);
      if (submitted.length === 1) return Response.json({}, { status: 503 });
      const receipt: Receipt = {
        id: request.solicitacao_id, plano_id: plan.id, plano_nome_snapshot: plan.nome,
        estado: "RECUSADO", valor: "129.90", simulado: true,
        simulado_em: "2026-11-24T12:00:00Z", confirmado_em: null,
      };
      history.push(receipt);
      return Response.json(receipt, { status: 201 });
    }
    throw new Error("Rota inesperada: " + url);
  }));
  render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: "Compra simulada de plano" })).toBeTruthy();
  fireEvent.change(await screen.findByLabelText("Plano", { exact: true }), { target: { value: plan.id } });
  fireEvent.change(screen.getByLabelText("Resultado da simulação"), { target: { value: "RECUSADO" } });
  fireEvent.click(screen.getByRole("button", { name: "Registrar simulação" }));
  expect(await screen.findByText(/Não foi possível confirmar o registro/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Registrar simulação" }));
  expect(await screen.findByText(/Simulação registrada · Recusado/)).toBeTruthy();
  const list = await screen.findByRole("list", { name: "Compras simuladas" });
  expect(within(list).getByText(plan.nome)).toBeTruthy();
  expect(within(list).getByText("Recusado")).toBeTruthy();
  expect(submitted).toEqual([
    { solicitacao_id: expect.any(String), plano_id: plan.id, resultado: "RECUSADO" },
    submitted[0],
  ]);
});

test("atendente não carrega o catálogo privado pelo endereço da tela", async () => {
  const fetch = vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return session("ATENDENTE");
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", fetch);
  render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(fetch).toHaveBeenCalledTimes(1);
});
