import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";

import { LocalEmailNotice } from "./LocalEmailNotice";

afterEach(() => {
  cleanup();
  vi.unstubAllEnvs();
});

test("orienta sobre a caixa local e oferece o endereço configurado", () => {
  vi.stubEnv("VITE_TEST_MAILBOX_URL", "http://127.0.0.1:8025");
  render(<LocalEmailNotice />);
  expect(screen.getByRole("note").textContent).toContain("não são enviados ao Gmail");
  expect(screen.getByRole("link").getAttribute("href")).toBe("http://127.0.0.1:8025/");
});

test.each(["", "javascript:alert(1)", "https://externo.example.test", "http://usuario:senha@localhost"])(
  "mantém a orientação sem criar link externo ou inválido: %s", value => {
    vi.stubEnv("VITE_TEST_MAILBOX_URL", value);
    render(<LocalEmailNotice />);
    expect(screen.getByRole("note")).toBeTruthy();
    expect(screen.queryByRole("link")).toBeNull();
  },
);
