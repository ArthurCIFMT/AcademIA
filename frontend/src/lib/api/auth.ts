export const roles = ["ADMINISTRADOR", "ATENDENTE", "INSTRUTOR", "CLIENTE"] as const;
export type Role = (typeof roles)[number];

export type LoginCredentials = { email: string; senha: string };

export type Session = {
  user_id: string;
  expires_at: string;
  csrf_token: string;
  roles: Role[];
};

export class ApiError extends Error {
  constructor(readonly status: number) {
    super("Falha na requisição de autenticação.");
  }
}

async function request(path: string, options: RequestInit): Promise<Response> {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL?.trim() || "/api").replace(/\/+$/, "");
  const url = new URL(baseUrl + "/v1/auth/" + path, window.location.origin);
  if (url.origin !== window.location.origin) {
    throw new Error("A API de autenticação precisa estar na mesma origem.");
  }

  const response = await fetch(url.pathname, {
    ...options,
    redirect: "error",
    cache: "no-store",
    credentials: "same-origin",
    headers: { Accept: "application/json", ...options.headers },
  });
  if (!response.ok) throw new ApiError(response.status);
  return response;
}

function isRole(value: unknown): value is Role {
  return roles.some((role) => role === value);
}

async function readSession(response: Response): Promise<Session> {
  const data = (await response.json()) as Partial<Session> | null;
  if (
    !data ||
    typeof data.user_id !== "string" ||
    typeof data.expires_at !== "string" ||
    !Number.isFinite(Date.parse(data.expires_at)) ||
    typeof data.csrf_token !== "string" ||
    !data.csrf_token ||
    !Array.isArray(data.roles) ||
    !data.roles.every(isRole)
  ) {
    throw new Error("Resposta de sessão inválida.");
  }
  return {
    user_id: data.user_id,
    expires_at: data.expires_at,
    csrf_token: data.csrf_token,
    roles: data.roles,
  };
}

export async function login(credentials: LoginCredentials, signal: AbortSignal) {
  return readSession(await request("login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(credentials),
    signal,
  }));
}

export async function getSession(signal: AbortSignal) {
  return readSession(await request("session", { signal }));
}

export async function logout(csrfToken: string, signal: AbortSignal) {
  const response = await request("logout", {
    method: "POST",
    headers: { "X-CSRF-Token": csrfToken },
    signal,
  });
  if (response.status !== 204) throw new Error("Saída sem confirmação da API.");
}


async function postRecovery(path: string, body: object, expectedStatus: number) {
  const response = await request(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (response.status !== expectedStatus) throw new Error("Resposta de recuperação inválida.");
}

export function requestRecovery(email: string) {
  return postRecovery("recovery", { email }, 202);
}

export function confirmRecovery(token: string, senha: string) {
  return postRecovery("recovery/confirm", { token, senha }, 204);
}
