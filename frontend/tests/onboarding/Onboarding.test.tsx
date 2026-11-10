import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { StrictMode } from "react";
import { BrowserRouter, MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, beforeEach, expect, test, vi } from "vitest";

import { App } from "../../src/App";
import type { Draft } from "../../src/features/onboarding/api";
import type { FormData } from "../../src/features/onboarding/form";

const invite = "/api/v1/onboarding/convite";
const own = "/api/v1/onboarding/meu";
const token = "A".repeat(43);
const path = "/onboarding/convite";
const valid: FormData = {
  altura_cm: 170, peso_kg: 74.2, objetivo_principal: "FORCA", experiencia: "INICIANTE",
  nivel_atividade: "LEVE", dias_semana: 3, duracao_sessao_min: 60, possui_condicoes_saude: "NAO",
  condicoes_saude: [], usa_medicamentos: "NAO_SEI", medicamentos: [], possui_dor_lesao_limitacao: "NAO",
  limitacoes: [], restricao_exercicio_declarada: "NAO", evento_saude_importante_recente: "NAO", observacoes: "",
};
const draft = { id: "rascunho-sintetico", numero: 1, revisao: 2, dados: valid } satisfies Draft;
const snapshot = { ...draft, concluido_em: "2026-11-10T12:00:00Z" };

let originalLocks: PropertyDescriptor | undefined;
beforeEach(() => {
  originalLocks = Object.getOwnPropertyDescriptor(navigator, "locks");
  Object.defineProperty(navigator, "locks", {
    configurable: true, value: { request: async (_name: string, run: () => Promise<unknown>) => run() },
  });
});
afterEach(() => {
  cleanup();
  if (originalLocks) Object.defineProperty(navigator, "locks", originalLocks);
  else Reflect.deleteProperty(navigator, "locks");
  vi.unstubAllGlobals();
});

function LocationIndicator() {
  const { pathname, hash } = useLocation();
  return <output data-testid="location">{pathname}{hash}</output>;
}

function mount(url: string, ...responses: Array<Response | Error>) {
  const request = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
  for (const response of responses) {
    if (response instanceof Error) request.mockRejectedValueOnce(response);
    else request.mockResolvedValueOnce(response);
  }
  vi.stubGlobal("fetch", request);
  render(<StrictMode><MemoryRouter initialEntries={[url]}><App /><LocationIndicator /></MemoryRouter></StrictMode>);
  return request;
}

const status = (code: number) => new Response(null, { status: code });
const change = (label: string, value: string) =>
  fireEvent.change(screen.getByLabelText(label), { target: { value } });
const click = (name: string) => fireEvent.click(screen.getByRole("button", { name }));
const session = (role = "CLIENTE") => Response.json({
  user_id: "conta-sintetica", roles: [role], expires_at: new Date(Date.now() + 60_000).toISOString(),
  csrf_token: "csrf-sintetico",
});

test("troca o fragmento uma vez e abre só o rascunho do convite", async () => {
  const request = mount(path + "#token=" + token, status(200), Response.json(draft));
  expect(screen.getByTestId("location").textContent).toBe(path);
  expect(request).not.toHaveBeenCalled();
  click("Abrir formulário");

  const input = await screen.findByLabelText<HTMLInputElement>("Altura (cm)");
  expect(input.value).toBe("170");
  expect(request.mock.calls.map(([url]) => url)).toEqual([invite + "/troca", invite + "/rascunho"]);
  expect(request.mock.calls[0][1]).toMatchObject({
    method: "POST", body: JSON.stringify({ token }), cache: "no-store",
  });
});

test("link recusado não usa uma sessão restrita anterior", async () => {
  const request = mount(path + "#token=" + token, status(401));
  click("Abrir formulário");
  expect((await screen.findByRole("alert")).textContent).toMatch(/expirou/);
  expect(screen.queryByLabelText("Altura (cm)")).toBeNull();
  expect(request.mock.calls.map(([url]) => url)).toEqual([invite + "/troca"]);
});

test("reabre, impede conclusão incompleta e mantém os campos após falha de rede", async () => {
  const incomplete = { ...draft, dados: { ...valid, usa_medicamentos: null } };
  const saved = { ...draft, revisao: 3, dados: {
    ...valid, usa_medicamentos: "SIM", medicamentos: [{ nome: "Medicação sintética", observacao: "" }],
  } };
  // StrictMode cancela e remonta o GET inicial.
  const request = mount(path, Response.json(incomplete), Response.json(incomplete),
    Response.json(incomplete), new Error("offline"), Response.json(incomplete), Response.json(saved),
    Response.json(saved), status(204));
  const answer = await screen.findByLabelText<HTMLSelectElement>("Usa medicamentos?");
  expect(answer.value).toBe("");
  const initialRequests = request.mock.calls.length;
  click("Concluir onboarding");
  expect(screen.getByRole("alert").textContent).toMatch(/Usa medicamentos/);
  expect(request.mock.calls).toHaveLength(initialRequests);
  change("Usa medicamentos?", "SIM");
  click("Concluir onboarding");
  expect(screen.getByRole("alert").textContent).toMatch(/pelo menos um registro/);
  click("Adicionar medicamento");
  change("Nome do medicamento", "Medicação sintética");
  click("Salvar rascunho");

  expect((await screen.findByRole("alert")).textContent).toMatch(/continuam nesta tela/);
  expect(screen.getByLabelText<HTMLInputElement>("Nome do medicamento").value).toBe("Medicação sintética");
  click("Concluir onboarding");
  expect(await screen.findByText("Onboarding concluído.")).toBeTruthy();
  const writes = request.mock.calls.filter(([, options]) => options.method);
  expect(writes.map(([url, options]) => [url, options.method])).toEqual([
    [invite + "/rascunho", "PATCH"], [invite + "/rascunho", "PATCH"], [invite + "/conclusao", "POST"],
  ]);
  expect(JSON.parse(String(writes[1][1].body))).toEqual({ revisao: 2, dados: saved.dados });
  expect(JSON.parse(String(writes[2][1].body))).toEqual({ revisao: 3 });
});

