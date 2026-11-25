import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { ClientBiometrics } from "./ClientBiometrics";

const path = "/api/v1/atendimento/clientes/aluno-teste/biometria";
const ready = {
  cadastrada: false, elegivel: true, disponivel: true, atualizada_em: null, pendencia: null,
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("oculta o envio quando o cliente não tem matrícula", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => Response.json({ ...ready, elegivel: false })));
  render(<ClientBiometrics clientId="aluno-teste" csrf="csrf" />);
  expect(await screen.findByText(/com matrícula registrada/)).toBeTruthy();
  expect(screen.queryByLabelText("Selecionar foto")).toBeNull();
});

test("envia a foto por JSON e exibe somente o estado da referência", async () => {
  const fetchMock = vi.fn(async (url: string, options: RequestInit) => {
    expect(url).toBe(path);
    if (options.method !== "POST") return Response.json(ready);
    expect(options.headers).toMatchObject({ "X-CSRF-Token": "csrf", "Content-Type": "application/json" });
    expect(JSON.parse(String(options.body))).toEqual({ imagem_base64: "Zm90bw==" });
    return Response.json({ ...ready, cadastrada: true });
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<ClientBiometrics clientId="aluno-teste" csrf="csrf" />);
  const camera = await screen.findByLabelText("Tirar foto no celular");
  expect(camera.getAttribute("capture")).toBe("user");
  fireEvent.change(screen.getByLabelText("Selecionar foto"), {
    target: { files: [new File(["foto"], "teste.jpg", { type: "image/jpeg" })] },
  });
  expect(screen.getByText("Foto selecionada para envio · teste.jpg")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Cadastrar foto" }));
  expect(await screen.findByText("Foto enviada. Referência facial cadastrada.")).toBeTruthy();
  expect(screen.queryByText(/Foto selecionada para envio/)).toBeNull();
  expect(screen.queryByRole("img")).toBeNull();
});

test("retoma troca pendente sem reenviar a imagem", async () => {
  const fetchMock = vi.fn(async (url: string, options: RequestInit) => {
    if (url === path) return Response.json({ ...ready, cadastrada: true, pendencia: "TROCA" });
    expect(url).toBe(path + "/pendencia");
    expect(options.method).toBe("POST");
    expect(options.body).toBeUndefined();
    return Response.json({ ...ready, cadastrada: true });
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<ClientBiometrics clientId="aluno-teste" csrf="csrf" />);
  fireEvent.click(await screen.findByRole("button", { name: "Verificar pendência" }));
  expect(await screen.findByText("Pendência verificada.")).toBeTruthy();
  expect(screen.getByRole("button", { name: "Substituir foto" })).toBeTruthy();
});
