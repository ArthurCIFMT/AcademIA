import { cleanup, fireEvent, render, screen, waitFor, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { Exercise, Resource } from "./api";

const api = "/api/v1/exercicios";
const route = "/area/instrutor/exercicios";
const first: Resource = { id: "recurso-a", nome: "Recurso A", disponivel: true };
const second: Resource = { id: "recurso-b", nome: "Recurso B", disponivel: true };
const backup: Resource = { id: "recurso-c", nome: "Recurso C", disponivel: true };
const item: Exercise = {
  id: "exercicio-sintetico", nome: "Movimento sintético", descricao: "Descrição de teste",
  grupo_muscular: "Grupo sintético", ativo: true, dispensa_equipamento: false,
  revisao: 1, elegivel: true, combinacoes: [[first, second], [backup]],
};

function session(role = "INSTRUTOR") {
  return Response.json({
    user_id: "conta-sintetica", roles: [role],
    expires_at: new Date(Date.now() + 60_000).toISOString(), csrf_token: "csrf-sintetico",
  });
}

function page(...items: Exercise[]) {
  return Response.json({ itens: items, pagina: 1, limite: 20, total: items.length });
}

function mount(path: string, ...responses: Response[]) {
  const request = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
  for (const response of responses) request.mockResolvedValueOnce(response);
  vi.stubGlobal("fetch", request);
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  return request;
}

function press(name: string) {
  fireEvent.click(screen.getByRole("button", { name }));
}

function fill(label: string, value: string) {
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("instrutor cadastra duas alternativas e recebe a elegibilidade do backend", async () => {
  const request = mount(route, session(), page(), Response.json([first, second, backup]),
    Response.json(item, { status: 201 }), page(item));
  await screen.findByText("Nenhum exercício cadastrado nesta página.");
  press("Cadastrar exercício");
  fill("Nome", item.nome);
  fill("Descrição do movimento", item.descricao);
  fill("Grupo muscular", item.grupo_muscular);
  await screen.findByRole("button", { name: "Adicionar alternativa" });
  await screen.findByText("O exercício fica fora da seleção até receber uma alternativa ou uma dispensa.");
  await waitFor(() => expect((screen.getByRole("button", { name: "Adicionar alternativa" }) as HTMLButtonElement).disabled).toBe(false));
  press("Adicionar alternativa");
  press("Salvar exercício");
  expect(screen.getByRole("alert").textContent).toMatch(/alternativa vazia/);
  const combination = within(screen.getByRole("group", { name: "Alternativa 1" }));
  fireEvent.click(combination.getByLabelText("Recurso A"));
  fireEvent.click(combination.getByLabelText("Recurso B"));
  press("Adicionar alternativa");
  fireEvent.click(within(screen.getByRole("group", { name: "Alternativa 2" })).getByLabelText("Recurso C"));
  press("Salvar exercício");
  expect(await screen.findByText("Disponível para seleção")).toBeTruthy();
  const post = request.mock.calls.find(([, options]) => options.method === "POST");
  expect(post?.[0]).toBe(api);
  expect(post?.[1].headers).toMatchObject({ "X-CSRF-Token": "csrf-sintetico" });
  expect(JSON.parse(String(post?.[1].body))).toEqual({
    nome: item.nome, descricao: item.descricao, grupo_muscular: item.grupo_muscular,
    ativo: true, dispensa_equipamento: false,
    combinacoes: [[first.id, second.id], [backup.id]],
  });
});

test("administrador consulta alternativa indisponível e inativa preservando a referência", async () => {
  const before = { ...item, elegivel: false, combinacoes: [[{ ...first, disponivel: false }]] };
  const after = { ...before, ativo: false, revisao: 2 };
  const request = mount("/area/administracao/exercicios", session("ADMINISTRADOR"), page(before),
    Response.json([]), Response.json(after), page(after));
  expect(await screen.findByText("Recursos indisponíveis ou pendentes")).toBeTruthy();
  press("Editar Movimento sintético");
  expect(screen.getByLabelText("Recurso A (indisponível)")).toBeTruthy();
  fireEvent.click(screen.getByLabelText("Ativo"));
  press("Salvar exercício");
  expect(await screen.findByText("Inativo")).toBeTruthy();
  const write = request.mock.calls.find(([, options]) => options.method === "PUT");
  expect(write?.[0]).toBe(api + "/" + item.id);
  expect(JSON.parse(String(write?.[1].body))).toMatchObject({ ativo: false, revisao: 1, combinacoes: [[first.id]] });
});

test("cliente não consulta a API de manutenção por acesso direto", async () => {
  const request = mount(route, session("CLIENTE"));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request.mock.calls.map(([url]) => url)).toEqual(["/api/v1/auth/session"]);
});
