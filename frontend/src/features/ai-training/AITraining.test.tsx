import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { AITrainingPage } from "./AITraining";
import type { Receipt } from "./api";
import { sampleContext } from "./fixtures";

const id = "11111111-1111-4111-8111-111111111111";
function receipt(estado = "PUBLICADA"): Receipt {
  return { solicitacao_id: id, estado, motivo: "TESTE", versao_publicada_id: estado === "PUBLICADA" ? "version" : null };
}
afterEach(() => { cleanup(); vi.restoreAllMocks(); vi.unstubAllGlobals(); });

function mount(handler: (url: string, init: RequestInit) => Promise<Response>, query = "") {
  const fetcher = vi.fn(handler);
  vi.stubGlobal("fetch", fetcher);
  vi.spyOn(crypto, "randomUUID").mockReturnValue(id);
  render(<MemoryRouter initialEntries={["/area/cliente/treino-ia" + query]}><AITrainingPage csrf="csrf-test" /></MemoryRouter>);
  return fetcher;
}
const click = (name: string) => fireEvent.click(screen.getByRole("button", { name }));

test("gera uma vez, mostra a ficha antes do parecer e consulta sem repetir POST", async () => {
  const fetcher = mount(async (_, init) => Response.json(init.method === "POST" ? receipt() : { execucao: receipt(), geracao: sampleContext }));
  click("Solicitar geração");
  expect(await screen.findByText("Movimento sintético")).toBeTruthy();
  expect(screen.getByText(/Aguardando designação/)).toBeTruthy();
  expect(screen.getByText("Orientação em português.")).toBeTruthy();
  expect(screen.getByRole("link", { name: "Literatura de teste" }).getAttribute("href")).toBe("https://example.test/livro");
  click("Consultar estado salvo");
  await waitFor(() => expect(fetcher.mock.calls.length).toBeGreaterThan(2));
  const writes = fetcher.mock.calls.filter(([, init]) => init.method === "POST");
  expect(writes).toHaveLength(1);
  expect(JSON.parse(String(writes[0][1].body))).toEqual({ solicitacao_id: id });
  expect(writes[0][1].headers).toMatchObject({ "X-CSRF-Token": "csrf-test" });
});

test.each([
  ["BLOQUEADA", "Geração bloqueada pela triagem"],
  ["DADOS_INSUFICIENTES", "É necessário completar ou conferir o onboarding"],
  ["ABSTENCAO", "Não há suporte suficiente para gerar esta ficha"],
  ["TIMEOUT", "O tempo da geração foi excedido"],
])("retoma %s sem repetir geração nem esconder o histórico", async (status, label) => {
  const fetcher = mount(async () => Response.json({ execucao: receipt(status), geracao: null }), "?solicitacao=" + id);
  expect(await screen.findByText(label)).toBeTruthy();
  expect(screen.getByText(/Seus treinos já existentes continuam/)).toBeTruthy();
  expect(screen.getByRole("link", { name: "Meus treinos e histórico" })).toBeTruthy();
  expect(fetcher.mock.calls.every(([, init]) => init.method !== "POST")).toBe(true);
});

test("cancelamento em voo não abre segunda geração", async () => {
  let state = "EM_EXECUCAO";
  let finish: (response: Response) => void = () => {};
  const pending = new Promise<Response>((resolve) => { finish = resolve; });
  const fetcher = mount(async (_, init) => {
    if (init.method === "POST") return pending;
    if (init.method === "DELETE") { state = "CANCELADA"; return Response.json(receipt(state)); }
    return Response.json({ execucao: receipt(state), geracao: null });
  });
  click("Solicitar geração");
  await screen.findByText("Geração em andamento");
  click("Cancelar solicitação");
  expect(await screen.findByText("Solicitação cancelada")).toBeTruthy();
  finish(Response.json(receipt("CANCELADA")));
  await waitFor(() => expect(screen.getByRole("button", { name: "Preparar nova solicitação" })).toBeTruthy());
  expect(fetcher.mock.calls.filter(([, init]) => init.method === "POST")).toHaveLength(1);
});

test("perda de autorização remove ficha e fontes do acompanhamento", async () => {
  let denied = false;
  mount(async () => denied ? new Response(null, { status: 403 }) : Response.json({ execucao: receipt(), geracao: sampleContext }), "?solicitacao=" + id);
  await screen.findByText("Movimento sintético");
  denied = true;
  click("Consultar estado salvo");
  await screen.findByRole("alert");
  expect(screen.queryByText("Movimento sintético")).toBeNull();
  expect(screen.queryByText("Literatura de teste")).toBeNull();
});

test("identificador desconhecido não dispara POST e URL maliciosa não vira link", async () => {
  const fetcher = mount(async () => new Response(null, { status: 404 }), "?solicitacao=" + id);
  await screen.findByRole("alert");
  expect(fetcher.mock.calls).toHaveLength(1);
  cleanup();
  const unsafe = structuredClone(sampleContext);
  unsafe.fontes[0].origem_url = "javascript:alert(1)";
  unsafe.fontes_alteradas = true;
  mount(async () => Response.json({ execucao: receipt(), geracao: unsafe }), "?solicitacao=" + id);
  await screen.findByText("Literatura de teste");
  expect(screen.queryByRole("link", { name: "Literatura de teste" })).toBeNull();
  expect(screen.getByText(/Uma fonte utilizada não está mais aprovada/)).toBeTruthy();
});
