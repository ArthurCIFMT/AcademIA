import { requestApi } from "../../lib/api/auth";
import type { Detail } from "../training-review/api";

export type Receipt = { solicitacao_id: string; estado: string; motivo: string; versao_publicada_id: string | null };
export type Source = { fragmento_id: string; documento_versao_id: string; titulo: string; origem_url: string; idioma: string; pagina: number | null; linha_inicio: number | null; linha_fim: number | null; secao: string | null };
export type Context = {
  execucao_id: string; iniciada_em: string; modelo: string; versao_prompts: string;
  regra_versao: number | null; politica_alterada: boolean; fontes_alteradas: boolean; fontes: Source[];
  contexto: { treino: Detail; onboarding_usado_id: string; onboarding_atual_id: string | null;
    pendencias: string[]; aviso: { instrutor_designado_id: string | null; interno_registrado: boolean; email_estado: string | null; email_tentativas: number } };
};
export type Followup = { execucao: Receipt; geracao: Context | null };
const base = "/v1/ia/fichas/execucoes";
export async function generate(id: string, csrf: string, signal: AbortSignal): Promise<Receipt> {
  return (await requestApi(base, { method: "POST", signal, headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf }, body: JSON.stringify({ solicitacao_id: id }) })).json() as Promise<Receipt>;
}
export async function followup(id: string, signal: AbortSignal): Promise<Followup> {
  return (await requestApi(base + "/" + encodeURIComponent(id) + "/acompanhamento", { signal })).json() as Promise<Followup>;
}
export async function cancel(id: string, csrf: string, signal: AbortSignal): Promise<Receipt> {
  return (await requestApi(base + "/" + encodeURIComponent(id), { method: "DELETE", signal, headers: { "X-CSRF-Token": csrf } })).json() as Promise<Receipt>;
}
export async function versionContext(client: string, version: string, signal: AbortSignal): Promise<Context> {
  return (await requestApi("/v1/ia/fichas/clientes/" + encodeURIComponent(client) + "/versoes/" + encodeURIComponent(version) + "/contexto", { signal })).json() as Promise<Context>;
}