test("uma aba antiga não envia o rascunho se outro convite trocou o cookie", async () => {
  const request = mount(path, Response.json(draft), Response.json(draft),
    Response.json({ ...draft, id: "outro-rascunho", dados: {} }));
  await screen.findByLabelText("Altura (cm)");
  click("Salvar rascunho");
  expect((await screen.findByRole("alert")).textContent).toMatch(/Outro convite/);
  expect(request.mock.calls.every(([, options]) => options.method === undefined)).toBe(true);
});

test("exibe a versão concluída e só atualiza com confirmação e revisão do rascunho", async () => {
  const saved = { ...draft, numero: 2, revisao: 1, dados: { ...valid, peso_kg: 76.3 } };
  const next = { ...saved, concluido_em: snapshot.concluido_em };
  const request = mount("/area/cliente/onboarding", session(), session(),
    Response.json({ rascunho: null, concluido: snapshot }),
    Response.json({ rascunho: null, concluido: snapshot }), Response.json(saved), Response.json(next));
  expect(await screen.findByText(/Versão 1 concluída/)).toBeTruthy();
  expect(screen.getByText("Não sei")).toBeTruthy();
  click("Atualizar meus dados");
  change("Peso (kg)", "76.3");
  click("Salvar rascunho");
  expect(await screen.findByText("Rascunho salvo.")).toBeTruthy();
  const last = request.mock.calls.at(-1);
  expect(last?.[0]).toBe(own + "/rascunho");
  expect(JSON.parse(String(last?.[1].body))).toEqual({ versao_base: snapshot.id, revisao: null, dados: saved.dados });

  click("Revisar atualização");
  expect(request.mock.calls.at(-1)).toEqual(last);
  click("Voltar à edição");
  expect(screen.getByLabelText<HTMLInputElement>("Peso (kg)").value).toBe("76.3");
  click("Revisar atualização");
  click("Confirmar nova versão");
  expect(await screen.findByText(/Versão 2 concluída/)).toBeTruthy();
  expect(request).toHaveBeenLastCalledWith(own + "/atualizacoes", expect.objectContaining({
    method: "POST",
    headers: expect.objectContaining({ "X-CSRF-Token": "csrf-sintetico" }),
  }));
  expect(JSON.parse(String(request.mock.calls.at(-1)?.[1].body))).toEqual({
    versao_base: snapshot.id, revisao: 1, dados: saved.dados, confirmado: true,
  });
});

test("outro papel não consulta dados de saúde por uma rota direta do cliente", async () => {
  const request = mount("/area/cliente/onboarding", session("ATENDENTE"), session("ATENDENTE"));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request.mock.calls.every(([url]) => url === "/api/v1/auth/session")).toBe(true);
});


test("uma falha ao revalidar no foco mantém a edição do cliente", async () => {
  const ownResult = { rascunho: draft, concluido: null };
  const request = mount("/area/cliente/onboarding", session(), session(),
    Response.json(ownResult), Response.json(ownResult), new Error("offline"));
  await screen.findByLabelText("Altura (cm)");
  change("Altura (cm)", "171.6");
  fireEvent.focus(window);
  await waitFor(() => expect(request.mock.calls.filter(([url]) => url.endsWith("/auth/session"))).toHaveLength(3));
  expect(screen.getByLabelText<HTMLInputElement>("Altura (cm)").value).toBe("171.6");
});


test("outro fragmento inicia nova tentativa mesmo se o histórico reutilizar a chave", async () => {
  const original = { url: window.location.href, state: window.history.state };
  const request = vi.fn()
    .mockResolvedValueOnce(status(401))
    .mockResolvedValueOnce(status(200))
    .mockResolvedValueOnce(Response.json(draft));
  vi.stubGlobal("fetch", request);

  try {
    const reusedState = { key: "same-browser-key" };
    window.history.replaceState(reusedState, "", path + "#token=" + token);
    render(<BrowserRouter><App /></BrowserRouter>);
    click("Abrir formulário");
    expect((await screen.findByRole("alert")).textContent).toMatch(/expirou/);

    const replacement = "B".repeat(43);
    window.history.replaceState(reusedState, "", path + "#token=" + replacement);
    fireEvent.popState(window);
    click("Abrir formulário");
    expect(await screen.findByLabelText("Altura (cm)")).toBeTruthy();
    expect(request.mock.calls[1][1].body).toBe(JSON.stringify({ token: replacement }));
  } finally {
    cleanup();
    window.history.replaceState(original.state, "", original.url);
  }
});
