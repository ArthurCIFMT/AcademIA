import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "../../App";
import { sampleContext } from "../ai-training/fixtures";
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test.each(["ACEITO", "REJEITADO"] as const)("instrutor consulta contexto e registra %s sem republicar", async (decision) => {
  const context = structuredClone(sampleContext);
  context.contexto.pendencias = ["ONBOARDING_ATUALIZADO"];
  context.contexto.aviso = { instrutor_designado_id: "instructor", interno_registrado: true, email_estado: "FALHOU", email_tentativas: 2 };
  const fetcher = vi.fn(async (url: string, init: RequestInit) => {
    if (url.endsWith("/auth/session")) return Response.json({ user_id: "instructor", roles: ["INSTRUTOR"], csrf_token: "csrf", expires_at: new Date(Date.now()+60000).toISOString() });
    if (url.endsWith("/contexto")) return Response.json(context);
    if (url.endsWith("/aviso")) return Response.json({ estado: "ENVIADO", tentativas: 3 });
    if (init.method === "POST") return Response.json({ ...context.contexto.treino, parecer: { estado: decision, motivo: "Rever carga", instrutor_id: "instructor", criado_em: "2026-11-11T12:00:00Z" } });
    return Response.json(context.contexto.treino);
  });
  vi.stubGlobal("fetch", fetcher);
  render(<MemoryRouter initialEntries={["/area/instrutor/clientes/client/treinos/version/revisao"]}><App /></MemoryRouter>);
  await screen.findByText(/O onboarding foi atualizado/);
  expect(screen.getByText(/Aviso por e-mail · FALHOU/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Tentar envio do aviso" }));
  await screen.findByText(/Aviso por e-mail · ENVIADO/);
  fireEvent.change(screen.getByLabelText("Decisão"), { target: { value: decision } });
  fireEvent.change(screen.getByLabelText("Motivo do parecer"), { target: { value: "Rever carga" } });
  fireEvent.click(screen.getByRole("button", { name: "Registrar parecer" }));
  await screen.findByText("Parecer " + decision);
  expect(screen.getByText("Movimento sintético")).toBeTruthy();
  await waitFor(() => {
    const writes = fetcher.mock.calls.filter(([, init]) => init.method === "POST");
    expect(writes.map(([url]) => url.split("/").at(-1))).toEqual(["aviso", "parecer"]);
    expect(JSON.parse(String(writes[0][1].body))).toEqual({ tentativa_anterior: 2 });
  });
});
