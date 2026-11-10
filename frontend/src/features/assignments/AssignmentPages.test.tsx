import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";

const base = "/api/v1/designacoes";
const clientId = "f8322928-b17d-4ec6-aa99-85ae29a8b9c4";
const adminId = "aa494a48-c4d5-45c5-8afd-8c16dc4d9aaa";
const firstId = "c54a8ad1-03c9-4779-8b71-2ab7f849ea59";
const secondId = "ce0b56d1-f2ce-4083-9627-96ea79a598c8";
const since = "2026-11-07T12:00:00Z";
const replacedAt = "2026-11-07T13:00:00Z";
const path = "/area/administracao/designacoes?cliente=" + clientId;

function session(roles: string[]) {
  return Response.json({
    user_id: adminId,
    expires_at: new Date(Date.now() + 60_000).toISOString(),
    csrf_token: "csrf-sintetico",
    roles,
  });
}

function mount(url: string) {
  render(<MemoryRouter initialEntries={[url]}><App /></MemoryRouter>);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("admin troca responsável, envia CSRF e vê o vínculo anterior no histórico", async () => {
  const previous = {
    id: firstId, cliente_id: clientId, instrutor_id: firstId, instrutor_nome: "Instrutor anterior",
    inicio: since, fim: null, atribuido_por: adminId,
  };
  const next = {
    ...previous, id: secondId, instrutor_id: secondId, instrutor_nome: "Novo instrutor", inicio: replacedAt,
  };
  let swapped = false;
  const request = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return session(["ADMINISTRADOR"]);
    if (url === base + "/instrutores?pagina=1") {
      return Response.json({
        itens: [{ id: secondId, nome: "Novo instrutor", email: "novo@example.test" }],
        pagina: 1, limite: 20, total: 1,
      });
    }
    if (url === base + "/clientes/" + clientId && options.method === "PUT") {
      swapped = true;
      return Response.json(next);
    }
    if (url === base + "/clientes/" + clientId + "?pagina=1") {
      return Response.json({
        cliente: { id: clientId, nome: "Cliente sintético" },
        cliente_elegivel: true,
        vigente: swapped ? next : previous,
        instrutor_ativo: true,
        historico: { itens: swapped ? [{ ...previous, fim: replacedAt }] : [], pagina: 1, limite: 20, total: swapped ? 1 : 0 },
      });
    }
    throw Error("Rota inesperada.");
  });
  vi.stubGlobal("fetch", request);
  mount(path);
  expect(await screen.findByText("Responsável atual: Instrutor anterior")).toBeTruthy();
  fireEvent.click(await screen.findByRole("radio", { name: /Novo instrutor/ }));
  fireEvent.click(screen.getByRole("button", { name: "Salvar designação" }));

  expect(await screen.findByText("Responsável atual: Novo instrutor")).toBeTruthy();
  expect(screen.getByText(/Instrutor anterior ·/)).toBeTruthy();
  expect(request).toHaveBeenCalledWith(base + "/clientes/" + clientId, expect.objectContaining({
    method: "PUT",
    headers: expect.objectContaining({ "X-CSRF-Token": "csrf-sintetico" }),
    body: JSON.stringify({ instrutor_id: secondId, vigente_id: firstId }),
  }));
});

test("instrutor consulta seus clientes sem enviar o ID do instrutor", async () => {
  const request = vi.fn()
    .mockResolvedValueOnce(session(["INSTRUTOR"]))
    .mockResolvedValueOnce(Response.json({
      itens: [{ id: clientId, nome: "Cliente sintético", inicio: since }],
      pagina: 1, limite: 20, total: 1,
    }));
  vi.stubGlobal("fetch", request);
  mount("/area/instrutor/clientes");
  expect(await screen.findByText(/Cliente sintético/)).toBeTruthy();
  expect(request).toHaveBeenCalledWith(base + "/minhas?pagina=1", expect.anything());
});

test("atendente não acessa a tela administrativa de designação", async () => {
  const request = vi.fn().mockResolvedValueOnce(session(["ATENDENTE"]));
  vi.stubGlobal("fetch", request);
  mount(path);
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request).toHaveBeenCalledTimes(1);
});
