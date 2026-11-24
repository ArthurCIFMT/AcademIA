import { requestApi } from "../../lib/api/auth";

export type Indicator<T> = { estado: "DISPONIVEL"; valor: T } | { estado: "INDISPONIVEL" };
type Week = { inicio: string; visitas: number };
type Day = { data: string; visitas: number; por_hora: { hora: number; visitas: number }[] };
export type Frequency = { semanas: Week[]; dias: Day[] };

export type DashboardOverview = {
  consultado_em: string;
  clientes_ativos: Indicator<number>;
  clientes_matriculados: Indicator<number>;
  funcionarios: Indicator<number>;
  lotacao: Indicator<number>;
  frequencia: Indicator<Frequency>;
};

export async function loadDashboard(signal: AbortSignal) {
  return (await requestApi("/v1/admin/dashboard", { signal })).json() as Promise<DashboardOverview>;
}
