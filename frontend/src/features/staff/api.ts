import { requestApi, type Role } from "../../lib/api/auth";

export const staffRoles = ["ADMINISTRADOR", "ATENDENTE", "INSTRUTOR"] as const satisfies readonly Role[];
export type StaffRole = (typeof staffRoles)[number];
export type StaffFields = {
  nome: string;
  cargo: string;
  data_admissao: string;
  papeis: StaffRole[];
};
export type StaffSummary = StaffFields & {
  id: string;
  email: string;
  ativo: boolean;
  estado_conta: "CONVIDADO" | "ATIVO" | "INATIVO" | "BLOQUEADO";
  revisao: number;
};
export type StaffDetail = StaffSummary & {
  convite: {
    estado: "ENVIANDO" | "ENVIADO" | "FALHOU" | "INCERTO" | "SEM_CONFIRMACAO";
    expira_em: string;
  } | null;
};
export type StaffPage = {
  itens: StaffSummary[];
  pagina: number;
  limite: number;
  total: number;
};
export type CreateStaff = StaffFields & { email: string; vincular_existente: boolean };
export type UpdateStaff = StaffFields & { ativo: boolean; revisao: number };

const endpoint = "/v1/funcionarios";

export async function listStaff(page: number, signal: AbortSignal): Promise<StaffPage> {
  return (await requestApi(endpoint + "?pagina=" + page, { signal })).json() as Promise<StaffPage>;
}

export async function getStaff(id: string): Promise<StaffDetail> {
  return (await requestApi(endpoint + "/" + encodeURIComponent(id), {})).json() as Promise<StaffDetail>;
}

async function changeStaff(
  path: string,
  method: "POST" | "PUT",
  data: CreateStaff | UpdateStaff | { revisao: number },
  csrf: string,
): Promise<StaffDetail> {
  const response = await requestApi(path, {
    method,
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(data),
  });
  return response.json() as Promise<StaffDetail>;
}

export function createStaff(data: CreateStaff, csrf: string) {
  return changeStaff(endpoint, "POST", data, csrf);
}

export function updateStaff(id: string, data: UpdateStaff, csrf: string) {
  return changeStaff(endpoint + "/" + encodeURIComponent(id), "PUT", data, csrf);
}

export function resendStaffInvite(id: string, revision: number, csrf: string) {
  return changeStaff(endpoint + "/" + encodeURIComponent(id) + "/convite", "POST", { revisao: revision }, csrf);
}
