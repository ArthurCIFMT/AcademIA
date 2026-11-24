import { requestApi } from "../../lib/api/auth";

export type AttendanceQuery = { de: string; ate: string; pagina: number };
export type AttendancePage = AttendanceQuery & {
  cliente_nome: string;
  itens: { id: string; entrada_em: string; saida_em: string | null }[];
  total: number;
  limite: number;
};

export async function loadAttendance(query: AttendanceQuery, signal: AbortSignal, clientId?: string) {
  const base = clientId ? "/v1/clientes/" + encodeURIComponent(clientId) : "/v1/cliente";
  const params = new URLSearchParams({ de: query.de, ate: query.ate, pagina: String(query.pagina) });
  return (await requestApi(base + "/frequencia?" + params, { signal })).json() as Promise<AttendancePage>;
}
