import { requestApi } from "../../lib/api/auth";
import type { FormData } from "../onboarding/form";

export type Assessment = {
  id: string;
  onboarding_id: string;
  instrutor_id: string;
  instrutor_nome: string;
  registrado_em: string;
  observacao: string | null;
};

export type AssessmentHistory = {
  cliente_nome: string;
  snapshot: { id: string; numero: number; dados: FormData } | null;
  historico: { itens: Assessment[]; pagina: number; limite: number; total: number };
};

export type AssessmentRequest = { onboarding_id: string; solicitacao_id: string; observacao: string };

function endpoint(clientId: string) {
  return "/v1/onboarding/clientes/" + encodeURIComponent(clientId) + "/avaliacoes";
}

export async function getAssessments(clientId: string, page: number, signal: AbortSignal): Promise<AssessmentHistory> {
  const response = await requestApi(endpoint(clientId) + "?pagina=" + page, { signal });
  return response.json() as Promise<AssessmentHistory>;
}

export async function createAssessment(clientId: string, csrf: string, body: AssessmentRequest) {
  await requestApi(endpoint(clientId), {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
    body: JSON.stringify(body),
  });
}
