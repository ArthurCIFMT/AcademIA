import { useEffect, useRef, useState } from "react";

import { requestApi } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { AccessDecisionStatus, type Decision } from "./AccessDecisionStatus";

export function AccessAuthorization({ eventId, csrf }: { eventId: string; csrf: string }) {
  const [decision, setDecision] = useState<Decision>();
  const [error, setError] = useState(false);
  const [busy, setBusy] = useState(false);
  const pending = useRef<AbortController | null>(null);
  useEffect(() => () => pending.current?.abort(), []);

  async function requestAuthorization() {
    if (pending.current) return;
    const controller = new AbortController();
    pending.current = controller;
    setBusy(true);
    setError(false);
    try {
      const response = await requestApi("/v1/atendimento/acessos/" + encodeURIComponent(eventId) + "/autorizacao", {
        method: "POST", signal: controller.signal, headers: { "X-CSRF-Token": csrf },
      });
      const value = await response.json() as Decision;
      if (!controller.signal.aborted) setDecision(value);
    } catch {
      if (!controller.signal.aborted) setError(true);
    } finally {
      pending.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  const done = decision?.resultado === "DENY" || decision?.comando.estado === "CONFIRMADO" || decision?.comando.estado === "EXPIRADO";
  return <section className="directory-card" aria-label="Autorização da passagem">
    {decision && <AccessDecisionStatus decision={decision} />}
    {error && <StatusMessage state="error" title="Não foi possível consultar a autorização. Tente novamente." />}
    {!done && <Button pending={busy} onClick={() => void requestAuthorization()}>
      {!decision ? "Solicitar autorização" : decision.comando.estado === "FALHOU" ? "Reenviar comando" : "Consultar passagem"}
    </Button>}
  </section>;
}
