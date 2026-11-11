import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import { downloadTraining, type History, type OpinionState, type Workout } from "./api";

const route = "/area/cliente/treinos";
const root = "/api/v1/treinos/clientes/cliente/publicadas";
const publishedAt = "2026-11-11T10:00:00Z";
const summary = { id: "versao-2", numero: 2, origem: "MANUAL" as const, autor_id: "instrutor",
  publicada_em: publishedAt, vigente: true, parecer_estado: "PENDENTE" as const };
const history: History = { schema_version: 1, versao_vigente_id: summary.id, itens: [summary] };
const workout: Workout = {
  schema_version: 1, consultado_em: publishedAt,
  ficha: { ...summary, dias: [{ titulo: "Dia A", itens: [{
    exercicio_id: "exercicio", equipamento_ids: ["equipamento"], series: 3, repeticoes: "8 a 12",
    carga_kg: "12.50", intervalo_segundos: 60, cadencia: "2-0-2", observacoes: "Prescrição sintética",
    exercicio_snapshot: { nome: "Movimento sintético", descricao: "Descrição do movimento",
      grupo_muscular: "Grupo", dispensa_equipamento: false },
  }] }, { titulo: "Dia B", itens: [] }] },
  parecer: { estado: "PENDENTE", motivo: null, instrutor_id: null, criado_em: null },
  equipamentos: [{ id: "equipamento", nome: "Recurso sintético", disponivel: false }],
};
function session(role = "CLIENTE") {
  return Response.json({ user_id: "cliente", roles: [role], csrf_token: "csrf-sintetico",
    expires_at: new Date(Date.now() + 60_000).toISOString() });
}
function mount(...responses: Array<Response | Error>) {
  const request = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
  responses.forEach((response) => response instanceof Error
    ? request.mockRejectedValueOnce(response) : request.mockResolvedValueOnce(response));
  vi.stubGlobal("fetch", request);
  render(<MemoryRouter initialEntries={[route]}><App /></MemoryRouter>);
  return request;
}
const click = (name: string) => fireEvent.click(screen.getByRole("button", { name }));
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.restoreAllMocks(); });

test("cliente sem ficha recebe estado vazio; falha de rede permite nova consulta", async () => {
  const empty = { schema_version: 1, versao_vigente_id: null, itens: [] };
  mount(session(), new Error("offline"), Response.json(empty));
  await screen.findByRole("alert");
  click("Tentar novamente");
  await screen.findByText("Você ainda não possui uma ficha publicada.");
  expect(screen.queryByRole("button", { name: "Exportar ficha em JSON" })).toBeNull();
});

test.each<OpinionState>(["PENDENTE", "ACEITO", "REJEITADO"])("exibe dias e prescrição com parecer %s sem ocultar ficha", async (state) => {
  mount(session(), Response.json(history), Response.json({ ...workout,
    parecer: { ...workout.parecer, estado: state, motivo: state === "REJEITADO" ? "Motivo sintético" : null } }));
  await screen.findByText("Movimento sintético");
  expect(screen.getByText("Dia A")).toBeTruthy();
  expect(screen.getByText("Dia B")).toBeTruthy();
  expect(screen.getByText("12,50 kg")).toBeTruthy();
  expect(screen.getByText("60 segundos")).toBeTruthy();
  expect(screen.getByText("2-0-2")).toBeTruthy();
  expect(screen.getByText("Observações · Prescrição sintética")).toBeTruthy();
  expect(screen.getByText("Identificação do autor · instrutor")).toBeTruthy();
  expect(screen.getByRole("note").textContent).toMatch(/equipamento indisponível/);
  expect(screen.getByRole("button", { name: "Exportar ficha em JSON" })).toBeTruthy();
  if (state === "REJEITADO") expect(screen.getByText("Motivo · Motivo sintético")).toBeTruthy();
});

test("histórico recarrega versão escolhida e retira conteúdo que deixou de estar disponível", async () => {
  const older = { ...summary, id: "versao-1", numero: 1, vigente: false };
  const versions = { ...history, itens: [summary, older] };
  const request = mount(session(), Response.json(versions), Response.json(workout),
    Response.json(versions), Response.json({ ...workout, ficha: { ...workout.ficha, ...older,
      dias: [{ titulo: "Treino histórico", itens: [] }] } }), Response.json(history));
  await screen.findByText("Movimento sintético");
  fireEvent.change(screen.getByLabelText("Versão da ficha"), { target: { value: older.id } });
  await screen.findByText("Treino histórico");
  click("Atualizar fichas");
  await screen.findByText("A versão selecionada deixou de estar disponível.");
  expect(screen.queryByText("Treino histórico")).toBeNull();
  expect(screen.queryByRole("button", { name: "Exportar ficha em JSON" })).toBeNull();
  expect(request.mock.calls.map(([url]) => url)).toContain(root + "/versao-1/ficha");
});

test("exporta JSON por nova requisição autenticada e libera o arquivo temporário", async () => {
  const create = vi.fn(() => "blob:teste");
  const revoke = vi.fn();
  vi.stubGlobal("URL", class extends URL { static createObjectURL = create; static revokeObjectURL = revoke; });
  const anchorClick = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});
  const request = mount(session(), Response.json(history), Response.json(workout),
    Response.json(workout, { headers: { "Content-Disposition": 'attachment; filename="academia-treino-2.json"' } }));
  await screen.findByText("Movimento sintético");
  click("Exportar ficha em JSON");
  await screen.findByText("Arquivo JSON preparado para download.");
  expect(request.mock.calls[3][0]).toBe(root + "/versao-2/exportacao");
  expect(request.mock.calls[3][1]).toMatchObject({ cache: "no-store", credentials: "same-origin" });
  expect(anchorClick).toHaveBeenCalledOnce();
  expect(create).toHaveBeenCalledOnce();
  await waitFor(() => expect(revoke).toHaveBeenCalledWith("blob:teste"));
});

test.each([403, 404])("exportação recusada (%s) limpa a ficha mostrada", async (status) => {
  mount(session(), Response.json(history), Response.json(workout), new Response(null, { status }));
  await screen.findByText("Movimento sintético");
  click("Exportar ficha em JSON");
  await screen.findByRole("alert");
  expect(screen.queryByText("Movimento sintético")).toBeNull();
  expect(screen.queryByRole("button", { name: "Exportar ficha em JSON" })).toBeNull();
});

test("download cancelado não cria arquivo e perfil sem papel de cliente não abre a tela", async () => {
  const create = vi.fn(() => "blob:teste");
  vi.stubGlobal("URL", class extends URL { static createObjectURL = create; });
  const controller = new AbortController();
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(Response.json(workout)));
  controller.abort();
  await act(async () => {
    await expect(downloadTraining("cliente", summary.id, controller.signal)).rejects.toThrow();
  });
  expect(create).not.toHaveBeenCalled();
  cleanup(); vi.unstubAllGlobals();
  const request = mount(session("ADMINISTRADOR"));
  await screen.findByRole("heading", { name: "Acesso não permitido" });
  expect(request).toHaveBeenCalledTimes(1);
});
