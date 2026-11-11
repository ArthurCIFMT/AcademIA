import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "../../App";
import type { Detail } from "./api";

const base = "/api/v1/treinos/clientes/cliente/versoes/versao";
const route = "/area/instrutor/clientes/cliente/treinos/versao/revisao";
const detail: Detail = {
  ficha: { id: "versao", numero: 1, origem: "MANUAL", autor_id: "instrutor",
    onboarding_id: "onboarding", avaliacao_id: null, versao_base_id: null,
    estado_publicacao: "RASCUNHO", vigente: false, revisao: 1, publicada_em: null,
    motivo_exclusao: null, dias: [{ titulo: "Dia A", itens: [{
      exercicio_id: "exercicio", equipamento_ids: [], series: 3, repeticoes: "8 a 12",
      carga_kg: null, intervalo_segundos: 60, cadencia: "2-0-2", observacoes: "Teste",
      exercicio_snapshot: { nome: "Movimento sintético" },
    }] }] },
  parecer: { id: null, estado: "PENDENTE", instrutor_id: null, criado_em: null, motivo: null },
  validacao: null,
};
const published: Detail = { ...detail, ficha: { ...detail.ficha, estado_publicacao: "PUBLICADO", vigente: true } };
const session = (role = "INSTRUTOR") => Response.json({
  user_id: "instrutor", roles: [role], csrf_token: "csrf-sintetico",
  expires_at: new Date(Date.now() + 60000).toISOString(),
});
afterEach(() => { cleanup(); vi.unstubAllGlobals(); });

function mount(responses: Array<Response | Error>, path = route) {
  const request = vi.fn<(url: string, options: RequestInit) => Promise<Response>>();
  responses.forEach((value) => value instanceof Error
    ? request.mockRejectedValueOnce(value) : request.mockResolvedValueOnce(value));
  vi.stubGlobal("fetch", request);
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  return request;
}
const click = (name: string) => fireEvent.click(screen.getByRole("button", { name }));

test("publica a versão salva com parecer pendente e registra avaliação posterior", async () => {
  const accepted: Detail = { ...published, parecer: { id: "parecer", estado: "ACEITO",
    instrutor_id: "instrutor", criado_em: "2026-11-10T10:00:00Z", motivo: null } };
  const request = mount([session(), Response.json(detail),
    Response.json({ treino: published, aviso_email: { estado: "FALHOU", tentativas: 1 } }),
    Response.json(accepted)]);
  await screen.findByText("Movimento sintético");
  expect(screen.getByRole<HTMLButtonElement>("button", { name: "Publicar versão salva" }).disabled).toBe(true);
  fireEvent.click(screen.getByRole("checkbox"));
  click("Publicar versão salva");
  expect(await screen.findByText("Ficha vigente")).toBeTruthy();
  expect(screen.getByText(/Esta ficha já pode ser consultada/)).toBeTruthy();
  expect(screen.getByText(/Aviso por e-mail · FALHOU/)).toBeTruthy();
  click("Registrar parecer");
  expect(await screen.findByText("Parecer ACEITO")).toBeTruthy();
  const writes = request.mock.calls.filter(([, options]) => options.method === "POST");
  expect(writes.map(([url]) => url)).toEqual([base + "/publicacao", base + "/parecer"]);
  expect(JSON.parse(String(writes[0][1].body))).toMatchObject({
    revisao: 1, onboarding_id: "onboarding", versao_base_id: null, restricoes_conferidas: true,
  });
  expect(writes[0][1].headers).toMatchObject({ "X-CSRF-Token": "csrf-sintetico" });
});

test("falha de rede preserva motivo e chave para repetir o mesmo parecer", async () => {
  const rejected: Detail = { ...published, parecer: { id: "parecer", estado: "REJEITADO",
    instrutor_id: "instrutor", criado_em: "2026-11-10T10:00:00Z", motivo: "Rever a carga." } };
  const request = mount([session(), Response.json(published), new Error("offline"), Response.json(rejected)]);
  await screen.findByText("Ficha vigente");
  fireEvent.change(screen.getByLabelText("Decisão"), { target: { value: "REJEITADO" } });
  fireEvent.change(screen.getByLabelText("Motivo do parecer"), { target: { value: "Rever a carga." } });
  click("Registrar parecer");
  await screen.findByRole("alert");
  expect(screen.getByLabelText<HTMLTextAreaElement>("Motivo do parecer").value).toBe("Rever a carga.");
  click("Registrar parecer");
  expect(await screen.findByText("Parecer REJEITADO")).toBeTruthy();
  expect(screen.getByText("Movimento sintético")).toBeTruthy();
  const writes = request.mock.calls.filter(([, options]) => options.method === "POST");
  expect(writes[0][1].body).toBe(writes[1][1].body);
});

test("expiração oculta conteúdo e perda de autorização limpa a versão", async () => {
  const expired: Detail = { ...published, ficha: { ...published.ficha, estado_publicacao: "CONTEUDO_EXPIRADO", vigente: false } };
  mount([session(), Response.json(expired), new Response(null, { status: 403 })]);
  await screen.findByText("Conteúdo expirado");
  expect(screen.queryByText("Movimento sintético")).toBeNull();
  click("Recarregar versão");
  await screen.findByRole("alert");
  expect(screen.queryByText("Conteúdo expirado")).toBeNull();
  expect(screen.queryByRole("button", { name: "Registrar parecer" })).toBeNull();
});

test("fila possui link autorizado e estado vazio, cliente não acessa a revisão", async () => {
  mount([session(), Response.json({ itens: [{ cliente_id: "cliente", cliente_nome: "Cliente sintético",
    versao_id: "versao", numero: 1, publicada_em: "2026-11-10T10:00:00Z" }],
    total: 1, pagina: 1, limite: 20 }), Response.json({ itens: [], total: 0, pagina: 1, limite: 20 })],
    "/area/instrutor/revisoes");
  expect((await screen.findByRole<HTMLAnchorElement>("link", { name: "Cliente sintético · Versão 1" })).getAttribute("href")).toBe(route);
  click("Atualizar fila");
  await screen.findByText("Nenhuma ficha aguardando parecer.");
  cleanup();
  const request = mount([session("CLIENTE")]);
  await screen.findByRole("heading", { name: "Acesso não permitido" });
  await waitFor(() => expect(request).toHaveBeenCalledTimes(1));
});
