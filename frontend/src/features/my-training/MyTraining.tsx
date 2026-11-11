import { useEffect, useRef, useState } from "react";

import { ApiError } from "../../lib/api/auth";
import { downloadTraining, loadTraining, type OpinionState, type Workspace, type Workout } from "./api";
import "./my-training.css";

type Query = { versionId: string | null; revision: number };
type Outcome = { query: Query; data: Workspace } | { query: Query; error: string };
const opinions: Record<OpinionState, string> = { PENDENTE: "Pendente", ACEITO: "Aceito", REJEITADO: "Rejeitado" };
const when = (value: string) => new Date(value).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
const weight = (value: string) => new Intl.NumberFormat("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(Number(value));

function failureMessage(failure: unknown) {
  if (failure instanceof ApiError) {
    if ([401, 403].includes(failure.status)) return "Seus treinos não estão disponíveis com esta sessão.";
    if (failure.status === 404) return "Esta versão não está mais disponível. Atualize para consultar a ficha vigente.";
  }
  return "Não foi possível carregar seus treinos. Tente novamente.";
}

function Prescription({ workout }: { workout: Workout }) {
  return <article className="my-training-prescription" aria-label={"Ficha da versão " + workout.ficha.numero}>
    <h4>Versão {workout.ficha.numero} · {workout.ficha.vigente ? "Vigente" : "Histórica"}</h4>
    <p>Publicada em {when(workout.ficha.publicada_em)}</p>
    <p>Origem · {workout.ficha.origem === "MANUAL" ? "Manual" : "Gerada por IA"}</p>
    {workout.ficha.autor_id && <p>Identificação do autor · {workout.ficha.autor_id}</p>}
    <section className="my-training-opinion" aria-label="Parecer do instrutor">
      <h5>Parecer do instrutor · {opinions[workout.parecer.estado]}</h5>
      {workout.parecer.estado === "PENDENTE" && <p>Você pode consultar esta ficha enquanto aguarda o parecer.</p>}
      {workout.parecer.estado === "REJEITADO" && <p>A rejeição fica registrada e a ficha continua disponível para consulta.</p>}
      {workout.parecer.motivo && <p>Motivo · {workout.parecer.motivo}</p>}
      {workout.parecer.instrutor_id && <p>Responsável pelo parecer · {workout.parecer.instrutor_id}</p>}
      {workout.parecer.criado_em && <p>Registrado em {when(workout.parecer.criado_em)}</p>}
    </section>
    {workout.ficha.dias.map((day, dayIndex) => <section className="my-training-day" key={dayIndex}>
      <h5>{day.titulo}</h5>
      <ol>{day.itens.map((item, index) => {
        const equipment = item.equipamento_ids.map((id) => workout.equipamentos.find((entry) => entry.id === id));
        const unavailable = equipment.some((entry) => !entry?.disponivel);
        return <li className="my-training-item" key={index}>
          <h6>{item.exercicio_snapshot.nome}</h6>
          {item.exercicio_snapshot.descricao && <p>{item.exercicio_snapshot.descricao}</p>}
          <dl>
            <div><dt>Séries</dt><dd>{item.series}</dd></div>
            <div><dt>Repetições</dt><dd>{item.repeticoes}</dd></div>
            <div><dt>Carga</dt><dd>{item.carga_kg === null ? "Não informada" : weight(item.carga_kg) + " kg"}</dd></div>
            <div><dt>Intervalo</dt><dd>{item.intervalo_segundos} segundos</dd></div>
            <div><dt>Cadência</dt><dd>{item.cadencia ?? "Não informada"}</dd></div>
          </dl>
          {item.observacoes && <p>Observações · {item.observacoes}</p>}
          <p>Equipamentos · {equipment.length
            ? equipment.map((entry) => entry?.nome ?? "Equipamento não encontrado").join(" + ")
            : item.exercicio_snapshot.dispensa_equipamento ? "Dispensa explícita de equipamento" : "Recursos não informados"}</p>
          {unavailable && <p role="note" className="my-training-warning">
            Há equipamento indisponível neste exercício. Consulte seu instrutor. A prescrição original foi preservada.
          </p>}
        </li>;
      })}</ol>
    </section>)}
    <p>Disponibilidade dos equipamentos consultada em {when(workout.consultado_em)}.</p>
  </article>;
}

export function MyTrainingPage({ clientId }: { clientId: string }) {
  const [query, setQuery] = useState<Query>({ versionId: null, revision: 0 });
  const [outcome, setOutcome] = useState<Outcome | null>(null);
  const [exporting, setExporting] = useState(false);
  const exportRef = useRef<AbortController | null>(null);
  useEffect(() => () => exportRef.current?.abort(), [clientId]);
  const [exportNotice, setExportNotice] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    void loadTraining(clientId, query.versionId, controller.signal).then(
      (data) => { if (!controller.signal.aborted) setOutcome({ query, data }); },
      (failure: unknown) => { if (!controller.signal.aborted) setOutcome({ query, error: failureMessage(failure) }); },
    );
    const refresh = () => {
      setExportNotice("");
      setQuery((current) => ({ ...current, revision: current.revision + 1 }));
    };
    window.addEventListener("focus", refresh);
    return () => { controller.abort(); window.removeEventListener("focus", refresh); };
  }, [clientId, query]);
  const ready = outcome?.query === query ? outcome : null;
  const workspace = ready && "data" in ready ? ready.data : null;
  const workout = workspace?.workout;
  function reload(versionId = query.versionId) {
    setExportNotice("");
    setQuery({ versionId, revision: query.revision + 1 });
  }
  async function exportWorkout() {
    if (!workout || exporting) return;
    const controller = new AbortController();
    exportRef.current = controller;
    setExporting(true); setExportNotice("");
    try {
      await downloadTraining(clientId, workout.ficha.id, controller.signal);
      setExportNotice("Arquivo JSON preparado para download.");
    } catch (failure) {
      if (controller.signal.aborted) return;
      if (failure instanceof ApiError && [401, 403, 404].includes(failure.status)) {
        setOutcome({ query, error: failureMessage(failure) });
      } else setExportNotice("Não foi possível exportar a ficha. Tente novamente.");
    } finally { setExporting(false); }
  }
  return <section className="my-training">
    <h3>Meus treinos</h3>
    <button type="button" disabled={!ready || exporting} onClick={() => reload()}>Atualizar fichas</button>
    {!ready && <p role="status">Carregando seus treinos…</p>}
    {ready && "error" in ready && <>
      <p role="alert">{ready.error}</p>
      <button type="button" onClick={() => reload(null)}>Tentar novamente</button>
    </>}
    {workspace?.removed && <>
      <p role="status">A versão selecionada deixou de estar disponível.</p>
      <button type="button" onClick={() => reload(null)}>Ver ficha vigente</button>
    </>}
    {workspace && !workspace.removed && !workout && <p>Você ainda não possui uma ficha publicada.</p>}
    {workspace && workspace.history.itens.length > 0 && <>
      <label htmlFor="my-training-version">Versão da ficha</label>
      <select id="my-training-version" disabled={exporting} value={workout?.ficha.id ?? ""}
        onChange={(event) => reload(event.target.value)}>
        {!workout && <option value="">Selecione uma versão disponível</option>}
        {workspace.history.itens.map((version) => <option key={version.id} value={version.id}>
          Versão {version.numero} · {version.vigente ? "Vigente" : "Histórica"} · {opinions[version.parecer_estado]}
        </option>)}
      </select>
    </>}
    {workout && <>
      <Prescription workout={workout} />
      <button type="button" disabled={exporting} onClick={() => void exportWorkout()}>
        {exporting ? "Exportando…" : "Exportar ficha em JSON"}
      </button>
    </>}
    {exportNotice && <p role="status">{exportNotice}</p>}
  </section>;
}
