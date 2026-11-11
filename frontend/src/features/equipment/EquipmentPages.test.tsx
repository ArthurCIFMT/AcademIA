import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { InventoryItem } from "./api";

const inventory = "/api/v1/admin/equipamentos";
const publicApi = "/api/v1/equipamentos";
const route = "/area/administracao/equipamentos";
const id = "9c38ef08-775e-4780-a383-39f85fb1bd77";
const item: InventoryItem = {
  id, nome: "Remo", categoria: "Cardio", descricao: "Uso na área de cardio.",
  ativo: true, operacional: true, revisao: 1, imagem_url: publicApi + "/" + id + "/imagem",
};

function session(role = "ADMINISTRADOR") {
  return Response.json({
    user_id: "conta-sintetica", roles: [role],
    expires_at: new Date(Date.now() + 60_000).toISOString(), csrf_token: "csrf-sintetico",
  });
}

function page<T>(...items: T[]) {
  return Response.json({ itens: items, pagina: 1, limite: 20, total: items.length });
}

function mount(path: string, ...responses: Response[]) {
  const request = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
  for (const response of responses) request.mockResolvedValueOnce(response);
  vi.stubGlobal("fetch", request);
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  return request;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("o visitante consulta nome, descrição e imagem sem pedir uma sessão", async () => {
  const request = mount("/equipamentos", page(item));
  const image = await screen.findByRole("img", { name: "Foto de Remo" });
  expect(image.getAttribute("src")).toBe(item.imagem_url);
  expect(screen.getByRole("heading", { name: item.nome })).toBeTruthy();
  expect(screen.getByText("Uso na área de cardio.")).toBeTruthy();
  expect(request.mock.calls.map(([url]) => url)).toEqual([publicApi + "?pagina=1"]);
});

test("o administrador cadastra com imagem e pode inativar o mesmo equipamento", async () => {
  const saved = { ...item, imagem_url: inventory + "/" + id + "/imagem" };
  const inactive = { ...saved, ativo: false, revisao: 2 };
  const request = mount(route, session(), page(), Response.json(saved, { status: 201 }), page(saved),
    Response.json(inactive), page(inactive));
  await screen.findByText("Nenhum equipamento cadastrado nesta página.");
  fireEvent.click(screen.getByRole("button", { name: "Cadastrar equipamento" }));
  fireEvent.change(screen.getByLabelText("Nome"), { target: { value: "Remo" } });
  fireEvent.change(screen.getByLabelText("Categoria"), { target: { value: "Cardio" } });
  fireEvent.change(screen.getByLabelText("Descrição"), { target: { value: item.descricao } });
  fireEvent.change(screen.getByLabelText("Foto (JPG ou PNG)"), {
    target: { files: [new File(["test"], "demo.png", { type: "image/png" })] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Salvar equipamento" }));
  fireEvent.click(await screen.findByRole("button", { name: "Editar Remo" }));
  fireEvent.click(screen.getByLabelText("Ativo"));
  fireEvent.click(screen.getByRole("button", { name: "Salvar equipamento" }));
  expect(await screen.findByText("Inativo · Operacional")).toBeTruthy();

  const writes = request.mock.calls.filter(([, options]) => options.method);
  expect(writes.map(([url, options]) => [url, options.method])).toEqual([
    [inventory, "POST"], [inventory + "/" + id, "PUT"],
  ]);
  expect(JSON.parse(String(writes[0][1].body))).toEqual({
    nome: "Remo", categoria: "Cardio", descricao: item.descricao,
    ativo: true, operacional: true, imagem_base64: "dGVzdA==", solicitacao_id: expect.any(String),
  });
  expect(JSON.parse(String(writes[1][1].body))).toEqual({
    nome: "Remo", categoria: "Cardio", descricao: item.descricao,
    ativo: false, operacional: true, revisao: 1,
  });
  expect(writes[0][1].headers).toMatchObject({ "X-CSRF-Token": "csrf-sintetico" });
});

test("um atendente não abre a tela administrativa por acesso direto", async () => {
  const request = mount(route, session("ATENDENTE"));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request.mock.calls.map(([url]) => url)).toEqual(["/api/v1/auth/session"]);
});
