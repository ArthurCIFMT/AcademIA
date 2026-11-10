import { requestApi } from "../../lib/api/auth";

export type ClientSummary = {
  id: string;
  nome: string;
  email: string;
  ativo: boolean;
  estado_conta: "CONVIDADO" | "ATIVO" | "INATIVO" | "BLOQUEADO";
  revisao: number;
};

export type ClientDetail = ClientSummary & {
  data_nascimento: string;
  telefone: string | null;
  convite: {
    estado: "ENVIANDO" | "ENVIADO" | "FALHOU" | "INCERTO" | "SEM_CONFIRMACAO";
    expira_em: string;
  } | null;
};

export type ClientPage = {
  itens: ClientSummary[];
  pagina: number;
  limite: number;
  total: number;
};

export type ClientFields = {
  nome: string;
  data_nascimento: string;
  telefone: string | null;
};

type ClientMutation = (ClientFields & { email: string; vincular_existente: boolean })
  | (ClientFields & { revisao: number; ativo: boolean })
  | { revisao: number };

const base = "/v1/clientes";

export async function listClients(search: string, page: number, signal: AbortSignal): Promise<ClientPage> {
  const query = new URLSearchParams({ pagina: String(page) });
  if (search) query.set("busca", search);
  return (await requestApi(base + "?" + query, { signal })).json() as Promise<ClientPage>;
}

export async function getClient(id: string): Promise<ClientDetail> {
  return (await requestApi(base + "/" + encodeURIComponent(id), {})).json() as Promise<ClientDetail>;
}

export async function changeClient(
  path: string, method: "POST" | "PUT", data: ClientMutation, csrf: string,
): Promise<ClientDetail> {
  const response = await requestApi(base + path, {
    method,
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(data),
  });
  return response.json() as Promise<ClientDetail>;
}
