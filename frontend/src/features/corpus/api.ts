import { requestApi } from "../../lib/api/auth";
export type Version = {
  id: string; documento_id: string; catalogo_id: string; ambiente: "LITERATURA" | "TESTE"; numero: number;
  sha256: string; formato: string; tamanho_bytes: number; estado: "PENDENTE" | "APROVADO" | "REVOGADO"; revisao: number;
  metadados: { titulo: string; origem_url: string; licenca: string; idioma: string; autores: string[];
    ano: number | null; paginas_declaradas: number | null; secao: string | null; finalidades: string[]; limites: string };
  aprovado_por: string | null; aprovado_em: string | null; revogado_por: string | null;
  revogado_em: string | null; motivo_revogacao: string | null;
};
export type Page = { itens: Version[]; pagina: number; limite: number; total: number };
export async function list(page: number, scope: string, signal: AbortSignal): Promise<Page> {
  return (await requestApi("/v1/corpus?pagina=" + page + (scope ? "&ambiente=" + scope : ""), { signal })).json() as Promise<Page>;
}
export async function mutate(path: string, body: object, csrf: string) {
  return requestApi("/v1/corpus" + path, { method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify(body) });
}
export function fileBase64(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onerror = () => reject(new Error("Falha ao ler arquivo"));
    reader.onload = () => resolve(String(reader.result).split(",")[1]);
    reader.readAsDataURL(file);
  });
}
