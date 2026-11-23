import { useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager, DirectoryTag, useDirectoryFocus } from "../clients/directory-ui";
import { cancelClass, managedClasses, publicClasses, saveClass,
  type ClassFields, type ClassPage, type ManagedClass, type PublicClass } from "./api";
import { academyIsoTime, academyLocalTime, scheduleTime } from "./schedule-time";
import "./classes.css";

type Loader<T> = (page: number, signal: AbortSignal) => Promise<ClassPage<T>>;

function useSchedule<T>(load: Loader<T>) {
  const [query, setQuery] = useState({ page: 1 });
  const [result, setResult] = useState<ClassPage<T> | null>(null);
  const [failed, setFailed] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    void load(query.page, controller.signal).then(
      (page) => { if (!controller.signal.aborted) setResult(page); },
      () => { if (!controller.signal.aborted) setFailed(true); },
    );
    return () => controller.abort();
  }, [load, query]);

  function reload(page = query.page) {
    setFailed(false);
    setResult(null);
    setQuery({ page });
  }

  return { result, failed, reload };
}

function ScheduleList<T extends PublicClass>({ result, failed, reload, empty, actions, cardHeading: Heading = "h3" }: {
  result: ClassPage<T> | null;
  failed: boolean;
  reload: (page?: number) => void;
  empty: string;
  actions?: (item: T) => ReactNode;
  cardHeading?: "h2" | "h3";
}) {
  if (failed) return <>
    <StatusMessage state="error" title="Não foi possível consultar a agenda." />
    <Button variant="secondary" onClick={() => reload()}>Tentar novamente</Button>
  </>;
  if (!result) return <StatusMessage state="loading" title="Carregando agenda…" />;
  return <>
    {result.itens.length ? <ul className="directory-cards" aria-label="Aulas da academia">
      {result.itens.map(item => <li className="directory-card" key={item.id}>
        <Heading className="class-card-title">{item.nome}</Heading>
        <p className="directory-meta">
          <time dateTime={item.inicio}>{scheduleTime.format(new Date(item.inicio))}</time>
          {" até "}<time dateTime={item.fim}>{scheduleTime.format(new Date(item.fim))}</time>
        </p>
        {item.descricao && <p className="class-description">{item.descricao}</p>}
        {actions?.(item)}
      </li>)}
    </ul> : <StatusMessage state="empty" title={empty} />}
    <DirectoryPager page={result} label="Páginas da agenda" changePage={reload} />
  </>;
}

export function PublicClassSchedule({ inClientArea = false }: { inClientArea?: boolean }) {
  const schedule = useSchedule(publicClasses);
  const Heading = inClientArea ? "h2" : "h1";
  return <section className="directory" aria-labelledby="public-schedule">
    <Heading id="public-schedule">Agenda de aulas</Heading>
    {!inClientArea && <p><Link to="/">Voltar ao início</Link></p>}
    <p className="directory-meta">Horários de São Paulo.</p>
    <ScheduleList {...schedule} empty="Nenhuma aula agendada no momento." cardHeading={inClientArea ? "h3" : "h2"} />
  </section>;
}

type Draft = { action: "edit"; item?: ManagedClass } | { action: "cancel"; item: ManagedClass };

