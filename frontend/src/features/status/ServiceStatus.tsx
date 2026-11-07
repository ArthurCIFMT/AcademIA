import { useEffect, useState } from "react";

import { getJson } from "../../lib/http";

type Status = "loading" | "online" | "error";

export function ServiceStatus() {
  const [status, setStatus] = useState<Status>("loading");
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    const timer = window.setTimeout(() => {
      controller.abort();
      setStatus("error");
    }, 10000);

    void getJson("/health", controller.signal)
      .then((data) => {
        if (controller.signal.aborted) return;
        const ok = typeof data === "object" && data !== null && "status" in data
          && data.status === "ok";
        setStatus(ok ? "online" : "error");
      })
      .catch(() => {
        if (!controller.signal.aborted) setStatus("error");
      })
      .finally(() => window.clearTimeout(timer));

    return () => {
      window.clearTimeout(timer);
      controller.abort();
    };
  }, [attempt]);

  return (
    <section className="status" aria-labelledby="status-title">
      <h2 id="status-title">Conexão com o sistema</h2>
      {status === "loading" && <p role="status">Verificando conexão…</p>}
      {status === "online" && <p role="status">Sistema disponível.</p>}
      {status === "error" && (
        <>
          <p role="alert">Não foi possível conectar ao sistema.</p>
          <button
            type="button"
            onClick={() => {
              setStatus("loading");
              setAttempt((value) => value + 1);
            }}
          >
            Tentar novamente
          </button>
        </>
      )}
    </section>
  );
}
