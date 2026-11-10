import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { StaffDetail } from "./api";

const endpoint = "/api/v1/funcionarios";
const staffPath = "/area/administracao/funcionarios";
const person: StaffDetail = {
  id: "2f749857-dc26-4310-81c0-630677cae6b1",
  email: "instrutor@example.test",
  nome: "Pessoa Sintética",
  cargo: "Instrutor",
  data_admissao: "2026-01-01",
  papeis: ["INSTRUTOR"],
  ativo: true,
  estado_conta: "CONVIDADO",
  revisao: 1,
  convite: { estado: "FALHOU", expira_em: "2026-11-11T12:00:00Z" },
};

function session(roles: string[]) {
  return Response.json({
    user_id: "0dc4dd14-2214-4117-9337-4e98f2b20d26",
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

test("admin cadastra, reenvia após falha, consulta e inativa pelo formulário", async () => {
  let record: StaffDetail | null = null;
  const request = vi.fn(async (url: string, options: RequestInit) => {
    if (url.endsWith("/auth/session")) return session(["ADMINISTRADOR"]);
    if (url === endpoint + "?pagina=1") {
      return Response.json({ itens: record ? [record] : [], pagina: 1, limite: 20, total: record ? 1 : 0 });
    }
    if (url === endpoint && options.method === "POST") {
      record = person;
      return Response.json(record, { status: 201 });
    }
    if (url === endpoint + "/" + person.id + "/convite") {
      record = { ...person, revisao: 2, convite: { estado: "ENVIADO", expira_em: "2026-11-11T12:00:00Z" } };
      return Response.json(record);
    }
    if (url === endpoint + "/" + person.id && options.method === "PUT") {
      record = { ...person, revisao: 3, ativo: false };
      return Response.json(record);
    }
    if (url === endpoint + "/" + person.id) return Response.json(record);
    throw new Error("Rota inesperada.");
  });
  vi.stubGlobal("fetch", request);

  mount(staffPath);
  fireEvent.click(await screen.findByRole("button", { name: "Cadastrar funcionário" }));
  fireEvent.change(screen.getByLabelText("Nome"), { target: { value: person.nome } });
  fireEvent.change(screen.getByLabelText("Cargo"), { target: { value: person.cargo } });
  fireEvent.change(screen.getByLabelText("Data de admissão"), { target: { value: person.data_admissao } });
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: person.email } });
  fireEvent.click(screen.getByLabelText("Instrutor"));
  fireEvent.click(screen.getByRole("button", { name: "Salvar cadastro" }));

  expect(await screen.findByText("Funcionário cadastrado.")).toBeTruthy();
  expect(screen.getByText(/Falha no envio/)).toBeTruthy();
  expect(request).toHaveBeenCalledWith(endpoint, expect.objectContaining({
    method: "POST",
    headers: expect.objectContaining({ "X-CSRF-Token": "csrf-sintetico" }),
    body: JSON.stringify({
      nome: person.nome, cargo: person.cargo, data_admissao: person.data_admissao,
      papeis: person.papeis, email: person.email, vincular_existente: false,
    }),
  }));

  fireEvent.click(screen.getByRole("button", { name: "Reenviar convite" }));
  expect(await screen.findByText(/Enviado à caixa/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Voltar à lista" }));
  fireEvent.click(await screen.findByRole("button", { name: "Consultar Pessoa Sintética" }));
  await screen.findByRole("heading", { name: "Editar funcionário" });
  fireEvent.click(screen.getByLabelText("Perfil de funcionário ativo"));
  fireEvent.click(screen.getByRole("button", { name: "Salvar alterações" }));
  expect(await screen.findByText("Alterações salvas.")).toBeTruthy();
  expect(request).toHaveBeenCalledWith(endpoint + "/" + person.id, expect.objectContaining({
    method: "PUT",
    body: JSON.stringify({
      nome: person.nome, cargo: person.cargo, data_admissao: person.data_admissao,
      papeis: person.papeis, ativo: false, revisao: 2,
    }),
  }));
  await waitFor(() => expect(screen.queryByRole("button", { name: "Reenviar convite" })).toBeNull());
});

test("rota direta administrativa bloqueia atendente antes de consultar a lista", async () => {
  const request = vi.fn().mockResolvedValueOnce(session(["ATENDENTE"]));
  vi.stubGlobal("fetch", request);
  mount(staffPath);
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request).toHaveBeenCalledTimes(1);
});

test("link de primeiro acesso define senha pelo endpoint correto", async () => {
  const token = "x".repeat(43);
  const password = "senha-sintetica";
  const request = vi.fn().mockResolvedValueOnce(new Response(null, { status: 204 }));
  vi.stubGlobal("fetch", request);
  mount("/primeiro-acesso#token=" + token);
  fireEvent.change(screen.getByLabelText("Nova senha", { exact: true }), { target: { value: password } });
  fireEvent.change(screen.getByLabelText("Confirme a nova senha"), { target: { value: password } });
  fireEvent.click(screen.getByRole("button", { name: "Definir senha" }));
  expect(await screen.findByText("Senha definida. Entre com sua senha.")).toBeTruthy();
  expect(request).toHaveBeenCalledWith("/api/v1/auth/first-access", expect.objectContaining({
    body: JSON.stringify({ token, senha: password }),
  }));
});
