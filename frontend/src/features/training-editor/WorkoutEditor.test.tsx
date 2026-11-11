import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { Context, Workout } from "./api";

const clientId = "cliente-sintetico";
const route = "/area/instrutor/clientes/" + clientId + "/treinos";
const api = "/api/v1/treinos/clientes/" + clientId;
const context: Context = {
  cliente_nome: "Cliente sintético", onboarding: { id: "onboarding-sintetico", numero: 1 },
  avaliacoes: [], equipamentos: [], versao_atual_id: null,
  exercicios: [{ id: "exercicio-sintetico", nome: "Movimento sintético", descricao: "Movimento de teste",
    grupo_muscular: "Grupo sintético", dispensa_equipamento: true, combinacoes_disponiveis: [[]] }],
};
const workout: Workout = {
  id: "rascunho-sintetico", numero: 1, origem: "MANUAL", autor_id: "instrutor-sintetico",
  onboarding_id: "onboarding-sintetico", avaliacao_id: null, versao_base_id: null,
  estado_publicacao: "RASCUNHO", revisao: 1,
  dias: [{ titulo: "Dia A", itens: [{
    exercicio_id: "exercicio-sintetico", equipamento_ids: [], series: 3,
    repeticoes: "8 a 12", carga_kg: "12.50", intervalo_segundos: 60,
    cadencia: "2-0-2", observacoes: null,
    exercicio_snapshot: { nome: "Movimento sintético" },
  }] }],
};

function session(role = "INSTRUTOR") {
  return Response.json({
    user_id: "instrutor-sintetico", roles: [role],
    expires_at: new Date(Date.now() + 60_000).toISOString(), csrf_token: "csrf-sintetico",
  });
}
function history(...items: Workout[]) {
  return Response.json({ itens: items, pagina: 1, limite: 20, total: items.length });
}
function mount(...responses: Array<Response | Error>) {
  const request = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
  for (const response of responses) {
    if (response instanceof Error) request.mockRejectedValueOnce(response);
    else request.mockResolvedValueOnce(response);
  }
  vi.stubGlobal("fetch", request);
  render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>);
  return request;
}
const click = (name: string) => fireEvent.click(screen.getByRole("button", { name }));
const fill = (name: string, value: string) => fireEvent.change(screen.getByLabelText(name), { target: { value } });

afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

test("salva um rascunho por dias e retém a edição em falha de rede", async () => {
  const request = mount(session(), Response.json(context), history(), new Error("offline"),
    Response.json(workout, { status: 201 }), Response.json(context), history(workout));
  await screen.findByText("Cliente sintético");
  click("Novo rascunho manual");
  click("Adicionar dia");
  fill("Título do dia", "Dia A");
  click("Adicionar exercício");
  fill("Exercício", "exercicio-sintetico");
  fill("Séries", "3");
  fill("Repetições", "8 a 12");
  fill("Carga (kg)", "12.50");
  fill("Intervalo (segundos)", "60");
  fill("Cadência", "2-0-2");
  click("Salvar rascunho");
  expect((await screen.findByRole("alert")).textContent).toMatch(/edição continua/);
  expect(screen.getByLabelText<HTMLInputElement>("Repetições").value).toBe("8 a 12");
  click("Salvar rascunho");
  expect(await screen.findByText("Rascunho salvo.")).toBeTruthy();
  const writes = request.mock.calls.filter(([, options]) => options.method);
  expect(writes.map(([url, options]) => [url, options.method])).toEqual([[api + "/rascunhos", "POST"], [api + "/rascunhos", "POST"]]);
  expect(writes[0][1].body).toBe(writes[1][1].body);
  expect(JSON.parse(String(writes[0][1].body))).toMatchObject({
    onboarding_id: context.onboarding?.id, versao_base_id: null, avaliacao_id: null,
    dias: [{ titulo: "Dia A", itens: [{ exercicio_id: "exercicio-sintetico", equipamento_ids: [],
      series: 3, repeticoes: "8 a 12", carga_kg: "12.50", intervalo_segundos: 60, cadencia: "2-0-2" }] }],
  });
  expect(writes[0][1].headers).toMatchObject({ "X-CSRF-Token": "csrf-sintetico" });
});

test("editar conteúdo publicado cria outro rascunho com a base atual", async () => {
  const published: Workout = { ...workout, estado_publicacao: "PUBLICADO" };
  const current = { ...context, versao_atual_id: published.id };
  const request = mount(session(), Response.json(current), history(published), Response.json(published),
    Response.json({ ...workout, id: "nova-versao", numero: 2 }, { status: 201 }),
    Response.json(current), history(published));
  await screen.findByText("Cliente sintético");
  click("Copiar para novo rascunho 1");
  await screen.findByText("Conteúdo copiado da versão 1.");
  expect(screen.getByLabelText<HTMLInputElement>("Repetições").value).toBe("8 a 12");
  fill("Séries", "4");
  click("Salvar rascunho");
  await screen.findByText("Rascunho salvo.");
  const [write] = request.mock.calls.filter(([, options]) => options.method);
  expect(write[0]).toBe(api + "/rascunhos");
  expect(write[1].method).toBe("POST");
  expect(JSON.parse(String(write[1].body))).toMatchObject({ versao_base_id: published.id });
});

test("cliente sem papel de instrutor não abre a manutenção de fichas", async () => {
  const request = mount(session("CLIENTE"));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(request.mock.calls.map(([url]) => url)).toEqual(["/api/v1/auth/session"]);
});
