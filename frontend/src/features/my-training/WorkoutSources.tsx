import { useEffect, useState } from "react";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { versionContext, type Context } from "../ai-training/api";
import { GenerationDetails } from "../ai-training/GenerationDetails";

export function WorkoutSources({ clientId, versionId, onUnavailable }: {
  clientId: string;
  versionId: string;
  onUnavailable: (status: number) => void;
}) {
  const [opened, setOpened] = useState(false);
  const [result, setResult] = useState<Context | "unavailable" | null>(null);
  useEffect(() => {
    if (!opened) return;
    const controller = new AbortController();
    void versionContext(clientId, versionId, controller.signal).then(value => {
      if (controller.signal.aborted) return;
      if (value.contexto.treino.ficha.estado_publicacao === "CONTEUDO_EXPIRADO") onUnavailable(404);
      else setResult(value);
    }, failure => {
      if (controller.signal.aborted) return;
      if (failure instanceof ApiError && [401, 403].includes(failure.status)) onUnavailable(failure.status);
      else setResult("unavailable");
    });
    return () => controller.abort();
  }, [clientId, versionId, opened, onUnavailable]);

  return <section className="my-training-sources">
    <Button variant="secondary" aria-expanded={opened} aria-controls="my-training-sources" onClick={() => {
      setResult(null);
      setOpened(value => !value);
    }}>{opened ? "Recolher fontes da ficha" : "Ver fontes da ficha"}</Button>
    <div id="my-training-sources" hidden={!opened}>
      {opened && (result === "unavailable" ? <StatusMessage state="conflict"
        title="As fontes desta ficha não estão disponíveis no momento." />
        : result ? <GenerationDetails data={result} technical={false} /> :
          <StatusMessage state="loading" title="Consultando as fontes da ficha…" />)}
    </div>
  </section>;
}
