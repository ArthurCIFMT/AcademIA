import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { FacialRecognition } from "../biometrics/FacialRecognition";
import { ManualAccessForm } from "./ManualAccessForm";

const failureId = "falha-registrada";
const csrf = "csrf-demo";
const client = {
  id: "cliente-sintetico", nome: "Cliente Sintético", email: "cliente@example.test",
  idade: 25, ativo: true, estado_conta: "ATIVO", revisao: 1,
};

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("mostra confirmação manual após uma falha facial registrada", async () => {
  vi.stubGlobal("fetch", vi.fn(async () => Response.json({
    id: failureId, resultado: "FALHA_PROVEDOR", cliente_nome: null, similaridade: null,
  })));
  render(<FacialRecognition csrf={csrf} />);
  expect(screen.queryByRole("button", { name: "Confirmar identidade manualmente" })).toBeNull();
  fireEvent.change(screen.getByLabelText("Selecionar foto"), {
    target: { files: [new File(["foto"], "captura.jpg", { type: "image/jpeg" })] },
  });
  fireEvent.click(screen.getByRole("button", { name: "Identificar cliente" }));
  expect(await screen.findByRole("button", { name: "Confirmar identidade manualmente" })).toBeTruthy();
});

test("busca cliente e envia o motivo e a confirmação explicitamente", async () => {
  const fetchMock = vi.fn(async (url: string, options: RequestInit) => {
    if (url.startsWith("/api/v1/clientes?")) {
      expect(url).toContain("busca=Cliente");
      return Response.json({ itens: [client], pagina: 1, limite: 20, total: 1 });
    }
    expect(url).toBe("/api/v1/atendimento/acessos/" + failureId + "/confirmacao-manual");
    expect(options.headers).toMatchObject({ "X-CSRF-Token": csrf });
    expect(JSON.parse(String(options.body))).toEqual({
      cliente_id: client.id, motivo: "Conferi a identidade", identidade_confirmada: true,
    });
    return Response.json({ decisao: {
      resultado: "DENY", motivo: "SEM_MATRICULA_VIGENTE", comando: { estado: "ACEITO" },
    } });
  });
  vi.stubGlobal("fetch", fetchMock);
  render(<ManualAccessForm csrf={csrf} failureId={failureId} />);
  fireEvent.click(screen.getByRole("button", { name: "Confirmar identidade manualmente" }));
  fireEvent.change(screen.getByLabelText("Cliente pelo nome ou e-mail"), { target: { value: "Cliente" } });
  fireEvent.click(screen.getByRole("button", { name: "Buscar cliente" }));
  fireEvent.click(await screen.findByRole("button", { name: "Selecionar Cliente Sintético" }));
  const confirm = screen.getByRole("button", { name: "Solicitar autorização" }) as HTMLButtonElement;
  const reason = screen.getByLabelText("Motivo da confirmação manual");
  fireEvent.change(reason, { target: { value: "Conferi a identidade" } });
  expect(confirm.disabled).toBe(true);
  fireEvent.click(screen.getByLabelText("Confirmei a identidade do cliente."));
  expect(confirm.disabled).toBe(false);
  fireEvent.click(confirm);
  expect(await screen.findByText("Acesso negado.")).toBeTruthy();
  expect(screen.getByText("O cliente precisa de uma matrícula vigente.")).toBeTruthy();
});
