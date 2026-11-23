import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { ManagedClass } from "./api";
import { academyIsoTime, academyLocalTime } from "./schedule-time";

const pub = "/api/v1/aulas";
const admin = "/api/v1/admin/aulas";
const adminPage = "/area/administracao/aulas";
const item: ManagedClass = {
  id: "d330dcc8-689f-4970-b890-b008f3e2798d", nome: "Pilates de exemplo",
  descricao: "Traga uma toalha.", inicio: "2030-02-02T02:30:00Z", fim: "2030-02-02T03:15:00Z",
  estado: "AGENDADA", revisao: 1,
};

function page(items: ManagedClass[]) {
  return Response.json({ itens: items, pagina: 1, limite: 20, total: items.length });
}

function session(role: string) {
  return Response.json({
    roles: [role], user_id: "usuario-de-teste", csrf_token: "csrf-demo",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
  });
}

function mount(path: string) {
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("converte as datas no fuso da academia e mantém precisão da API ao editar", () => {
  expect(academyLocalTime(item.inicio)).toBe("2030-02-01T23:30");
  expect(academyIsoTime("2030-02-01", "23:30")).toBe("2030-02-02T02:30:00.000Z");
  expect(academyIsoTime("2030-02-30", "23:30")).toBeNull();
  const original = "2030-02-02T02:30:42.391Z";
  expect(academyIsoTime("2030-02-01", "23:30", original)).toBe(original);
});

test.each(["/aulas", "/area/cliente/aulas"])("consulta %s com datas de São Paulo e sem ações administrativas", async (path) => {
  const fetch = vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return session("CLIENTE");
    if (url.startsWith(pub + "?")) return page([item]);
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", fetch);
  mount(path);
  expect(await screen.findByRole("heading", { name: item.nome })).toBeTruthy();
  expect(screen.getByText(/01\/02\/2030.*23:30/)).toBeTruthy();
  expect(screen.getByText(/02\/02\/2030.*00:15/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: /cadastrar|editar|cancelar/i })).toBeNull();
  expect(fetch.mock.calls.some(([url]) => url.startsWith(admin))).toBe(false);
});

test("permite cadastrar, editar e cancelar uma aula pela área administrativa", async () => {
  const changes: { method: string; body: Record<string, unknown> }[] = [];
  let entries: ManagedClass[] = [];
  const fetch = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return session("ADMINISTRADOR");
    if (url.startsWith(admin + "?")) return page(entries);
    if (url.startsWith(admin) && typeof options.body === "string") {
      expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf-demo" });
      const body = JSON.parse(options.body);
      changes.push({ method: options.method ?? "", body });
      const next = url.endsWith("/cancelamento") ? { ...entries[0], estado: "CANCELADA", revisao: 3 }
        : { ...item, ...body, revisao: options.method === "PUT" ? 2 : 1 };
      entries = [next as ManagedClass];
      return Response.json(next, { status: url === admin ? 201 : 200 });
    }
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", fetch);
  mount(adminPage);
  expect(await screen.findByText("Nenhuma aula cadastrada.")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Cadastrar aula" }));
  expect(document.activeElement).toBe(screen.getByRole("heading", { name: "Cadastrar aula" }));
  const fill = (label: string, value: string) => fireEvent.change(screen.getByLabelText(label), { target: { value } });
  fill("Nome da aula", item.nome);
  fill("Data de início", "2030-02-01");
  fill("Hora de início", "23:30");
  fill("Data de término", "2030-02-01");
  fill("Hora de término", "00:15");
  fireEvent.click(screen.getByRole("button", { name: "Salvar aula" }));
  expect((await screen.findByRole("alert")).textContent).toContain("O término precisa ser depois do início.");
  expect(changes).toHaveLength(0);
  fill("Data de término", "2030-02-02");
  fireEvent.click(screen.getByRole("button", { name: "Salvar aula" }));
  expect(await screen.findByText("Aula cadastrada.")).toBeTruthy();
  expect(changes[0]).toMatchObject({ method: "POST", body: {
    nome: item.nome, inicio: "2030-02-02T02:30:00.000Z", fim: "2030-02-02T03:15:00.000Z",
    solicitacao_id: expect.any(String),
  } });

  fireEvent.click(await screen.findByRole("button", { name: "Editar aula " + item.nome }));
  expect((screen.getByLabelText("Hora de início") as HTMLInputElement).value).toBe("23:30");
  fill("Nome da aula", "Pilates atualizado");
  fireEvent.click(screen.getByRole("button", { name: "Salvar aula" }));
  expect(await screen.findByText("Aula atualizada.")).toBeTruthy();
  expect(changes[1]).toMatchObject({ method: "PUT", body: { nome: "Pilates atualizado", revisao: 1 } });

  fireEvent.click(await screen.findByRole("button", { name: "Cancelar aula Pilates atualizado" }));
  expect(changes).toHaveLength(2);
  fireEvent.click(screen.getByRole("button", { name: "Confirmar cancelamento" }));
  expect(await screen.findByText("Aula cancelada.")).toBeTruthy();
  expect(changes[2]).toEqual({ method: "POST", body: { revisao: 2 } });
  expect(await screen.findByText("Cancelada", { exact: true })).toBeTruthy();
  expect(screen.queryByRole("button", { name: "Editar aula Pilates atualizado" })).toBeNull();
});

test("cliente não carrega o painel ao abrir diretamente a URL de administração", async () => {
  const fetch = vi.fn().mockResolvedValueOnce(session("CLIENTE"));
  vi.stubGlobal("fetch", fetch);
  mount(adminPage);
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(fetch).toHaveBeenCalledTimes(1);
});
