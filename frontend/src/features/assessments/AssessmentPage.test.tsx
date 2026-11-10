import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { AssessmentHistory } from "./api";

const clientId = "36bf97bf-ac60-4b35-b99a-4fa45a1d199f";
const area = "/area/instrutor/clientes";
const api = "/api/v1/onboarding/clientes/" + clientId + "/avaliacoes";
const view: AssessmentHistory = {
  cliente_nome: "Cliente sintético",
  snapshot: { id: "snapshot-sintetico", numero: 1, dados: { altura_cm: 173 } },
  historico: { itens: [], pagina: 1, limite: 20, total: 0 },
};
const entry = {
  id: "avaliacao-sintetica", onboarding_id: "snapshot-sintetico",
  instrutor_id: "instrutor-sintetico", instrutor_nome: "Instrutor sintético",
  registrado_em: "2026-11-10T12:00:00Z", observacao: "Observação sintética",
};

function session(role = "INSTRUTOR") {
  return Response.json({
    user_id: "conta-sintetica", roles: [role], expires_at: new Date(Date.now() + 60_000).toISOString(),
    csrf_token: "csrf-sintetico",
  });
}

function mount(path: string, ...replies: Array<Response | Error>) {
  const request = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
  for (const reply of replies) {
    if (reply instanceof Error) request.mockRejectedValueOnce(reply);
    else request.mockResolvedValueOnce(reply);
  }
  vi.stubGlobal("fetch", request);
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  return request;
}

function fill(text: string) {
  fireEvent.change(screen.getByLabelText("Observação da avaliação"), { target: { value: text } });
}
const submit = () => fireEvent.click(screen.getByRole("button", { name: "Registrar avaliação" }));

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("abre pelo cliente designado, preserva a observação em falha e repete com a mesma chave", async () => {
  const assigned = Response.json({
    itens: [{ id: clientId, nome: view.cliente_nome, inicio: entry.registrado_em }],
    pagina: 1, limite: 20, total: 1,
  });
  const saved = { ...view, historico: { ...view.historico, itens: [entry], total: 1 } };
  const request = mount(area, session(), assigned, Response.json(view), new Error("offline"),
    Response.json(entry, { status: 201 }), Response.json(saved));
  fireEvent.click(await screen.findByRole("link", { name: "Avaliações de Cliente sintético" }));
  await screen.findByText("Onboarding concluído · versão 1");
  fill("   ");
  submit();
  expect(screen.getByRole("alert").textContent).toMatch(/Preencha/);
  expect(request.mock.calls.every(([, options]) => options.method === undefined)).toBe(true);
  fill(entry.observacao);
  submit();
  expect((await screen.findByRole("alert")).textContent).toMatch(/continua nesta tela/);
  expect(screen.getByLabelText<HTMLTextAreaElement>("Observação da avaliação").value).toBe(entry.observacao);
  submit();
  expect(await screen.findByText("Avaliação registrada.")).toBeTruthy();
  expect(screen.getByText(entry.instrutor_nome)).toBeTruthy();
  expect(screen.getByText(entry.observacao)).toBeTruthy();

  const posts = request.mock.calls.filter(([, options]) => options.method === "POST");
  expect(posts.map(([url]) => url)).toEqual([api, api]);
  const payload = JSON.parse(String(posts[0][1].body));
  expect(payload).toEqual({
    onboarding_id: view.snapshot?.id, observacao: entry.observacao, solicitacao_id: expect.any(String),
  });
  expect(posts[0][1].headers).toMatchObject({ "X-CSRF-Token": "csrf-sintetico" });
  expect(posts[1][1].body).toBe(posts[0][1].body);
});

test("remove o conteúdo protegido se o vínculo for revogado durante a edição", async () => {
  mount(area + "/" + clientId + "/avaliacoes", session(), Response.json(view), new Response(null, { status: 403 }));
  await screen.findByLabelText("Observação da avaliação");
  fill("Texto que deve sair da tela");
  submit();
  expect((await screen.findByRole("alert")).textContent).toMatch(/acesso.*não está disponível/);
  expect(screen.queryByText(view.cliente_nome)).toBeNull();
  expect(screen.queryByLabelText("Observação da avaliação")).toBeNull();
});

test("atendente não consulta a API profissional por acesso direto à rota", async () => {
  const request = mount(area + "/" + clientId + "/avaliacoes", session("ATENDENTE"));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request).toHaveBeenCalledTimes(1);
  expect(request.mock.calls[0][0]).toBe("/api/v1/auth/session");
});

test("onboarding ainda incompleto permite ver o histórico sem iniciar nova avaliação", async () => {
  mount(area + "/" + clientId + "/avaliacoes", session(), Response.json({ ...view, snapshot: null }));
  expect(await screen.findByText("O cliente ainda não concluiu o onboarding.")).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Histórico de avaliações" })).toBeTruthy();
  expect(screen.queryByLabelText("Observação da avaliação")).toBeNull();
});
