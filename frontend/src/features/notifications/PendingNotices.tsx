import { useEffect, useState } from "react";
import { Button, Card, StatusMessage } from "../../ui/primitives";
import "./notifications.css";

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
    <Card title="Avisos pendentes">
      {result.status === "loading" && <StatusMessage state="loading" title="Carregando avisos…" />}
      {result.status === "denied" && <StatusMessage state="error" title="Acesso aos avisos indisponível." />}
      {result.status === "failed" && (
        <div className="notice-actions">
          <StatusMessage state="error" title="Não foi possível carregar os avisos." />
          <Button onClick={() => {
            setResult({ status: "loading" });
            setAttempt(attempt + 1);
          }}>Tentar novamente</Button>
        </div>
      )}
      {result.status === "ready" && (result.notices.length === 0
        ? <StatusMessage state="empty" title="Nenhum aviso pendente." />
        : <ul className="notice-list">{result.notices.map((notice) => (
          <li key={notice.id}>
            {labels[notice.tipo]} · <time dateTime={notice.criada_em}>
              {new Date(notice.criada_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}
            </time>
          </li>
        ))}</ul>)}
    </Card>
  );
}
