import { useEffect, useState } from "react";

const labels = {
  TREINO_PARA_AVALIAR: "Treino para avaliar",
  ALTERACAO_CRITICA: "Alteração crítica na academia",
};

type Notice = { id: string; tipo: keyof typeof labels; criada_em: string };

type Result =
  | { status: "loading" | "denied" | "failed" }
  | { status: "ready"; notices: Notice[] };

function isNotice(value: unknown): value is Notice {
  if (typeof value !== "object" || value === null) return false;
  const notice = value as Partial<Notice>;
  return typeof notice.id === "string" &&
    (notice.tipo === "TREINO_PARA_AVALIAR" || notice.tipo === "ALTERACAO_CRITICA") &&
    typeof notice.criada_em === "string" &&
    Number.isFinite(Date.parse(notice.criada_em));
}

export function PendingNotices() {
  const [result, setResult] = useState<Result>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();

    async function load() {
      try {
        const base = (import.meta.env.VITE_API_BASE_URL?.trim() || "/api").replace(/\/+$/, "");
        const url = new URL(base + "/v1/notificacoes/pendentes", window.location.origin);
        if (url.origin !== window.location.origin) throw new Error("Origem da API inválida.");
        const response = await fetch(url.pathname, {
          credentials: "same-origin",
          cache: "no-store",
          redirect: "error",
          headers: { Accept: "application/json" },
          signal: controller.signal,
        });
        if (controller.signal.aborted) return;
        if (response.status === 401 || response.status === 403) {
          setResult({ status: "denied" });
          return;
        }
        if (!response.ok) throw new Error("Falha ao consultar notificações.");
        const notices: unknown = await response.json();
        if (!Array.isArray(notices) || !notices.every(isNotice)) {
          throw new Error("Lista de notificações inválida.");
        }
        if (!controller.signal.aborted) setResult({ status: "ready", notices });
      } catch {
        if (!controller.signal.aborted) setResult({ status: "failed" });
      }
    }

    void load();
    return () => controller.abort();
  }, [attempt]);

  return (
    <section aria-labelledby="notificacoes-title">
      <h3 id="notificacoes-title">Avisos pendentes</h3>
      {result.status === "loading" && <p role="status">Carregando avisos…</p>}
      {result.status === "denied" && <p role="alert">Acesso aos avisos indisponível.</p>}
      {result.status === "failed" && (
        <>
          <p role="alert">Não foi possível carregar os avisos.</p>
          <button type="button" onClick={() => {
            setResult({ status: "loading" });
            setAttempt(attempt + 1);
          }}>Tentar novamente</button>
        </>
      )}
      {result.status === "ready" && (result.notices.length === 0
        ? <p>Nenhum aviso pendente.</p>
        : <ul>{result.notices.map((notice) => (
          <li key={notice.id}>
            {labels[notice.tipo]} · <time dateTime={notice.criada_em}>
              {new Date(notice.criada_em).toLocaleString("pt-BR")}
            </time>
          </li>
        ))}</ul>)}
    </section>
  );
}
