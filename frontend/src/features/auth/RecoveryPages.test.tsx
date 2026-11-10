import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";

const token = "a".repeat(43);
const secret = "senha-sintetica-nova";
const base = "/api/v1/auth/recovery";

function LocationIndicator() {
  const { pathname, hash } = useLocation();
  return <span data-testid="location">{pathname}{hash}</span>;
}

function openPage(url: string, ...responses: Response[]) {
  const fetchMock = vi.fn();
  for (const response of responses) fetchMock.mockResolvedValueOnce(response);
  vi.stubGlobal("fetch", fetchMock);
  render(<MemoryRouter initialEntries={[url]}><App /><LocationIndicator /></MemoryRouter>);
  return fetchMock;
}

function submitPassword(confirmation: string) {
  fireEvent.change(screen.getByLabelText("Nova senha", { exact: true }), { target: { value: secret } });
  fireEvent.change(screen.getByLabelText("Confirme a nova senha"), { target: { value: confirmation } });
  fireEvent.click(screen.getByRole("button", { name: "Redefinir senha" }));
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("entra na recuperação pelo login e exibe confirmação genérica", async () => {
  const fetchMock = openPage("/login", new Response(null, { status: 401 }), new Response(null, { status: 202 }));
  fireEvent.click(await screen.findByRole("link", { name: "Esqueci minha senha" }));
  fireEvent.change(screen.getByLabelText("E-mail"), { target: { value: "cliente@example.test" } });
  fireEvent.click(screen.getByRole("button", { name: "Solicitar recuperação" }));

  expect(await screen.findByText("Se o e-mail estiver elegível para recuperação, você receberá um link.")).toBeTruthy();
  expect(fetchMock).toHaveBeenLastCalledWith(base, expect.objectContaining({
    method: "POST",
    body: JSON.stringify({ email: "cliente@example.test" }),
    credentials: "same-origin",
  }));
});

test("remove o fragmento e envia token e senha no JSON da confirmação", async () => {
  const fetchMock = openPage("/redefinir-senha#token=" + token, new Response(null, { status: 204 }));

  expect(screen.getByTestId("location").textContent).toBe("/redefinir-senha");
  expect(fetchMock).not.toHaveBeenCalled();
  submitPassword(secret);
  expect(await screen.findByText("Senha redefinida. Entre com a nova senha.")).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledWith(base + "/confirm", expect.objectContaining({
    method: "POST",
    body: JSON.stringify({ token, senha: secret }),
  }));
  expect(screen.queryByLabelText("Nova senha", { exact: true })).toBeNull();
});

test("recusa confirmação divergente e oferece outro link após resposta 401", async () => {
  const fetchMock = openPage("/redefinir-senha#token=" + token, new Response(null, { status: 401 }));
  submitPassword("senha-diferente");
  expect((await screen.findByRole("alert")).textContent).toBe("As senhas precisam ser iguais.");
  expect(fetchMock).not.toHaveBeenCalled();

  submitPassword(secret);
  expect(await screen.findByText("O link de recuperação é inválido ou expirou.")).toBeTruthy();
  expect(screen.getByRole("link", { name: "Solicitar outro link" }).getAttribute("href")).toBe("/recuperar-acesso");
});

test("sem token não apresenta formulário nem chama a API", () => {
  const fetchMock = openPage("/redefinir-senha");
  expect(screen.queryByLabelText("Nova senha", { exact: true })).toBeNull();
  expect(screen.getByRole("alert").textContent).toBe("O link de recuperação é inválido ou expirou.");
  expect(fetchMock).not.toHaveBeenCalled();
});
