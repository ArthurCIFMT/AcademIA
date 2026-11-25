import { requestApi } from "../../lib/api/auth";
import type { Page, Plan } from "../memberships/api";

const base = "/v1/cliente/compra-simulada";
type Offer = Pick<Plan, "id" | "nome" | "modalidade" | "duracao_dias"> & { preco_base: string };

export type Outcome = "CONFIRMADO" | "PENDENTE" | "RECUSADO";
export type Receipt = {
  id: string; plano_id: string; plano_nome_snapshot: string; valor: string;
  estado: Outcome; simulado_em: string; confirmado_em: string | null; simulado: true;
};

async function list<T>(path: string, page: number, signal: AbortSignal): Promise<Page<T>> {
  return (await requestApi(path + "?pagina=" + page, { signal })).json() as Promise<Page<T>>;
}

export const offers = (page: number, signal: AbortSignal) => list<Offer>(base + "/planos", page, signal);
export const receipts = (page: number, signal: AbortSignal) => list<Receipt>(base, page, signal);

export async function simulate(
  data: { solicitacao_id: string; plano_id: string; resultado: Outcome }, csrf: string,
): Promise<Receipt> {
  return (await requestApi(base, {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(data),
  })).json() as Promise<Receipt>;
}
