import { requestApi } from "../../lib/api/auth";
import type { FormData } from "./form";

export type Draft = { id: string; numero: number; revisao: number; dados: FormData };
export type Snapshot = Draft & { concluido_em: string };
export type OwnOnboarding = { rascunho: Draft | null; concluido: Snapshot | null };
export type Scope = { kind: "invite"; draftId: string } | { kind: "own"; csrf: string; base: Snapshot | null };

const invited = "/v1/onboarding/convite";
const own = "/v1/onboarding/meu";

export class InviteSessionChanged extends Error {}
export class WebLocksUnavailable extends Error {}

async function withInvitation<T>(run: () => Promise<T>): Promise<T> {
  if (!navigator.locks) throw new WebLocksUnavailable();
  return navigator.locks.request("academia-onboarding-invitation", run);
}

function editRequest(scope: Scope, path: string, method: "PATCH" | "POST", body: object) {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (scope.kind === "own") headers["X-CSRF-Token"] = scope.csrf;
  const request = () => requestApi((scope.kind === "own" ? own : invited) + path, {
    method, headers, body: JSON.stringify(body),
  });
  if (scope.kind === "own") return request();
  return withInvitation(async () => {
    // Outra aba pode ter aberto um convite diferente e substituído o cookie.
    const active = await invitedDraft(AbortSignal.timeout(10000));
    if (active.id !== scope.draftId) throw new InviteSessionChanged();
    return request();
  });
}

export async function ownOnboarding(signal: AbortSignal): Promise<OwnOnboarding> {
  return (await requestApi(own, { signal })).json() as Promise<OwnOnboarding>;
}

export async function invitedDraft(signal: AbortSignal): Promise<Draft> {
  return (await requestApi(invited + "/rascunho", { signal })).json() as Promise<Draft>;
}

export async function openInvitation(token: string): Promise<Draft> {
  return withInvitation(async () => {
    await requestApi(invited + "/troca", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    return invitedDraft(AbortSignal.timeout(10000));
  });
}

export async function saveDraft(scope: Scope, revisao: number | null, dados: FormData): Promise<Draft> {
  const revision = scope.kind === "own" ? { versao_base: scope.base?.id ?? null, revisao } : { revisao };
  return (await editRequest(scope, "/rascunho", "PATCH", { ...revision, dados })).json() as Promise<Draft>;
}

export async function finishDraft(scope: Scope, revisao: number): Promise<Snapshot | null> {
  const revision = scope.kind === "own" ? { versao_base: scope.base?.id ?? null, revisao } : { revisao };
  const response = await editRequest(scope, "/conclusao", "POST", revision);
  return scope.kind === "own" ? response.json() as Promise<Snapshot> : null;
}

export async function confirmUpdate(
  scope: Extract<Scope, { kind: "own" }>, revisao: number | null, dados: FormData,
): Promise<Snapshot> {
  const response = await editRequest(scope, "/atualizacoes", "POST", {
    versao_base: scope.base?.id, revisao, dados, confirmado: true,
  });
  return response.json() as Promise<Snapshot>;
}
