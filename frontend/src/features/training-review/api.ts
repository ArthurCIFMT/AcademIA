import { requestApi } from "../../lib/api/auth";
import type { Workout } from "../training-editor/api";

export type Detail = {
  ficha: Workout & { explicacao?: string | null; vigente: boolean; motivo_exclusao: string | null; publicada_em: string | null };
  parecer: { id: string | null; estado: "PENDENTE" | "ACEITO" | "REJEITADO";
    instrutor_id: string | null; criado_em: string | null; motivo: string | null };
  validacao: { revisao: number; validado_por: string; validado_em: string } | null;
};
export type MailStatus = { estado: "ENVIANDO" | "ENVIADO" | "FALHOU" | "INCERTO"; tentativas: number };
export type Queue = { itens: { cliente_id: string; cliente_nome: string;
  versao_id: string; numero: number; publicada_em: string }[];
  pagina: number; limite: number; total: number };
const version = (client: string, id: string) => "/v1/treinos/clientes/" + encodeURIComponent(client)
  + "/versoes/" + encodeURIComponent(id);
export async function readDetail(client: string, id: string, signal: AbortSignal): Promise<Detail> {
  return (await requestApi(version(client, id) + "/revisao", { signal })).json() as Promise<Detail>;
}
export async function readQueue(page: number, signal: AbortSignal): Promise<Queue> {
  return (await requestApi("/v1/treinos/pendentes?pagina=" + page, { signal })).json() as Promise<Queue>;
}
async function mutate(path: string, csrf: string, body: object) {
  return requestApi(path, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body) });
}
export async function publish(client: string, detail: Detail, csrf: string, requestId: string) {
  const { ficha } = detail;
  return (await mutate(version(client, ficha.id) + "/publicacao", csrf, {
    solicitacao_id: requestId, revisao: ficha.revisao, onboarding_id: ficha.onboarding_id,
    versao_base_id: ficha.versao_base_id, restricoes_conferidas: true,
  })).json() as Promise<{ treino: Detail; aviso_email: MailStatus | null }>;
}
export async function review(client: string, id: string, csrf: string,
  body: { solicitacao_id: string; estado: "ACEITO" | "REJEITADO"; motivo: string | null }): Promise<Detail> {
  return (await mutate(version(client, id) + "/parecer", csrf, body)).json() as Promise<Detail>;
}
export async function resend(client: string, id: string, csrf: string, previous: number | null): Promise<MailStatus | null> {
  return (await mutate(version(client, id) + "/aviso", csrf, { tentativa_anterior: previous })).json() as Promise<MailStatus | null>;
}
