import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import { Button, FormField, NavigationDisclosure, ResponsiveTable, StatusMessage } from "./primitives";

afterEach(cleanup);

test("ação secundária pode ser acionada dentro de formulário sem submetê-lo", () => {
  const submit = vi.fn((event: React.FormEvent) => event.preventDefault());
  const action = vi.fn();
  render(<form onSubmit={submit}><Button variant="secondary" onClick={action}>Voltar</Button></form>);
  fireEvent.click(screen.getByRole("button", { name: "Voltar" }));
  expect(action).toHaveBeenCalledOnce();
  expect(submit).not.toHaveBeenCalled();
});

test("ação pendente tem texto próprio e impede clique repetido", () => {
  const send = vi.fn();
  const { rerender } = render(<Button onClick={send}>Salvar</Button>);
  fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
  rerender(<Button pending pendingLabel="Salvando…" onClick={send}>Salvar</Button>);
  const pending = screen.getByRole<HTMLButtonElement>("button", { name: "Salvando…" });
  expect(pending.disabled).toBe(true);
  expect(pending.getAttribute("aria-busy")).toBe("true");
  fireEvent.click(pending);
  expect(send).toHaveBeenCalledOnce();
});

test("campo mantém rótulo, requisito e descrição quando a validação muda", () => {
  const field = (error?: string) => (
    <FormField label="E-mail" hint="Use seu e-mail cadastrado." error={error} required>
      {control => <input {...control} type="email" />}
    </FormField>
  );
  const { rerender } = render(field());
  const input = screen.getByRole<HTMLInputElement>("textbox", { name: "E-mail" });
  expect(input.required).toBe(true);
  expect(screen.getByRole("textbox", { description: "Use seu e-mail cadastrado." })).toBe(input);
  rerender(field("Informe um e-mail válido."));
  expect(screen.getByRole("textbox", {
    description: "Use seu e-mail cadastrado. Informe um e-mail válido.",
  })).toBe(input);
  expect(input.getAttribute("aria-invalid")).toBe("true");
  rerender(field());
  expect(input.hasAttribute("aria-invalid")).toBe(false);
  expect(screen.queryByText("Informe um e-mail válido.")).toBeNull();
});

test("mensagens distinguem atualização de estado de um conflito e preservam o rótulo da tabela", () => {
  const { rerender } = render(<StatusMessage state="loading" title="Carregando" />);
  expect(screen.getByRole("status").textContent).toBe("Carregando");
  rerender(<StatusMessage state="conflict" title="Revisão superada">Recarregue os dados.</StatusMessage>);
  expect(screen.getByRole("alert").textContent).toContain("Revisão superada");
  rerender(<ResponsiveTable caption="Equipamentos"><tbody><tr><th scope="row">Halteres</th></tr></tbody></ResponsiveTable>);
  const region = screen.getByRole("region", { name: "Equipamentos" });
  expect(region.tabIndex).toBe(0);
  expect(within(region).getByRole("table", { name: "Equipamentos" })).toBeTruthy();
  expect(within(region).getByRole("rowheader", { name: "Halteres" })).toBeTruthy();
});

test("Escape fecha a navegação e devolve o foco ao controle", () => {
  const { container } = render(<NavigationDisclosure label="Menu" navigationLabel="Área do cliente">
    <a href="#treinos">Meus treinos</a>
  </NavigationDisclosure>);
  const summary = screen.getByText("Menu");
  const disclosure = container.querySelector("details")!;
  disclosure.open = true;
  const item = screen.getByRole("link", { name: "Meus treinos" });
  item.focus();
  fireEvent.keyDown(item, { key: "Escape" });
  expect(disclosure.open).toBe(false);
  expect(document.activeElement).toBe(summary);
});
