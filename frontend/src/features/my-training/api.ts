import { requestApi } from "../../lib/api/auth";

export type OpinionState = "PENDENTE" | "ACEITO" | "REJEITADO";
export type Summary = {
  id: string; numero: number; origem: "MANUAL" | "IA"; autor_id: string | null;
  publicada_em: string; vigente: boolean; parecer_estado: OpinionState;
};
export type History = { schema_version: 1; versao_vigente_id: string | null; itens: Summary[] };
export type Item = {
  exercicio_id: string; equipamento_ids: string[]; series: number; repeticoes: string;
  carga_kg: string | null; intervalo_segundos: number; cadencia: string | null;
  observacoes: string | null;
  exercicio_snapshot: { nome: string; descricao: string; grupo_muscular: string; dispensa_equipamento: boolean };
};
export type Workout = {
  schema_version: 1; consultado_em: string;
  ficha: Omit<Summary, "parecer_estado"> & { dias: { titulo: string; itens: Item[] }[] };
  parecer: { estado: OpinionState; motivo: string | null; instrutor_id: string | null; criado_em: string | null };
  equipamentos: { id: string; nome: string; disponivel: boolean }[];
};
export type Workspace = { history: History; workout: Workout | null; removed: boolean };
const base = (clientId: string) => "/v1/treinos/clientes/" + encodeURIComponent(clientId) + "/publicadas";

export async function loadTraining(clientId: string, versionId: string | null, signal: AbortSignal): Promise<Workspace> {
  const history = await (await requestApi(base(clientId), { signal })).json() as History;
  const selected = versionId ?? history.versao_vigente_id;
  if (!selected) return { history, workout: null, removed: false };
  if (!history.itens.some((item) => item.id === selected)) return { history, workout: null, removed: true };
  const workout = await (await requestApi(base(clientId) + "/" + encodeURIComponent(selected) + "/ficha", { signal })).json() as Workout;
  return { history, workout, removed: false };
}

export async function downloadTraining(clientId: string, versionId: string, signal: AbortSignal) {
  const response = await requestApi(base(clientId) + "/" + encodeURIComponent(versionId) + "/exportacao", { signal });
  const blob = await response.blob();
  signal.throwIfAborted();
  const filename = response.headers.get("Content-Disposition")?.match(/filename="([a-zA-Z0-9._-]+\.json)"/)?.[1]
    ?? "academia-treino.json";
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  try {
    document.body.append(anchor);
    anchor.click();
  } finally {
    anchor.remove();
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}
