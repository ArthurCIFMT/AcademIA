import { requestApi } from "../../lib/api/auth";
import type { ExerciseCandidate } from "./types";

export type WorkoutMeta = {
  id: string; numero: number; origem: "MANUAL" | "IA"; autor_id: string | null;
  onboarding_id: string; avaliacao_id: string | null; versao_base_id: string | null;
  estado_publicacao: "RASCUNHO" | "PUBLICADO" | "SUBSTITUIDO" | "CONTEUDO_EXPIRADO";
  revisao: number;
};
export type Item = {
  exercicio_id: string; equipamento_ids: string[] | null; series: number | string;
  repeticoes: string; carga_kg: string | number | null; intervalo_segundos: number | string;
  cadencia: string | null; observacoes: string | null; exercicio_snapshot?: Record<string, unknown>;
};
export type Day = { titulo: string; itens: Item[] };
export type Workout = WorkoutMeta & { dias: Day[] };
export type Context = {
  cliente_nome: string; onboarding: { id: string; numero: number } | null;
  avaliacoes: { id: string; registrado_em: string }[]; exercicios: ExerciseCandidate[];
  equipamentos: { id: string; nome: string }[]; versao_atual_id: string | null;
};
export type History = { itens: WorkoutMeta[]; pagina: number; limite: number; total: number };
export type Content = { onboarding_id: string; avaliacao_id: string | null; dias: Day[] };

const base = (id: string) => "/v1/treinos/clientes/" + encodeURIComponent(id);
export async function loadWorkspace(clientId: string, page: number, signal: AbortSignal) {
  const [context, history] = await Promise.all([
    requestApi(base(clientId) + "/contexto", { signal }),
    requestApi(base(clientId) + "/versoes?pagina=" + page, { signal }),
  ]);
  return { context: await context.json() as Context, history: await history.json() as History };
}
export async function loadWorkout(clientId: string, versionId: string): Promise<Workout> {
  return (await requestApi(base(clientId) + "/versoes/" + encodeURIComponent(versionId), {})).json() as Promise<Workout>;
}
export async function saveWorkout(
  clientId: string, csrf: string, content: Content,
  requestId: string, baseId: string | null, existing: Workout | null,
): Promise<Workout> {
  const response = await requestApi(base(clientId) + "/rascunhos" + (existing ? "/" + encodeURIComponent(existing.id) : ""), {
    method: existing ? "PUT" : "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(existing
      ? { ...content, revisao: existing.revisao }
      : { ...content, solicitacao_id: requestId, versao_base_id: baseId }),
  });
  return response.json() as Promise<Workout>;
}
