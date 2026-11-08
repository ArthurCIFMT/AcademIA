import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../src/App";
import type { Role } from "../../src/lib/api/auth";

const base = "/api/v1/auth/";

function session(roles: Role[] = ["CLIENTE"], expiresAt = new Date(Date.now() + 60_000).toISOString()) {
  return Response.json({
    user_id: "9b8aaab5-ea91-418e-8419-53745cf99d98",
    expires_at: expiresAt,
    csrf_token: "csrf-sintetico",
    roles,
  });
}

function mount(path: string) {
  return render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
}

function mockRequests(...responses: Response[]) {
  const fetchMock = vi.fn();
  for (const response of responses) fetchMock.mockResolvedValueOnce(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function fillCredentials() {
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "cliente@example.test" } });
  fireEvent.change(screen.getByLabelText("Senha"), { target: { value: "senha-sintetica" } });
  fireEvent.click(screen.getByRole("button", { name: "Entrar" }));
}

afterEach(() => {
  cleanup();
  vi.useRealTimers();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

test("restaura antes de mostrar uma rota direta e exige login se não houver sessão", async () => {
  let restore!: (response: Response) => void;
  const response = new Promise<Response>((resolve) => { restore = resolve; });
  const fetchMock = vi.fn().mockReturnValue(response);
  vi.stubGlobal("fetch", fetchMock);
  mount("/area/cliente");

  expect(screen.getByRole("status").textContent).toBe("Verificando sessão…");
  expect(screen.queryByRole("heading", { name: "Área do cliente" })).toBeNull();
  restore(new Response(null, { status: 401 }));

  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledTimes(1);
  expect(fetchMock).toHaveBeenCalledWith(base + "session", expect.objectContaining({
    credentials: "same-origin",
    cache: "no-store",
  }));
});

test("envia login em JSON e abre somente áreas dos papéis retornados", async () => {
  const fetchMock = mockRequests(new Response(null, { status: 401 }), session(["CLIENTE", "ATENDENTE"]));
  mount("/login");
  await screen.findByRole("heading", { name: "Entrar" });
  fillCredentials();

  expect(await screen.findByRole("heading", { name: "Área de atendimento" })).toBeTruthy();
  expect(screen.queryByRole("link", { name: "Administração" })).toBeNull();
  fireEvent.click(screen.getByRole("link", { name: "Cliente" }));
  expect(await screen.findByRole("heading", { name: "Área do cliente" })).toBeTruthy();
  expect(fetchMock).toHaveBeenLastCalledWith(base + "login", expect.objectContaining({
    method: "POST",
    credentials: "same-origin",
    headers: { Accept: "application/json", "Content-Type": "application/json" },
    body: JSON.stringify({ email: "cliente@example.test", senha: "senha-sintetica" }),
  }));
});

test("rejeita credenciais inválidas sem abrir sessão ou repetir a requisição", async () => {
  const fetchMock = mockRequests(new Response(null, { status: 401 }), new Response(null, { status: 401 }));
  mount("/login");
  await screen.findByRole("heading", { name: "Entrar" });
  fillCredentials();

  expect((await screen.findByRole("alert")).textContent).toBe("E-mail ou senha inválidos.");
  expect((screen.getByLabelText("Senha") as HTMLInputElement).value).toBe("");
  expect(screen.queryByRole("button", { name: "Sair" })).toBeNull();
  expect(fetchMock).toHaveBeenCalledTimes(2);
});

test("exibe acesso negado em rota cujo papel não consta na sessão", async () => {
  mockRequests(session());
  mount("/area/administracao");

  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Área administrativa" })).toBeNull();
  expect(screen.getByRole("link", { name: "Cliente" })).toBeTruthy();
});

test("exibe 403 retornado pela API da sessão sem redirecionar nem repetir a consulta", async () => {
  const fetchMock = mockRequests(new Response(null, { status: 403 }));
  mount("/area/cliente");

  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(screen.getByRole("link", { name: "Entrar novamente" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Área do cliente" })).toBeNull();
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("oculta a área imediatamente no logout e confirma saída com CSRF e 204", async () => {
  const fetchMock = mockRequests(session(), new Response(null, { status: 204 }));
  mount("/area/cliente");
  await screen.findByRole("heading", { name: "Área do cliente" });
  fireEvent.click(screen.getByRole("button", { name: "Sair" }));

  expect(screen.queryByRole("heading", { name: "Área do cliente" })).toBeNull();
  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeTruthy();
  expect(fetchMock).toHaveBeenLastCalledWith(base + "logout", expect.objectContaining({
    method: "POST",
    headers: { Accept: "application/json", "X-CSRF-Token": "csrf-sintetico" },
  }));
});

test("permite confirmar o logout novamente sem voltar a exibir a área", async () => {
  mockRequests(session(), new Response(null, { status: 403 }), new Response(null, { status: 204 }));
  mount("/area/cliente");
  await screen.findByRole("heading", { name: "Área do cliente" });
  fireEvent.click(screen.getByRole("button", { name: "Sair" }));

  expect((await screen.findByRole("alert")).textContent).toBe("Não foi possível confirmar a saída.");
  expect(screen.queryByRole("heading", { name: "Área do cliente" })).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeTruthy();
});

test("remove a área ao atingir o prazo absoluto da sessão sem consultar a API em loop", async () => {
  const fetchMock = mockRequests(session());
  vi.useFakeTimers();
  mount("/area/cliente");
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  expect(screen.getByRole("heading", { name: "Área do cliente" })).toBeTruthy();

  await act(async () => { await vi.advanceTimersByTimeAsync(60_001); });
  expect(screen.queryByRole("heading", { name: "Área do cliente" })).toBeNull();
  expect(screen.getByRole("heading", { name: "Entrar" })).toBeTruthy();
  expect(screen.getByRole("status").textContent).toContain("Sua sessão expirou");
  expect(fetchMock).toHaveBeenCalledTimes(1);
});

test("revalida ao retornar à aba e remove a área ao receber 401", async () => {
  const fetchMock = mockRequests(session(), new Response(null, { status: 401 }));
  mount("/area/cliente");
  await screen.findByRole("heading", { name: "Área do cliente" });

  fireEvent.focus(window);
  await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
  expect(await screen.findByRole("heading", { name: "Entrar" })).toBeTruthy();
  expect(screen.queryByRole("heading", { name: "Área do cliente" })).toBeNull();
});
