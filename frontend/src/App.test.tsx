import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "./App";

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
  vi.unstubAllGlobals();
});

function renderHome() {
  return render(<MemoryRouter><App /></MemoryRouter>);
}

test("renderiza e consulta a API na URL configurada", async () => {
  vi.stubEnv("VITE_API_BASE_URL", "/ambiente/");
  const fetchMock = vi.fn().mockResolvedValue(Response.json({ status: "ok" }));
  vi.stubGlobal("fetch", fetchMock);

  renderHome();

  expect(screen.getByRole("heading", { name: "AcademIA" })).toBeTruthy();
  expect(screen.getByRole("status").textContent).toBe("Verificando conexão…");
  expect(await screen.findByText("Sistema disponível.")).toBeTruthy();
  expect(fetchMock).toHaveBeenCalledWith("/ambiente/health", expect.any(Object));
});

test("mostra erro de rede e recupera após nova tentativa", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockRejectedValueOnce(new TypeError("rede"))
      .mockResolvedValueOnce(Response.json({ status: "ok" })),
  );

  renderHome();

  expect((await screen.findByRole("alert")).textContent).toContain("conectar");
  fireEvent.click(screen.getByRole("button", { name: "Tentar novamente" }));
  expect(await screen.findByText("Sistema disponível.")).toBeTruthy();
  expect(screen.queryByRole("alert")).toBeNull();
});
