import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "../../lib/api/auth";
import { Button, FormField, StatusMessage } from "../../ui/primitives";
import { downloadTraining, loadTraining, removedVersion, type Workspace } from "./api";
import { opinions, Prescription } from "./Prescription";
import { WorkoutSources } from "./WorkoutSources";
import "./my-training.css";

type Query = { versionId: string | null; revision: number };
type Outcome = { query: Query; data: Workspace } | { query: Query; error: string };
const unavailable = "Seus treinos não estão disponíveis com esta sessão.";

function failureMessage(failure: unknown) {
  if (failure instanceof ApiError && [401, 403].includes(failure.status)) return unavailable;
  return "Não foi possível carregar seus treinos. Tente novamente.";
}

export function MyTrainingPage({ clientId }: { clientId: string }) {
  const [query, setQuery] = useState<Query>({ versionId: null, revision: 0 });
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [day, setDay] = useState<{ versionId: string; index: number } | null>(null);
  const [exporting, setExporting] = useState(false);
  const [exportNotice, setExportNotice] = useState<{ error: boolean; message: string } | null>(null);
  const exportRef = useRef<AbortController | null>(null);
  const focusTarget = useRef<HTMLHeadingElement>(null);
  const focusVersion = useRef(false);
  useEffect(() => () => exportRef.current?.abort(), [clientId]);

  const cancelExport = useCallback(() => {
    exportRef.current?.abort();
    exportRef.current = null;
    setExporting(false);
    setExportNotice(null);
  }, []);

  const reload = useCallback((versionId?: string | null) => {
    cancelExport();
    setQuery(current => ({
      versionId: versionId === undefined ? current.versionId : versionId,
      revision: current.revision + 1,
    }));
  }, [cancelExport]);

  useEffect(() => {
    const controller = new AbortController();
    void loadTraining(clientId, query.versionId, controller.signal).then(
      data => { if (!controller.signal.aborted) setOutcome({ query, data }); },
      failure => { if (!controller.signal.aborted) setOutcome({ query, error: failureMessage(failure) }); },
    );
    return () => controller.abort();
  }, [clientId, query]);

  useEffect(() => {
    const refresh = () => reload();
    window.addEventListener("focus", refresh);
    return () => window.removeEventListener("focus", refresh);
  }, [reload]);

  const ready = outcome?.query === query ? outcome : null;
  const workspace = ready && "data" in ready ? ready.data : null;
  const workout = workspace?.workout;
  const current = workspace?.history.itens.find(item => item.id === workspace.history.versao_vigente_id);
  const selectedDay = day && workout && day.versionId === workout.ficha.id ? day.index : 0;
  useEffect(() => {
    if (ready && focusVersion.current) {
      focusVersion.current = false;
      focusTarget.current?.focus();
    }
  }, [ready]);

  function selectVersion(versionId: string | null) {
    focusVersion.current = true;
    setDay(null);
    reload(versionId);
  }

  const showUnavailable = useCallback((status: number) => {
    cancelExport();
    if (status === 404 && workspace && workout) {
      setOutcome({ query, data: removedVersion(workspace.history, workout.ficha.id) });
    } else setOutcome({ query, error: unavailable });
  }, [cancelExport, query, workspace, workout]);

  async function exportWorkout() {
    if (!workout || exportRef.current) return;
    const controller = new AbortController();
    exportRef.current = controller;
    setExporting(true);
    setExportNotice(null);
    try {
      await downloadTraining(clientId, workout.ficha.id, controller.signal);
      if (!controller.signal.aborted) setExportNotice({ error: false, message: "Arquivo JSON preparado para download." });
    } catch (failure) {
      if (controller.signal.aborted) return;
      if (failure instanceof ApiError && [401, 403, 404].includes(failure.status)) showUnavailable(failure.status);
      else setExportNotice({ error: true, message: "Não foi possível exportar a ficha. Tente novamente." });
    } finally {
      if (exportRef.current === controller) {
        exportRef.current = null;
        setExporting(false);
      }
    }
  }

  return <section className="my-training">
    <div className="my-training-title">
      <h2>Meus treinos</h2>
      <Button variant="secondary" disabled={!ready || exporting} onClick={() => reload()}>Atualizar fichas</Button>
    </div>
    {!ready && <StatusMessage state="loading" title="Carregando seus treinos…" />}
    {ready && "error" in ready && <>
      <h3 ref={focusTarget} tabIndex={-1}>Consulta indisponível</h3>
      <StatusMessage state="error" title={ready.error} />
      <Button variant="secondary" onClick={() => reload(query.versionId)}>Tentar novamente</Button>
    </>}
    {workspace && <>
      {workspace.history.itens.length > 0 && <details className="my-training-history" open={query.versionId !== null || undefined}>
        <summary>Histórico de versões</summary>
        <FormField label="Versão da ficha">{field =>
          <select {...field} disabled={exporting} value={workout?.ficha.id ?? ""}
            onChange={event => selectVersion(event.target.value === workspace.history.versao_vigente_id ? null : event.target.value)}>
            {!workout && <option value="" disabled>Selecione uma versão disponível</option>}
            {workspace.history.itens.map(version => <option key={version.id} value={version.id}>
              Versão {version.numero} · {version.vigente ? "Vigente" : "Histórica"} · {opinions[version.parecer_estado]}
            </option>)}
          </select>
        }</FormField>
      </details>}
      {workspace.removed && <>
        <h3 ref={focusTarget} tabIndex={-1}>Versão indisponível</h3>
        <StatusMessage state="conflict" title="A versão selecionada deixou de estar disponível." />
      </>}
      {(!workout || !workout.ficha.vigente) && (workspace.removed || current) &&
        <div className="my-training-current">
          {current && <p>Ficha vigente · Versão {current.numero}</p>}
          <Button variant="secondary" disabled={exporting} onClick={() => selectVersion(null)}>Ver ficha vigente</Button>
        </div>}
      {!workspace.removed && !workout && <StatusMessage state="empty" title="Você ainda não possui uma ficha publicada." />}
      {workout && <>
        <h3 ref={focusTarget} tabIndex={-1}>
          Versão {workout.ficha.numero} · {workout.ficha.vigente ? "Vigente" : "Histórica"}
        </h3>
        <Prescription workout={workout} selectedDay={selectedDay}
          onSelectDay={index => setDay({ versionId: workout.ficha.id, index })} />
        <div className="my-training-actions">
          <Button variant="secondary" pending={exporting} pendingLabel="Exportando…"
            onClick={() => void exportWorkout()}>Exportar ficha em JSON</Button>
          {workout.ficha.origem === "IA" && <WorkoutSources clientId={clientId} versionId={workout.ficha.id}
            onUnavailable={showUnavailable} />}
        </div>
      </>}
    </>}
    {exportNotice && <StatusMessage state={exportNotice.error ? "error" : "success"} title={exportNotice.message} />}
  </section>;
}
