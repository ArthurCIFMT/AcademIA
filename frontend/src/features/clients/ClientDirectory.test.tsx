import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { ClientDetail } from "./api";

const base = "/api/v1/clientes";
const attendantPath = "/area/atendimento/clientes";
const client: ClientDetail = {
  id: "cd45f050-4b76-43fa-a313-eb0ca1612cd3",
  nome: "Cliente Sintético",
  email: "cliente@example.test",
  data_nascimento: "1990-01-01",
  telefone: null,
  ativo: true,
  estado_conta: "CONVIDADO",
  revisao: 1,
  convite: { estado: "FALHOU", expira_em: "2026-11-11T12:00:00Z" },
};

function session(roles: string[]) {
  return Response.json({
    user_id: "7424b406-dae0-4bda-914b-3e85e120c80d",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
    csrf_token: "csrf-sintetico",
    roles,
  });
}

function mount(path: string) {
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("atendente cadastra, reenvia convite, pesquisa e inativa um cliente", async () => {
  let record: ClientDetail | null = null;
  const request = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return session(["ATENDENTE"]);
    if (url.startsWith(base + "?")) {
      return Response.json({ itens: record ? [record] : [], pagina: 1, limite: 20, total: record ? 1 : 0 });
    }
    if (url === base && options.method === "POST") {
      record = client;
      return Response.json(record, { status: 201 });
    }
    if (url.endsWith("/convite")) {
      record = { ...client, revisao: 2, convite: { estado: "ENVIADO", expira_em: "2026-11-11T12:00:00Z" } };
      return Response.json(record);
    }
    if (url === base + "/" + client.id && options.method === "PUT") {
      record = { ...client, revisao: 3, ativo: false };
      return Response.json(record);
    }
    if (url === base + "/" + client.id) return Response.json(record);
    throw Error("Rota inesperada.");
  });
  vi.stubGlobal("fetch", request);
  mount(attendantPath);
  fireEvent.click(await screen.findByRole("button", { name: "Cadastrar cliente" }));
  fireEvent.change(screen.getByLabelText("Nome", { exact: true }), { target: { value: client.nome } });
  fireEvent.change(screen.getByLabelText("Data de nascimento"), { target: { value: client.data_nascimento } });
  fireEvent.change(screen.getByLabelText("E-mail", { exact: true }), { target: { value: client.email } });
  fireEvent.click(screen.getByRole("button", { name: "Salvar cadastro" }));
  expect(await screen.findByText("Cliente cadastrado.")).toBeTruthy();
  expect(screen.getByText(/Falha no envio do convite/)).toBeTruthy();
  expect(request).toHaveBeenCalledWith(base, expect.objectContaining({
    method: "POST", headers: expect.objectContaining({ "X-CSRF-Token": "csrf-sintetico" }),
    body: JSON.stringify({
      nome: client.nome, data_nascimento: client.data_nascimento, telefone: null,
      email: client.email, vincular_existente: false,
    }),
  }));

  fireEvent.click(screen.getByRole("button", { name: "Reenviar convite" }));
  expect(await screen.findByText(/Convite enviado/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Voltar à lista" }));
  fireEvent.change(screen.getByLabelText("Nome ou e-mail"), { target: { value: client.email } });
  fireEvent.click(screen.getByRole("button", { name: "Pesquisar" }));
  fireEvent.click(await screen.findByRole("button", { name: "Consultar Cliente Sintético" }));
  expect(request).toHaveBeenCalledWith(base + "?pagina=1&busca=cliente%40example.test", expect.anything());
  await screen.findByRole("heading", { name: "Editar cliente" });
  fireEvent.click(screen.getByLabelText("Perfil de cliente ativo"));
  fireEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
  expect(await screen.findByText("Alterações salvas.")).toBeTruthy();
  expect(request).toHaveBeenCalledWith(base + "/" + client.id, expect.objectContaining({
    method: "PUT",
    body: JSON.stringify({
      nome: client.nome, data_nascimento: client.data_nascimento, telefone: null,
      revisao: 2, ativo: false,
    }),
  }));
});

test("cliente recebe acesso negado antes de a tela consultar dados administrativos", async () => {
  const request = vi.fn().mockResolvedValueOnce(session(["CLIENTE"]));
  vi.stubGlobal("fetch", request);
  mount("/area/administracao/clientes");
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request).toHaveBeenCalledTimes(1);
});
