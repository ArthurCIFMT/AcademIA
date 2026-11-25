import { requestApi } from "../../lib/api/auth";

export type PlanFields = {
  nome: string;
  modalidade: string;
  duracao_dias: number;
  limite_acessos: number | null;
  preco_base: string | null;
  ativo: boolean;
};
export type Plan = PlanFields & { id: string; revisao: number };
export type Membership = {
  id: string;
  cliente_id: string;
  plano_id: string;
  atendente_id: string;
  inicio: string;
  fim: string;
  estado: "ATIVA" | "ENCERRADA";
  situacao: "VIGENTE" | "FUTURA" | "VENCIDA" | "ENCERRADA";
  modalidade_contratada: string;
  limites_snapshot: { limite_acessos: number | null; janela_limite: "DIA_CIVIL" | null };
};
export type Page<Item> = { itens: Item[]; total: number; pagina: number; limite: number };

const planAdmin = "/v1/admin/planos";

function historyPath(clientId: string) {
  return "/v1/atendimento/clientes/" + encodeURIComponent(clientId) + "/matriculas";
}

async function list<Item>(path: string, page: number, signal: AbortSignal): Promise<Page<Item>> {
  return (await requestApi(path + "?pagina=" + page, { signal })).json() as Promise<Page<Item>>;
}

export const listManagedPlans = (page: number, signal: AbortSignal) =>
  list<Plan>(planAdmin, page, signal);
export const listActivePlans = (page: number, signal: AbortSignal) =>
  list<Plan>("/v1/atendimento/planos", page, signal);
export const listMemberships = (clientId: string, page: number, signal: AbortSignal) =>
  list<Membership>(historyPath(clientId), page, signal);

function write(path: string, method: "POST" | "PUT", data: object, csrf: string) {
  return requestApi(path, {
    method, headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(data),
  });
}

export function savePlan(data: PlanFields, csrf: string, requestId: string, plan?: Plan) {
  return plan
    ? write(planAdmin + "/" + encodeURIComponent(plan.id), "PUT", { ...data, revisao: plan.revisao }, csrf)
    : write(planAdmin, "POST", { ...data, solicitacao_id: requestId }, csrf);
}

export async function registerMembership(clientId: string, plan: Plan, start: string, csrf: string, requestId: string) {
  const response = await write(historyPath(clientId), "POST", {
    solicitacao_id: requestId, plano_id: plan.id, plano_revisao: plan.revisao, inicio: start,
  }, csrf);
  return response.json() as Promise<Membership>;
}
