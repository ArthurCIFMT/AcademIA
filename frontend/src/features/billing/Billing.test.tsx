import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { Charge } from "./api";

const clientId = "cliente-teste";
const adminRoute = "/area/administracao/clientes/" + clientId + "/cobrancas";
const adminApi = "/api/v1/admin/clientes/" + clientId + "/cobrancas";
const ownRoute = "/area/cliente/cobrancas";
const ownApi = "/api/v1/cliente/cobrancas";
const item: Charge = {
  id: "cobranca-teste", competencia: "2026-11-01", vencimento: "2026-11-27",
  valor: "150.00", valor_pago: "0.00", saldo: "150.00", estado: "ABERTA",
  situacao: "ABERTA", matricula_id: "matricula-teste", revisao: 1,
};

function mount(role: string, path: string, response: (url: string, options: RequestInit) => Response) {
  const fetch = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return Response.json({
      roles: [role], user_id: "sessao-teste", csrf_token: "csrf-exemplo",
      expires_at: new Date(Date.now() + 60_000).toISOString(),
    });
    return response(url, options);
  });
  vi.stubGlobal("fetch", fetch);
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  return fetch;
}

function page<T>(items: T[]) {
  return { itens: items, pagina: 1, limite: 20, total: items.length };
}

function billing(items: Charge[]) {
  return Response.json({
    ...page(items), cliente_nome: "Cliente sintético",
    politica_inadimplencia: "SOMENTE_INFORMATIVA",
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label, { exact: true }), { target: { value } });
}

test("cria, edita e consulta o histórico de uma cobrança administrativa", async () => {
  let items: Charge[] = [];
  const requests: Record<string, unknown>[] = [];
  mount("ADMINISTRADOR", adminRoute, (url, options) => {
    if (url.startsWith(adminApi + "?")) return billing(items);
    if (url.startsWith(adminApi + "/matriculas?")) return Response.json(page([
      { id: item.matricula_id, inicio: "2026-11-01", fim: "2026-11-30", modalidade: "Musculação" },
    ]));
    if (url.includes("/historico?")) return Response.json(page([
      { revisao: 2, dados: items[0], autor_nome: "Administrador teste", registrado_em: "2026-11-24T02:00:00Z" },
      { revisao: 1, dados: item, autor_nome: "Administrador teste", registrado_em: "2026-11-24T01:00:00Z" },
    ]));
    expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf-exemplo" });
    const body = JSON.parse(String(options.body));
    requests.push(body);
    if (options.method === "POST") {
      items = [item];
      return Response.json(item, { status: 201 });
    }
    expect(options.method).toBe("PUT");
    expect(url).toBe(adminApi + "/" + item.id);
    items = [{ ...item, valor: body.valor, saldo: body.valor, revisao: 2 }];
    return Response.json(items[0]);
  });

  await screen.findByText("Nenhuma cobrança registrada.");
  fireEvent.click(screen.getByRole("button", { name: "Nova cobrança" }));
  await screen.findByRole("option", { name: /Musculação/ });
  fill("Competência", "2026-11");
  fill("Vencimento", item.vencimento);
  fill("Valor em reais", "150,00");
  fireEvent.change(screen.getByRole("combobox", { name: /Matrícula vinculada/ }),
    { target: { value: item.matricula_id } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar cobrança" }));
  expect(await screen.findByText("Cobrança salva.")).toBeTruthy();
  expect(requests[0]).toEqual({
    competencia: item.competencia, vencimento: item.vencimento, valor: "150.00",
    matricula_id: item.matricula_id, solicitacao_id: expect.any(String),
  });
  expect((await screen.findByRole("link", { name: "Registrar pagamento" })).getAttribute("href"))
    .toContain("/pagamentos?cobranca=" + item.id);

  fireEvent.click(screen.getByRole("button", { name: "Editar" }));
  fill("Valor em reais", "159,90");
  fireEvent.click(screen.getByRole("button", { name: "Salvar cobrança" }));
  await screen.findByRole("button", { name: "Ver revisões" });
  expect(requests[1]).toMatchObject({ valor: "159.90", revisao: 1, estado: "ABERTA" });
  fireEvent.click(screen.getByRole("button", { name: "Ver revisões" }));
  const history = await screen.findByRole("list", { name: "Revisões da cobrança" });
  expect(within(history).getAllByRole("listitem")).toHaveLength(2);
  expect(within(history).getByRole("heading", { name: "Revisão 1" })).toBeTruthy();
});

test("o cliente consulta somente a rota própria e vê o saldo sem ações administrativas", async () => {
  const fetch = mount("CLIENTE", ownRoute, (url) => {
    expect(url).toBe(ownApi + "?pagina=1");
    return billing([{ ...item, situacao: "VENCIDA", valor_pago: "70.00", saldo: "80.00" }]);
  });
  expect(await screen.findByText("Vencida")).toBeTruthy();
  expect(screen.getByText(/Saldo R\$\s*80,00/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Editar" })).toBeNull();
  expect(screen.queryByRole("link", { name: "Registrar pagamento" })).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url.startsWith(adminApi))).toBe(false);
});

test.each(["CLIENTE", "ATENDENTE", "INSTRUTOR"])("recusa %s na tela administrativa de cobranças", async role => {
  const fetch = mount(role, adminRoute, () => billing([item]));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(fetch.mock.calls.some(([url]) => url.startsWith(adminApi))).toBe(false);
});
