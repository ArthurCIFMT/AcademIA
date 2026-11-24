import { requestApi } from "../../lib/api/auth";

export type ChargeState = "ABERTA" | "CANCELADA";
export type ChargeSituation = ChargeState | "VENCIDA" | "QUITADA";
export type ChargeFields = {
  competencia: string; vencimento: string; valor: string; matricula_id: string | null;
};
type Snapshot = ChargeFields & { estado: ChargeState };
export type Charge = Snapshot & {
  id: string; revisao: number; situacao: ChargeSituation; valor_pago: string; saldo: string;
};
export type Page<T> = { itens: T[]; pagina: number; limite: number; total: number };
export type ChargePage = Page<Charge> & {
  cliente_nome: string; politica_inadimplencia: "SOMENTE_INFORMATIVA";
};
export type Revision = { revisao: number; autor_nome: string | null; registrado_em: string; dados: Snapshot };
export type Membership = { id: string; inicio: string; fim: string; modalidade: string };

const base = (id: string) => "/v1/admin/clientes/" + encodeURIComponent(id) + "/cobrancas";

async function get<T>(path: string, signal: AbortSignal) {
  return (await requestApi(path, { signal })).json() as Promise<T>;
}

export function charges(clientId: string | undefined, page: number, signal: AbortSignal) {
  return get<ChargePage>((clientId ? base(clientId) : "/v1/cliente/cobrancas") + "?pagina=" + page, signal);
}

export function charge(clientId: string, chargeId: string, signal: AbortSignal) {
  return get<Charge>(base(clientId) + "/" + encodeURIComponent(chargeId), signal);
}

export function revisions(clientId: string, id: string, page: number, signal: AbortSignal) {
  return get<Page<Revision>>(base(clientId) + "/" + encodeURIComponent(id) + "/historico?pagina=" + page, signal);
}

export function memberships(id: string, page: number, signal: AbortSignal) {
  return get<Page<Membership>>(base(id) + "/matriculas?pagina=" + page, signal);
}

export async function saveCharge(clientId: string, fields: ChargeFields, csrf: string,
  change: { id: string; revisao: number; estado: ChargeState } | { solicitacao_id: string }) {
  const modifying = "id" in change;
  const path = modifying ? base(clientId) + "/" + encodeURIComponent(change.id) : base(clientId);
  const body = modifying ? { ...fields, revisao: change.revisao, estado: change.estado } : { ...fields, ...change };
  await requestApi(path, {
    method: modifying ? "PUT" : "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body),
  });
}
