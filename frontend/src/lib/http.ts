export async function getJson(path: string, signal: AbortSignal): Promise<unknown> {
  const baseUrl = (import.meta.env.VITE_API_BASE_URL?.trim() || "/api").replace(/\/+$/, "");
  const response = await fetch(baseUrl + path, {
    signal,
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error("Falha na consulta à API.");
  return response.json();
}
