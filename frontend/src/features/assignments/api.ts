import { requestApi } from "../../lib/api/auth";

export type Page<T> = { itens: T[]; pagina: number; limite: number; total: number };
export type Person = { id: string; nome: string };
export type Instructor = Person & { email: string };
export type Assignment = {
  id: string;
  cliente_id: string;
  instrutor_id: string;
  instrutor_nome: string;
  inicio: string;
  fim: string | null;
  atribuido_por: string;
};
export type AssignmentHistory = {
  cliente: Person;
  cliente_elegivel: boolean;
  vigente: Assignment | null;
  instrutor_ativo: boolean;
  historico: Page<Assignment>;
};
export type AssignedClient = Person & { inicio: string };

const endpoint = "/v1/designacoes";
const clientPath = (id: string) => endpoint + "/clientes/" + encodeURIComponent(id);

export async function assignmentHistory(id: string, page: number, signal: AbortSignal): Promise<AssignmentHistory> {
  return (await requestApi(clientPath(id) + "?pagina=" + page, { signal })).json() as Promise<AssignmentHistory>;
}

export async function instructorOptions(search: string, page: number, signal: AbortSignal): Promise<Page<Instructor>> {
  const query = new URLSearchParams({ pagina: String(page) });
  if (search) query.set("busca", search);
  return (await requestApi(endpoint + "/instrutores?" + query, { signal })).json() as Promise<Page<Instructor>>;
}

export async function myAssignments(page: number, signal: AbortSignal): Promise<Page<AssignedClient>> {
  return (await requestApi(endpoint + "/minhas?pagina=" + page, { signal })).json() as Promise<Page<AssignedClient>>;
}

export async function changeAssignment(id: string, instructor: string, current: string | null, csrf: string) {
  await requestApi(clientPath(id), {
    method: "PUT",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify({ instrutor_id: instructor, vigente_id: current }),
  });
}
