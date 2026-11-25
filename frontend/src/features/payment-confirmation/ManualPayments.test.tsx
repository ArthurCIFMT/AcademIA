import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { ManualPayment } from "./api";

const clientId = "05b1f23d-aa71-4288-833b-e33c43fdba56";
const ui = "/area/administracao/clientes/" + clientId + "/pagamentos";
const endpoint = "/api/v1/admin/clientes/" + clientId + "/pagamentos";

const existing: ManualPayment = {
  id: "pagamento-de-teste", estado: "CONFIRMADO", confirmado_em: "2026-11-24T13:00:00Z",
  registrado_por_nome: "Funcionário de teste", valor: "149.90", metodo: "PIX", pago_em: "2026-11-23",
  referencia_externa: "REF-TESTE", substitui_id: null, anulado_em: null, anulado_por_nome: null,
  motivo_anulacao: null,
};

function mount(role: string, fakeApi: (url: string, options: RequestInit) => Response) {
  const fetch = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return Response.json({
      roles: [role], user_id: "sessao-sintetica", csrf_token: "csrf-demo",
      expires_at: new Date(Date.now() + 60_000).toISOString(),
    });
    if (url.startsWith(endpoint)) return fakeApi(url, options);
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", fetch);
  render(<MemoryRouter initialEntries={[ui]}><App /></MemoryRouter>);
  return fetch;
}

function page(items: ManualPayment[]) {
  return Response.json({ cliente_nome: "Maria Teste", itens: items, total: items.length, pagina: 1, limite: 20 });
}

function click(name: string) {
  fireEvent.click(screen.getByRole("button", { name }));
}

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label, { exact: true }), { target: { value } });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("registra valor em reais, mantém a chave durante erro e exibe a confirmação no histórico", async () => {
  const requests: object[] = [];
  let records: ManualPayment[] = [];
  mount("ADMINISTRADOR", (url, options) => {
    if (url.startsWith(endpoint + "?")) return page(records);
    expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf-demo" });
    requests.push(JSON.parse(String(options.body)));
    if (requests.length === 1) return new Response(null, { status: 503 });
    records = [existing];
    return Response.json(existing, { status: 201 });
  });
  await screen.findByText("Nenhum pagamento manual neste histórico.");
  click("Registrar pagamento");
  fill("Valor em reais", "149,90");
  fill("Data do pagamento", existing.pago_em);
  fireEvent.change(screen.getByRole("combobox", { name: "Forma de pagamento" }), { target: { value: "PIX" } });
  fill("Referência fictícia do pagamento", existing.referencia_externa);
  click("Salvar registro");
  await screen.findByText("Não foi possível confirmar a operação. Tente novamente.");
  click("Salvar registro");
  await screen.findByText("Pagamento registrado.");
  expect(await screen.findByText("Confirmado", { exact: true })).toBeTruthy();
  expect(requests[0]).toEqual({
    solicitacao_id: expect.any(String), valor: "149.90", metodo: "PIX",
    pago_em: "2026-11-23", referencia_externa: "REF-TESTE",
  });
  expect(requests[1]).toEqual(requests[0]);
});

test("corrige um pagamento e preserva o anterior inativo, depois registra a anulação", async () => {
  const updated: ManualPayment = { ...existing, valor: "120.00", id: "corrigido", substitui_id: existing.id };
  let records = [existing];
  mount("ADMINISTRADOR", (url, options) => {
    if (url.startsWith(endpoint + "?")) return page(records);
    const body = JSON.parse(String(options.body));
    if (url.endsWith("/" + existing.id + "/correcao")) {
      expect(body).toMatchObject({ motivo: "Valor corrigido", valor: "120.00" });
      records = [updated, { ...existing, estado: "ANULADO", motivo_anulacao: body.motivo, anulado_em: existing.confirmado_em }];
      return Response.json(updated, { status: 201 });
    }
    expect(url).toBe(endpoint + "/corrigido/anulacao");
    expect(body).toEqual({ motivo: "Lançamento indevido" });
    records = [{ ...updated, estado: "ANULADO", anulado_em: updated.confirmado_em, motivo_anulacao: body.motivo }, records[1]];
    return Response.json(records[0]);
  });
  await screen.findByText("Confirmado", { exact: true });
  click("Corrigir");
  expect((screen.getByLabelText("Valor em reais", { exact: true }) as HTMLInputElement).value).toBe("149,90");
  fill("Valor em reais", "120,00");
  fill("Motivo", "Valor corrigido");
  click("Salvar registro");
  await screen.findByText("Correção registrada. O pagamento anterior permanece no histórico.");
  const history = await screen.findByRole("list", { name: "Histórico de pagamentos" });
  expect(within(history).getAllByRole("listitem")).toHaveLength(2);
  expect(within(history).getByText("Anulado", { exact: true })).toBeTruthy();
  click("Anular");
  fill("Motivo", "Lançamento indevido");
  click("Confirmar anulação");
  expect(await screen.findByText("Registro anulado.", { exact: true })).toBeTruthy();
  await screen.findByText(/Lançamento indevido/);
  expect(screen.queryByRole("button", { name: "Corrigir" })).toBeNull();
});

test.each(["ATENDENTE", "INSTRUTOR", "CLIENTE"])("bloqueia a área financeira para %s", async role => {
  const fetch = mount(role, () => page([existing]));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(fetch.mock.calls.some(([url]) => url.startsWith(endpoint))).toBe(false);
});
