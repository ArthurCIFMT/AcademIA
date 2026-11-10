import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";

const endpoint = "/api/v1/notificacoes/pendentes";

function session(roles: string[]) {
  return Response.json({
    user_id: "0dc4dd14-2214-4117-9337-4e98f2b20d26",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
    csrf_token: "csrf-sintetico",
    roles,
  });
}

function openArea(path: string, ...responses: Response[]) {
  const fetchMock = vi.fn();
  responses.forEach((response) => fetchMock.mockResolvedValueOnce(response));
  vi.stubGlobal("fetch", fetchMock);
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  return fetchMock;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("mostra a pendência no espaço autorizado e a oculta no logout", async () => {
  const fetchMock = openArea("/area/instrutor", session(["INSTRUTOR"]), Response.json([{
    id: "2f749857-dc26-4310-81c0-630677cae6b1",
    tipo: "TREINO_PARA_AVALIAR",
    criada_em: "2026-11-07T12:00:00Z",
  }]), new Response(null, { status: 204 }));

  expect(await screen.findByText("Treino para avaliar", { exact: false })).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledWith(endpoint, expect.objectContaining({
    credentials: "same-origin",
    cache: "no-store",
  }));
  fireEvent.click(screen.getByRole("button", { name: "Sair" }));
  expect(screen.queryByRole("heading", { name: "Avisos pendentes" })).toBeNull();
  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeTruthy();
});

test("trata lista vazia após repetir uma falha técnica", async () => {
  openArea("/area/administracao", session(["ADMINISTRADOR"]),
    new Response(null, { status: 503 }), Response.json([]));

  expect((await screen.findByRole("alert")).textContent).toContain("carregar os avisos");
  fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
  expect(await screen.findByText("Nenhum aviso pendente.")).toBeTruthy();
});

test("mostra acesso recusado e evita repetição automática", async () => {
  const fetchMock = openArea("/area/instrutor", session(["INSTRUTOR"]),
    new Response(null, { status: 403 }));

  expect((await screen.findByRole("alert")).textContent).toContain("Acesso aos avisos indisponível");
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

test("não consulta pendências administrativas para uma conta de cliente", async () => {
  const fetchMock = openArea("/area/cliente", session(["CLIENTE"]));
  expect(await screen.findByRole("heading", { name: "Área do cliente" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Avisos pendentes" })).toBeNull();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});
