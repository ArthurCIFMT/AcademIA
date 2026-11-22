import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { reviewPath } from "../training-review/TrainingReview";
import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { ClientWorkspaceNav } from "../assignments/ClientWorkspaceNav";
import { loadWorkspace, loadWorkout, saveWorkout, type Context, type Content, type Day, type History,
  type Item, type Workout } from "./api";
import "./training-editor.css";

const DEFAULT_REST_SECONDS = 60;
const publicationLabels = {
  RASCUNHO: "Rascunho", PUBLICADO: "Ficha vigente", SUBSTITUIDO: "Ficha histórica", CONTEUDO_EXPIRADO: "Conteúdo expirado",
};

function moved<T>(items: T[], index: number, step: number): T[] {
  const copy = [...items];
  [copy[index], copy[index + step]] = [copy[index + step], copy[index]];
  return copy;
}

function Editor({ context, clientId, csrf, initial, onSaved, reload, onOpenRevision, onDenied, onBack, opening }: {
  context: Context; clientId: string; csrf: string;
  initial: { value: Workout | null; copy: boolean };
  onSaved: (value: Workout) => void; reload: () => void;
  onOpenRevision: (id: string) => void; onDenied: () => void; onBack: () => void; opening: boolean;
}) {
  const existing = initial.copy ? null : initial.value;
  const [days, setDays] = useState<Day[]>(() => initial.value?.dias ?? []);
  const [onboardingId, setOnboardingId] = useState(
    initial.copy ? context.onboarding?.id ?? "" : initial.value?.onboarding_id ?? context.onboarding?.id ?? "",
  );
  const [assessment, setAssessment] = useState(initial.copy ? "" : initial.value?.avaliacao_id ?? "");
  const [requestId] = useState(() => crypto.randomUUID());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const writing = useRef<AbortController | null>(null);
  useEffect(() => () => writing.current?.abort(), []);

  function updateDay(index: number, next: Day) {
    setDays(days.map((day, position) => position === index ? next : day));
  }
  function updateItem(dayIndex: number, itemIndex: number, next: Item) {
    updateDay(dayIndex, { ...days[dayIndex],
      itens: days[dayIndex].itens.map((item, position) => position === itemIndex ? next : item) });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (writing.current || opening) return;
    if (!onboardingId) { setError("O cliente precisa concluir o onboarding."); return; }
    if (days.some((day) => day.itens.some((item) => item.equipamento_ids === null))) {
      setError("Selecione uma alternativa de equipamentos para cada exercício.");
      return;
    }
    const content: Content = {
      onboarding_id: onboardingId, avaliacao_id: assessment || null,
      dias: days.map((day, index) => ({ titulo: day.titulo.trim() || `Dia ${index + 1}`, itens: day.itens.map((item) => ({
        exercicio_id: item.exercicio_id, equipamento_ids: item.equipamento_ids,
        series: Number(item.series), repeticoes: item.repeticoes,
        carga_kg: item.carga_kg === "" ? null : item.carga_kg,
        intervalo_segundos: item.intervalo_segundos === "" ? DEFAULT_REST_SECONDS : Number(item.intervalo_segundos),
        cadencia: item.cadencia || null, observacoes: item.observacoes || null,
      })) })),
    };
    setBusy(true);
    setError("");
    setConflict(false);
    const controller = new AbortController();
    writing.current = controller;
    try {
      const saved = await saveWorkout(clientId, csrf, content, requestId, context.versao_atual_id, existing, controller.signal);
      if (!controller.signal.aborted) onSaved(saved);
    } catch (failure) {
      if (controller.signal.aborted) return;
      const status = failure instanceof ApiError ? failure.status : 0;
      if (status === 409 || status === 404) {
        setConflict(true);
        setError("A revisão, o onboarding ou os recursos mudaram. As alterações locais continuam no editor.");
      } else if (status === 401 || status === 403) onDenied();
      else if (status === 422) setError("Revise os campos e a avaliação vinculada.");
      else setError("Não foi possível confirmar o salvamento. A edição continua nesta tela.");
    } finally { writing.current = null; if (!controller.signal.aborted) setBusy(false); }
  }

  return (
    <form className="training-editor" onSubmit={(event) => void submit(event)}>
      <h4>{existing ? "Editar rascunho da versão " + existing.numero : "Novo rascunho manual"}</h4>
      {existing && <p className="instructor-meta">Revisão salva {existing.revisao}</p>}
      {initial.copy && <p>Conteúdo copiado da versão {initial.value?.numero}.</p>}
      <fieldset disabled={busy || opening}>
        <legend>Dados da ficha</legend>
        <label htmlFor="workout-onboarding">Onboarding de referência</label>
        <select id="workout-onboarding" required value={onboardingId} onChange={(event) => {
          setOnboardingId(event.target.value); setAssessment("");
        }}>
          <option value="">Selecione</option>
          {context.onboarding && <option value={context.onboarding.id}>Versão {context.onboarding.numero} atual</option>}
          {onboardingId && onboardingId !== context.onboarding?.id &&
            <option value={onboardingId}>Referência anterior · escolha a versão atual</option>}
        </select>
        <label htmlFor="workout-assessment">Avaliação de referência</label>
        <select id="workout-assessment" value={assessment} onChange={(event) => setAssessment(event.target.value)}>
          <option value="">Sem avaliação vinculada</option>
          {context.avaliacoes.map((item) => <option key={item.id} value={item.id}>
            {new Date(item.registrado_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}
          </option>)}
        </select>
        {days.map((day, dayIndex) => (
          <fieldset key={dayIndex} className="training-day">
            <legend>{day.titulo.trim() || `Dia ${dayIndex + 1}`}</legend>
            <label>Título do dia
              <input maxLength={60} value={day.titulo} placeholder={`Dia ${dayIndex + 1}`}
                onChange={(event) => updateDay(dayIndex, { ...day, titulo: event.target.value })} />
            </label>
            {day.itens.map((item, itemIndex) => {
              const itemId = "workout-item-" + dayIndex + "-" + itemIndex;
              const candidate = context.exercicios.find((option) => option.id === item.exercicio_id);
              const groups = candidate?.combinacoes_disponiveis ?? [];
              const hasOption = groups.some(group => JSON.stringify(group) === JSON.stringify(item.equipamento_ids));
              const unavailable = Boolean(item.exercicio_id) && (!candidate || (item.equipamento_ids !== null && !hasOption));
              const choices = hasOption || item.equipamento_ids === null ? groups : [item.equipamento_ids, ...groups];
              return (
                <fieldset key={itemIndex} className="training-item">
                  <legend>{itemIndex + 1}. {candidate?.nome ?? String(item.exercicio_snapshot?.nome ?? "Exercício")}</legend>
                  <label htmlFor={itemId + "-exercise"}>Exercício</label>
                    <select id={itemId + "-exercise"} required value={item.exercicio_id} onChange={(event) => {
                      const next = context.exercicios.find((option) => option.id === event.target.value);
                      updateItem(dayIndex, itemIndex, { ...item, exercicio_id: event.target.value,
                        equipamento_ids: next?.combinacoes_disponiveis.length === 1 ? next.combinacoes_disponiveis[0] : null });
                    }}>
                      <option value="">Selecione</option>
                      {!candidate && item.exercicio_id && <option value={item.exercicio_id}>
                        {String(item.exercicio_snapshot?.nome ?? item.exercicio_id)} · indisponível
                      </option>}
                      {context.exercicios.map((option) => <option key={option.id} value={option.id}>{option.nome}</option>)}
                    </select>
                  {unavailable && <StatusMessage state="conflict" title="O exercício ou a alternativa usados no rascunho não estão disponíveis.">
                    Confira os recursos atuais e selecione uma opção disponível.
                  </StatusMessage>}
                  <label htmlFor={itemId + "-equipment"}>Alternativa de equipamentos</label>
                    <select id={itemId + "-equipment"} required value={item.equipamento_ids === null ? "" : JSON.stringify(item.equipamento_ids)}
                      onChange={(event) => updateItem(dayIndex, itemIndex,
                        { ...item, equipamento_ids: event.target.value ? JSON.parse(event.target.value) as string[] : null })}>
                      <option value="">Selecione</option>
                      {choices.map((group) => <option key={JSON.stringify(group)} value={JSON.stringify(group)}>
                        {group.length ? group.map((id) => context.equipamentos.find((option) => option.id === id)?.nome ?? "Recurso indisponível").join(" + ") : "Dispensa explícita"}
                      </option>)}
                    </select>
                  <div className="training-numbers">
                  <label>Séries<input required type="number" min={1} max={100} step={1} value={item.series}
                    onChange={(event) => updateItem(dayIndex, itemIndex, { ...item, series: event.target.value })} /></label>
                  <label>Repetições<input required maxLength={40} value={item.repeticoes}
                    onChange={(event) => updateItem(dayIndex, itemIndex, { ...item, repeticoes: event.target.value })} /></label>
                  <label>Carga (kg)<input type="number" min={0} max={999999.99} step="0.01" value={item.carga_kg ?? ""}
                    onChange={(event) => updateItem(dayIndex, itemIndex, { ...item, carga_kg: event.target.value })} /></label>
                  <label>Intervalo (segundos)<input type="number" min={0} max={3600} step={1} value={item.intervalo_segundos}
                    placeholder={String(DEFAULT_REST_SECONDS)} aria-describedby={itemId + "-rest-help"}
                    onChange={(event) => updateItem(dayIndex, itemIndex, { ...item, intervalo_segundos: event.target.value })} /></label>
                  <small id={itemId + "-rest-help"}>Se ficar em branco, o rascunho usa {DEFAULT_REST_SECONDS} segundos. Você pode ajustar antes de publicar.</small>
                  <label>Cadência<input maxLength={40} value={item.cadencia ?? ""}
                    onChange={(event) => updateItem(dayIndex, itemIndex, { ...item, cadencia: event.target.value })} /></label>
                  </div>
                  <label>Observações<textarea maxLength={1000} value={item.observacoes ?? ""}
                    onChange={(event) => updateItem(dayIndex, itemIndex, { ...item, observacoes: event.target.value })} /></label>
                  <div className="training-actions">
                    <button type="button" disabled={itemIndex === 0} onClick={() => updateDay(dayIndex,
                      { ...day, itens: moved(day.itens, itemIndex, -1) })}>Subir exercício</button>
                    <button type="button" disabled={itemIndex === day.itens.length - 1} onClick={() => updateDay(dayIndex,
                      { ...day, itens: moved(day.itens, itemIndex, 1) })}>Descer exercício</button>
                    <Button variant="danger" onClick={() => updateDay(dayIndex,
                      { ...day, itens: day.itens.filter((_, index) => index !== itemIndex) })}>Remover exercício</Button>
                  </div>
                </fieldset>
              );
            })}
            <div className="training-actions">
              <button type="button" disabled={day.itens.length >= 30} onClick={() => updateDay(dayIndex, {
                ...day, itens: [...day.itens, { exercicio_id: "", equipamento_ids: null, series: "",
                  repeticoes: "", carga_kg: null, intervalo_segundos: "", cadencia: null, observacoes: null }],
              })}>Adicionar exercício</button>
              <button type="button" disabled={dayIndex === 0} onClick={() => setDays(moved(days, dayIndex, -1))}>Subir dia</button>
              <button type="button" disabled={dayIndex === days.length - 1} onClick={() => setDays(moved(days, dayIndex, 1))}>Descer dia</button>
              <Button variant="danger" onClick={() => setDays(days.filter((_, index) => index !== dayIndex))}>Remover dia</Button>
            </div>
          </fieldset>
        ))}
        <button type="button" disabled={days.length >= 7} onClick={() => setDays([...days, { titulo: "", itens: [] }])}>Adicionar dia</button>
      </fieldset>
      {error && <StatusMessage state={conflict ? "conflict" : "error"} title={error} />}
      <div className="training-actions">
        <Button type="submit" pending={busy} pendingLabel="Salvando…" disabled={opening || !context.onboarding}>Salvar rascunho</Button>
        <Button variant="secondary" disabled={busy || opening} onClick={reload}>Recarregar opções</Button>
        {conflict && existing && <Button variant="secondary" disabled={busy || opening} onClick={() => onOpenRevision(existing.id)}>
          Descartar edição e abrir revisão salva
        </Button>}
      </div>
      <div className="instructor-actions">
        {existing && !busy && !opening && <Link to={reviewPath(clientId, existing.id)}>Publicar ou avaliar a versão salva</Link>}
        <Button variant="secondary" disabled={busy || opening} onClick={onBack}>
          Descartar alterações não salvas e voltar
        </Button>
      </div>
    </form>
  );
}

function Workspace({ clientId, csrf, userId }: { clientId: string; csrf: string; userId: string }) {
  const [query, setQuery] = useState({ page: 1 });
  const [context, setContext] = useState<Context | null>(null);
  const [history, setHistory] = useState<History | null>(null);
  const [failure, setFailure] = useState<"denied" | "network" | null>(null);
  const [editor, setEditor] = useState<{ value: Workout | null; copy: boolean } | null>(null);
  const [notice, setNotice] = useState("");
  const [openError, setOpenError] = useState("");
  const [opening, setOpening] = useState(false);
  const [formKey, setFormKey] = useState(0);
  const denied = useRef(false);
  const openRequest = useRef<AbortController | null>(null);
  useEffect(() => () => openRequest.current?.abort(), []);

  const denyAccess = useCallback(() => {
    denied.current = true;
    openRequest.current?.abort();
    setEditor(null); setContext(null); setHistory(null); setFailure("denied");
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    void loadWorkspace(clientId, query.page, controller.signal).then(
      (data) => { if (!controller.signal.aborted && !denied.current) { setContext(data.context); setHistory(data.history); setFailure(null); } },
      (error: unknown) => {
        if (controller.signal.aborted || denied.current) return;
        if (error instanceof ApiError && [401, 403].includes(error.status)) {
          denyAccess();
        } else setFailure("network");
      },
    );
    return () => controller.abort();
  }, [clientId, query, denyAccess]);

  useEffect(() => {
    const focus = () => {
      if (!denied.current) setQuery(value => ({ ...value }));
    };
    window.addEventListener("focus", focus);
    return () => window.removeEventListener("focus", focus);
  }, []);

  function reload(page = query.page) {
    setFailure(null); setQuery({ page });
  }
  async function open(versionId: string) {
    if (openRequest.current || denied.current) return;
    const controller = new AbortController();
    openRequest.current = controller;
    setOpening(true); setNotice(""); setOpenError("");
    try {
      const value = await loadWorkout(clientId, versionId, controller.signal);
      if (controller.signal.aborted) return;
      if (value.estado_publicacao === "CONTEUDO_EXPIRADO") {
        setOpenError("O conteúdo desta versão expirou.");
        reload();
        return;
      }
      setEditor({ value, copy: value.estado_publicacao !== "RASCUNHO" || value.autor_id !== userId });
      setFormKey((key) => key + 1);
    } catch (error) {
      if (controller.signal.aborted) return;
      if (error instanceof ApiError && [401, 403].includes(error.status)) denyAccess();
      else setOpenError("Não foi possível abrir a versão. Tente novamente.");
    } finally { openRequest.current = null; if (!controller.signal.aborted) setOpening(false); }
  }
  if (failure === "denied") return <StatusMessage state="error" title="Seu acesso ao treino deste cliente não está disponível." />;
  if (!context || !history) return failure ? (
    <><p role="alert">Não foi possível carregar o editor.</p><button type="button" onClick={() => reload()}>Tentar novamente</button></>
  ) : <p role="status">Carregando fichas…</p>;
  return (
    <>
      <h3>{context.cliente_nome}</h3>
      {!context.onboarding && <p>O cliente precisa concluir o onboarding para salvar a ficha.</p>}
      {notice && <StatusMessage state="success" title={notice} />}
      {openError && <StatusMessage state="error" title={openError} />}
      {failure === "network" && <StatusMessage state="error" title="As opções não foram atualizadas. A edição continua nesta tela." />}
      {editor ? (
        <Editor key={formKey} context={context} clientId={clientId} csrf={csrf}
          initial={editor} reload={() => reload()} opening={opening} onOpenRevision={id => void open(id)}
          onBack={() => { setEditor(null); setNotice(""); setOpenError(""); }} onDenied={denyAccess}
          onSaved={value => {
            if (denied.current) return;
            setEditor({ value, copy: false }); setFormKey(key => key + 1);
            setNotice("Rascunho salvo."); reload(1);
          }} />
      ) : (
        <>
          <Button disabled={opening} onClick={() => {
            setEditor({ value: null, copy: false }); setFormKey((key) => key + 1); setNotice("");
          }}>Novo rascunho manual</Button>
          {history.itens.length === 0 && <StatusMessage state="empty" title="Nenhuma ficha registrada para este cliente." />}
          <ul className="instructor-cards">{history.itens.map(version => (
            <li key={version.id} className="instructor-card">
              <h4>Versão {version.numero} · {publicationLabels[version.estado_publicacao]}</h4>
              <p className="instructor-meta">{version.origem === "MANUAL" ? "Ficha manual" : "Ficha gerada por IA"}</p>
              <p><Link to={reviewPath(clientId, version.id)}>Consultar versão {version.numero}</Link></p>
              {version.estado_publicacao !== "CONTEUDO_EXPIRADO" && <Button variant="secondary" disabled={opening}
                onClick={() => void open(version.id)}>
                {version.estado_publicacao === "RASCUNHO" && version.autor_id === userId ? "Editar rascunho" : "Copiar para novo rascunho"} {version.numero}
              </Button>}
            </li>
          ))}</ul>
          {(history.total > history.limite || history.pagina > 1) && <nav className="training-actions" aria-label="Páginas de fichas">
            <button type="button" disabled={history.pagina <= 1} onClick={() => reload(history.pagina - 1)}>Anterior</button>
            <button type="button" disabled={history.pagina * history.limite >= history.total} onClick={() => reload(history.pagina + 1)}>Próxima</button>
          </nav>}
        </>
      )}
    </>
  );
}

export function WorkoutEditorPage({ csrf, userId }: { csrf: string; userId: string }) {
  const { clientId } = useParams();
  return (
    <section className="instructor-workspace">
      <h2>Fichas de treino</h2>
      {clientId && <ClientWorkspaceNav clientId={clientId} />}
      {clientId && <Workspace key={clientId} clientId={clientId} csrf={csrf} userId={userId} />}
    </section>
  );
}