function ScheduleForm({ draft, csrf, close, saved }: {
  draft: Draft; csrf: string; close: () => void; saved: (message: string) => void;
}) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [requestId] = useState(() => crypto.randomUUID());
  const pending = useRef(false);
  const item = draft.item;
  const [startDate, startTime] = item ? academyLocalTime(item.inicio).split("T") : [];
  const [endDate, endTime] = item ? academyLocalTime(item.fim).split("T") : [];

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const fields = new FormData(event.currentTarget);
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      if (draft.action === "cancel") {
        await cancelClass(draft.item, csrf);
        saved("Aula cancelada.");
        return;
      }
      const nome = String(fields.get("nome") ?? "").trim();
      const inicio = academyIsoTime(String(fields.get("start-date")), String(fields.get("start-time")), item?.inicio);
      const fim = academyIsoTime(String(fields.get("end-date")), String(fields.get("end-time")), item?.fim);
      if (!nome || !inicio || !fim || Date.parse(fim) <= Date.parse(inicio)) {
        setError("Informe o nome e horários válidos. O término precisa ser depois do início.");
        return;
      }
      const data: ClassFields = { nome, inicio, fim, descricao: String(fields.get("descricao") ?? "").trim() || null };
      await saveClass(data, csrf, requestId, item);
      saved(item ? "Aula atualizada." : "Aula cadastrada.");
    } catch (failure) {
      const status = failure instanceof ApiError ? failure.status : 0;
      if (status === 409) setError("A agenda mudou. Volte à lista e confira o registro antes de tentar de novo.");
      else if (status === 422) setError("Confira o nome, a descrição e os horários informados.");
      else if (status === 401 || status === 403) setError("Sua sessão perdeu a permissão para gerenciar aulas.");
      else setError("Não foi possível confirmar a operação. Tente novamente.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return <form className="directory-form" onSubmit={event => void submit(event)}>
    {draft.action === "cancel"
      ? <p>Ao cancelar <strong>{draft.item.nome}</strong>, ela sai da agenda pública e permanece no histórico.</p>
      : <fieldset className="directory-group" disabled={busy}>
        <legend>Informações da aula</legend>
        <label className="ac-field">Nome da aula<input name="nome" required maxLength={120} defaultValue={item?.nome} /></label>
        <p className="directory-meta">Informe os horários de São Paulo.</p>
        <div className="class-time-fields">
          <label className="ac-field">Data de início<input name="start-date" type="date" required defaultValue={startDate} /></label>
          <label className="ac-field">Hora de início<input name="start-time" type="time" required defaultValue={startTime} /></label>
          <label className="ac-field">Data de término<input name="end-date" type="date" required defaultValue={endDate} /></label>
          <label className="ac-field">Hora de término<input name="end-time" type="time" required defaultValue={endTime} /></label>
        </div>
        <label className="ac-field">Descrição (opcional)<textarea name="descricao" maxLength={1000} defaultValue={item?.descricao ?? ""} /></label>
      </fieldset>}
    {error && <StatusMessage state="error" title={error} />}
    <div className="directory-actions">
      <Button type="submit" variant={draft.action === "cancel" ? "danger" : "primary"} pending={busy}>
        {draft.action === "cancel" ? "Confirmar cancelamento" : "Salvar aula"}
      </Button>
      <Button variant="secondary" disabled={busy} onClick={close}>Voltar à agenda</Button>
    </div>
  </form>;
}

export function AdminClassSchedule({ csrf }: { csrf: string }) {
  const schedule = useSchedule(managedClasses);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [notice, setNotice] = useState("");
  const heading = useDirectoryFocus(draft !== null);

  function open(next: Draft) {
    setNotice("");
    setDraft(next);
  }

  function close() {
    setDraft(null);
    schedule.reload();
  }

  return <section className="directory" aria-labelledby="admin-schedule">
    <h2 id="admin-schedule" ref={heading} tabIndex={-1}>
      {draft ? draft.action === "cancel" ? "Cancelar aula" : draft.item ? "Editar aula" : "Cadastrar aula"
        : "Gerenciar aulas"}
    </h2>
    {notice && <StatusMessage state="success" title={notice} />}
    {draft ? <ScheduleForm draft={draft} csrf={csrf} close={close} saved={message => {
      setNotice(message);
      setDraft(null);
      schedule.reload(1);
    }} /> : <>
      <div className="directory-actions">
        <Button onClick={() => open({ action: "edit" })}>Cadastrar aula</Button>
      </div>
      <p className="directory-meta">Horários de São Paulo.</p>
      <ScheduleList {...schedule} empty="Nenhuma aula cadastrada." actions={item => <>
        <p><DirectoryTag tone={item.estado === "CANCELADA" ? "attention" : "positive"}>
          {item.estado === "CANCELADA" ? "Cancelada" : "Agendada"}
        </DirectoryTag></p>
        {item.estado === "AGENDADA" && <div className="directory-actions">
          <Button variant="secondary" aria-label={"Editar aula " + item.nome} onClick={() => open({ action: "edit", item })}>Editar</Button>
          <Button variant="danger" aria-label={"Cancelar aula " + item.nome} onClick={() => open({ action: "cancel", item })}>Cancelar aula</Button>
        </div>}
      </>} />
    </>}
  </section>;
}
