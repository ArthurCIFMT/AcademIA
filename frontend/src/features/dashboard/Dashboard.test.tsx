import { cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";

import { App } from "../../App";
import type { DashboardOverview, Indicator } from "./api";

const path = "/area/administracao";
const endpoint = "/api/v1/admin/dashboard";
const ready = <T,>(valor: T): Indicator<T> => ({ estado: "DISPONIVEL", valor });
const unavailable = { estado: "INDISPONIVEL" } as const;

const overview: DashboardOverview = {
  consultado_em: "2026-11-24T02:30:00Z",
  clientes_ativos: ready(12),
  clientes_matriculados: ready(7),
  funcionarios: ready(5),
  lotacao: ready(3),
  frequencia: ready({
    semanas: [{ inicio: "2026-11-16", visitas: 11 }, { inicio: "2026-11-23", visitas: 3 }],
    dias: [
      { data: "2026-11-22", visitas: 2, por_hora: [{ hora: 18, visitas: 2 }] },
      { data: "2026-11-23", visitas: 3, por_hora: [{ hora: 7, visitas: 1 }, { hora: 23, visitas: 2 }] },
    ],
  }),
};

function openArea(role: string, reply: () => Response) {
  const fetch = vi.fn(async (url: string) => {
    if (url.endsWith("/auth/session")) return Response.json({
      roles: [role], user_id: "teste-painel", csrf_token: "csrf-demo",
      expires_at: new Date(Date.now() + 60_000).toISOString(),
    });
    if (url.endsWith("/notificacoes/pendentes")) return Response.json([]);
    if (url === endpoint) return reply();
    throw new Error("URL inesperada: " + url);
  });
  vi.stubGlobal("fetch", fetch);
  render(<MemoryRouter initialEntries={[path]}><App /></MemoryRouter>);
  return fetch;
}

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

test("exibe os indicadores e permite escolher o dia do gráfico horário", async () => {
  openArea("ADMINISTRADOR", () => Response.json(overview));
  await screen.findByRole("list", { name: "Visitas por semana" });
  expect(screen.getByText("Clientes ativos").nextElementSibling?.textContent).toBe("12");
  expect(screen.getByText("Clientes com matrícula vigente").nextElementSibling?.textContent).toBe("7");
  expect(within(screen.getByRole("list", { name: "Visitas por semana" })).getByText("11")).toBeTruthy();
  expect(within(screen.getByRole("list", { name: "Visitas por faixa de uma hora" })).getByText("23h")).toBeTruthy();
  fireEvent.change(screen.getByRole("combobox", { name: "Dia para detalhar" }), { target: { value: "2026-11-22" } });
  expect(within(screen.getByRole("list", { name: "Visitas por faixa de uma hora" })).getByText("18h")).toBeTruthy();
  expect(screen.getByRole("heading", { name: "Avisos pendentes" })).toBeTruthy();
});

test("preserva zeros e separa a falha de outros indicadores ao atualizar", async () => {
  const snapshots = [
    { ...overview, frequencia: unavailable, lotacao: ready(0), funcionarios: unavailable },
    { ...overview, lotacao: ready(0), frequencia: ready({
      semanas: [{ inicio: "2026-11-23", visitas: 0 }],
      dias: [{ data: "2026-11-23", visitas: 0, por_hora: [] }],
    }) },
  ];
  const fetch = openArea("ADMINISTRADOR", () => Response.json(snapshots.shift()));
  await screen.findByText("Frequência temporariamente indisponível.");
  expect(screen.getByText("Funcionários cadastrados").nextElementSibling?.textContent).toBe("Indisponível");
  expect(screen.getByText("Pessoas presentes agora").nextElementSibling?.textContent).toBe("0");
  expect(screen.getByText("Clientes ativos").nextElementSibling?.textContent).toBe("12");
  fireEvent.click(screen.getByRole("button", { name: "Atualizar indicadores" }));
  expect(await screen.findByText("Nenhuma visita registrada neste dia.")).toBeTruthy();
  expect(fetch.mock.calls.filter(([url]) => url === endpoint)).toHaveLength(2);
});

test("permite nova consulta após indisponibilidade da API", async () => {
  let failed = true;
  openArea("ADMINISTRADOR", () => failed ? new Response(null, { status: 503 }) : Response.json(overview));
  await screen.findByText("Não foi possível consultar os indicadores.");
  failed = false;
  fireEvent.click(screen.getByRole("button", { name: "Atualizar indicadores" }));
  await screen.findByRole("list", { name: "Visitas por semana" });
});

test.each(["ATENDENTE", "INSTRUTOR", "CLIENTE"])("impede que %s consulte o painel", async role => {
  const fetch = openArea(role, () => Response.json(overview));
  expect(await screen.findByRole("heading", { name: "Acesso não permitido" })).toBeTruthy();
  expect(fetch.mock.calls.some(([url]) => url === endpoint)).toBe(false);
});
