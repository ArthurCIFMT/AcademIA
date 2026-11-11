import { requestApi } from "../../lib/api/auth";

export type Resource = { id: string; nome: string; disponivel: boolean };
export type Exercise = {
  id: string;
  nome: string;
  descricao: string;
  grupo_muscular: string;
  ativo: boolean;
  dispensa_equipamento: boolean;
  revisao: number;
  elegivel: boolean;
  combinacoes: Resource[][];
};

export type ExerciseFields = {
  nome: string;
  descricao: string;
  grupo_muscular: string;
  ativo: boolean;
  dispensa_equipamento: boolean;
  combinacoes: string[][];
};

export type ExercisePage = { itens: Exercise[]; pagina: number; limite: number; total: number };

const path = "/v1/exercicios";

export async function exercisePage(page: number, signal: AbortSignal): Promise<ExercisePage> {
  const response = await requestApi(path + "?pagina=" + page, { signal });
  return response.json() as Promise<ExercisePage>;
}

export async function exerciseResources(signal: AbortSignal): Promise<Resource[]> {
  const response = await requestApi(path + "/recursos", { signal });
  return response.json() as Promise<Resource[]>;
}

export async function saveExercise(data: ExerciseFields, csrf: string, exercise?: Exercise) {
  const url = exercise ? path + "/" + encodeURIComponent(exercise.id) : path;
  const body = exercise ? { ...data, revisao: exercise.revisao } : data;
  await requestApi(url, {
    method: exercise ? "PUT" : "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body),
  });
}
