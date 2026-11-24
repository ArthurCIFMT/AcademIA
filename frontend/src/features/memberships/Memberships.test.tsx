import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { Membership, Plan } from "./api";

const plan: Plan = {
  id: "plano-teste", nome: "Mensal", modalidade: "Musculação", duracao_dias: 30,
  limite_acessos: 2, ativo: true, revisao: 1,
};
const historyPath = "/api/v1/atendimento/clientes/cliente-teste/matriculas";
const paths = {
  admin: "/area/administracao/planos",
  attendant: "/area/atendimento/matriculas",
};

function session(role: string) {
  return Response.json({
    user_id: "usuario-de-teste", roles: [role], csrf_token: "csrf-demo",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
  });
}

function page<T>(items: T[]) {
  return Response.json({ itens: items, pagina: 1, limite: 20, total: items.length });
}

function mount(path: string) {
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("administra plano e pode desativá-lo pela tela", async () => {
  const writes: Record<string, unknown>[] = [];
  const mockFetch = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return session("ADMINISTRADOR");
    if (url.startsWith("/api/v1/admin/planos?")) return page([{ ...plan, ativo: writes.length === 0 }]);
    if (url === "/api/v1/admin/planos/plano-teste" && options.method === "PUT") {
      expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf-demo" });
      writes.push(JSON.parse(String(options.body)));
      return Response.json({ ...plan, ativo: false, revisao: 2 });
    }
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", mockFetch);
  mount(paths.admin);
  fireEvent.click(await screen.findByRole("button", { name: "Editar plano Mensal" }));
  fireEvent.click(screen.getByRole("checkbox", { name: "Plano ativo" }));
  fireEvent.click(screen.getByRole("button", { name: "Salvar plano" }));
  expect(await screen.findByText("Plano salvo.")).toBeTruthy();
  expect(await screen.findByText("Inativo")).toBeTruthy();
  expect(writes).toEqual([{
    nome: plan.nome, modalidade: plan.modalidade, duracao_dias: 30,
    limite_acessos: 2, ativo: false, revisao: 1,
  }]);
});

test("atendente matricula cliente pelo plano ativo e consulta a renovação", async () => {
  const writes: Record<string, unknown>[] = [];
  let entries: Membership[] = [];
  const mockFetch = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return session("ATENDENTE");
    if (url.startsWith("/api/v1/clientes?")) return page([{
      id: "cliente-teste", nome: "Cliente de exemplo", email: "cliente@example.test",
      ativo: true, estado_conta: "CONVIDADO", idade: 32, revisao: 1,
    }]);
    if (url.startsWith("/api/v1/atendimento/planos?")) return page([plan]);
    if (url.startsWith(historyPath + "?")) return page(entries);
    if (url.endsWith("/biometria")) return Response.json({ cadastrada: false, elegivel: entries.length > 0,
      disponivel: false, atualizada_em: null, pendencia: null });
    if (url === historyPath && options.method === "POST") {
      expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf-demo" });
      writes.push(JSON.parse(String(options.body)));
      const saved: Membership = {
        id: "matricula-teste", cliente_id: "cliente-teste", plano_id: plan.id,
        atendente_id: "atendente-teste", inicio: "2026-12-01", fim: "2026-12-30",
        estado: "ATIVA", situacao: "FUTURA", modalidade_contratada: plan.modalidade,
        limites_snapshot: { limite_acessos: 2, janela_limite: "DIA_CIVIL" },
      };
      entries = [saved];
      return Response.json(saved, { status: 201 });
    }
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", mockFetch);
  mount(paths.attendant);
  fireEvent.click(await screen.findByRole("button", { name: "Ver matrículas de Cliente de exemplo" }));
  fireEvent.change(await screen.findByLabelText("Plano"), { target: { value: plan.id } });
  fireEvent.change(screen.getByLabelText("Início"), { target: { value: "2026-12-01" } });
  expect(screen.getByText(/Válida até 30\/12\/2026, inclusive/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Registrar matrícula" }));
  expect(await screen.findByText("Matrícula registrada até 30/12/2026.")).toBeTruthy();
  const history = await screen.findByRole("list", { name: "Histórico de matrículas" });
  expect(within(history).getByText("Futura · 2 entradas por dia")).toBeTruthy();
  expect(await screen.findByText("Renovar matrícula")).toBeTruthy();
  expect((screen.getByLabelText("Início") as HTMLInputElement).value).toBe("2026-12-31");
  expect(writes).toEqual([{
    solicitacao_id: expect.any(String), plano_id: plan.id, plano_revisao: 1, inicio: "2026-12-01",
  }]);
});

test.each([paths.admin, paths.attendant])("cliente não carrega a tela protegida %s", async (path) => {
  const mockFetch = vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return session("CLIENTE");
    throw new Error("Rota inesperada: " + url);
  });
  vi.stubGlobal("fetch", mockFetch);
  mount(path);
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(mockFetch).toHaveBeenCalledTimes(1);
});
