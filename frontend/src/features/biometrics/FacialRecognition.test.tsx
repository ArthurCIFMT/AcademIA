import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import { FacialRecognition } from "./FacialRecognition";

function selectPhoto() {
  fireEvent.change(screen.getByLabelText("Selecionar foto"), {
    target: { files: [new File(["foto"], "captura.jpg", { type: "image/jpeg" })] },
  });
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("envia somente captura, direção e evento e apresenta identificação sem liberação", async () => {
  const mock = vi.fn(async (url: string, options: RequestInit) => {
    expect(url).toBe("/api/v1/atendimento/reconhecimento");
    expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf-demo" });
    expect(JSON.parse(String(options.body))).toEqual({
      evento_id: expect.any(String), direcao: "SAIDA", imagem_base64: "Zm90bw==",
    });
    return Response.json({ resultado: "IDENTIFICADO", cliente_nome: "Cliente sintético", similaridade: 0.987 });
  });
  vi.stubGlobal("fetch", mock);
  render(<FacialRecognition csrf="csrf-demo" />);
  expect(screen.getByLabelText("Tirar foto no celular").getAttribute("capture")).toBe("user");
  fireEvent.change(screen.getByLabelText("Direção"), { target: { value: "SAIDA" } });
  selectPhoto();
  fireEvent.click(screen.getByRole("button", { name: "Identificar cliente" }));
  expect(await screen.findByText("Cliente identificado.")).toBeTruthy();
  expect(screen.getByText("Cliente sintético")).toBeTruthy();
  expect(screen.getByText("Similaridade 98,7%")).toBeTruthy();
  expect(screen.getByText(/A autorização de entrada é uma etapa separada/)).toBeTruthy();
  expect(screen.queryByText(/entrada autorizada/i)).toBeNull();
});

test("reenviar a mesma tentativa após falha de rede conserva o evento", async () => {
  const attempts: string[] = [];
  const mock = vi.fn(async (_url: string, options: RequestInit) => {
    attempts.push(String(options.body));
    if (attempts.length === 1) throw new TypeError("Conexão interrompida");
    return Response.json({ resultado: "PONTUACAO_BAIXA", cliente_nome: null, similaridade: 0.74 });
  });
  vi.stubGlobal("fetch", mock);
  render(<FacialRecognition csrf="csrf-demo" />);
  selectPhoto();
  fireEvent.click(screen.getByRole("button", { name: "Identificar cliente" }));
  expect(await screen.findByText(/Tente novamente com a mesma captura/)).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Identificar cliente" }));
  expect(await screen.findByText(/Similaridade insuficiente/)).toBeTruthy();
  expect(attempts).toHaveLength(2);
  expect(attempts[0]).toBe(attempts[1]);
});

test("o cliente autenticado não recebe a tela de atendimento", async () => {
  const mock = vi.fn(async () => Response.json({
    user_id: "cliente-sintetico", roles: ["CLIENTE"], csrf_token: "csrf-demo",
    expires_at: new Date(Date.now() + 60_000).toISOString(),
  }));
  vi.stubGlobal("fetch", mock);
  render(<MemoryRouter initialEntries={["/area/atendimento/reconhecimento"]}><App /></MemoryRouter>);
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(screen.queryByLabelText("Selecionar foto")).toBeNull();
});
