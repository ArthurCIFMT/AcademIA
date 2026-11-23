import { requestApi } from "../../lib/api/auth";

export type ClassFields = {
  nome: string;
  descricao: string | null;
  inicio: string;
  fim: string;
};

export type PublicClass = ClassFields & { id: string };
export type ManagedClass = PublicClass & { estado: "AGENDADA" | "CANCELADA"; revisao: number };
export type ClassPage<T> = { itens: T[]; pagina: number; limite: number; total: number };

const adminPath = "/v1/admin/aulas";

async function list<T>(path: string, page: number, signal: AbortSignal) {
  return (await requestApi(path + "?pagina=" + page, { signal })).json() as Promise<ClassPage<T>>;
}

export function publicClasses(page: number, signal: AbortSignal) {
  return list<PublicClass>("/v1/aulas", page, signal);
}

export function managedClasses(page: number, signal: AbortSignal) {
  return list<ManagedClass>(adminPath, page, signal);
}

function write(path: string, method: "POST" | "PUT", body: object, csrf: string) {
  return requestApi(path, {
    method, headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body),
  });
}

export function saveClass(data: ClassFields, csrf: string, requestId: string, item?: ManagedClass) {
  return item
    ? write(adminPath + "/" + encodeURIComponent(item.id), "PUT", { ...data, revisao: item.revisao }, csrf)
    : write(adminPath, "POST", { ...data, solicitacao_id: requestId }, csrf);
}

export function cancelClass(item: ManagedClass, csrf: string) {
  return write(adminPath + "/" + encodeURIComponent(item.id) + "/cancelamento", "POST", { revisao: item.revisao }, csrf);
}
