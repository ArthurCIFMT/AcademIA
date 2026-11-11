import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import {
  assignmentHistory,
  changeAssignment,
  instructorOptions,
  myAssignments,
  type AssignedClient,
  type AssignmentHistory,
  type Instructor,
  type Page,
} from "./api";
import "./assignments.css";

function dateLabel(value: string) {
  return new Date(value).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
}

function Pager({ page, onPage, label }: {
  page: Page<unknown>; onPage: (page: number) => void; label: string;
}) {
  if (page.pagina === 1 && page.total <= page.limite) return null;
  return (
    <nav className="assignments-controls" aria-label={label}>
      <button type="button" onClick={() => onPage(page.pagina - 1)} disabled={page.pagina === 1}>Anterior</button>
      <span>Página {page.pagina}</span>
      <button type="button" onClick={() => onPage(page.pagina + 1)}
        disabled={page.pagina * page.limite >= page.total}>Próxima</button>
    </nav>
  );
}

function InstructorPicker({ busy, onAssign }: { busy: boolean; onAssign: (id: string) => void }) {
  const [filter, setFilter] = useState({ term: "", page: 1 });
  const [options, setOptions] = useState<Page<Instructor> | null>(null);
  const [selected, setSelected] = useState("");
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void instructorOptions(filter.term, filter.page, controller.signal).then(
      result => { if (!controller.signal.aborted) setOptions(result); },
      () => { if (!controller.signal.aborted) setFailed(true); },
    );
    return () => controller.abort();
  }, [filter]);

  function load(term: string, page: number) {
    setOptions(null);
    setFailed(false);
    setSelected("");
    setFilter({ term, page });
  }

  return (
    <>
      <form className="assignments-controls" onSubmit={event => {
        event.preventDefault();
        load(String(new FormData(event.currentTarget).get("busca") ?? "").trim(), 1);
      }}>
        <label>Nome ou e-mail do instrutor<input name="busca" type="search" maxLength={254} disabled={busy} /></label>
        <button type="submit" disabled={busy}>Buscar instrutor</button>
      </form>
      {options ? (
        <>
          {options.itens.length ? (
            <fieldset disabled={busy}>
              <legend>Instrutores ativos</legend>
              {options.itens.map(person => (
                <label className="assignment-choice" key={person.id}>
                  <input type="radio" name="instrutor" checked={selected === person.id}
                    onChange={() => setSelected(person.id)} />
                  {person.nome} · {person.email}
                </label>
              ))}
              <button type="button" disabled={!selected} onClick={() => onAssign(selected)}>Salvar designação</button>
            </fieldset>
          ) : <p>Nenhum instrutor ativo encontrado.</p>}
          <Pager label="Páginas de instrutores" page={options} onPage={page => load(filter.term, page)} />
        </>
      ) : failed ? (
        <>
          <p role="alert">Não foi possível carregar os instrutores.</p>
          <button type="button" onClick={() => load(filter.term, filter.page)}>Tentar novamente</button>
        </>
      ) : <p role="status">Carregando instrutores…</p>}
    </>
  );
}

function ManageAssignments({ clientId, csrf }: { clientId: string; csrf: string }) {
  const [query, setQuery] = useState({ page: 1 });
  const [view, setView] = useState<AssignmentHistory | null>(null);
  const [loadFailed, setLoadFailed] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void assignmentHistory(clientId, query.page, controller.signal).then(
      result => { if (!controller.signal.aborted) setView(result); },
      () => { if (!controller.signal.aborted) setLoadFailed(true); },
    );
    return () => controller.abort();
  }, [clientId, query]);

  function reload(page: number) {
    setView(null);
    setLoadFailed(false);
    setQuery({ page });
  }

  async function assign(instructorId: string) {
    if (!view) return;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await changeAssignment(clientId, instructorId, view.vigente?.id ?? null, csrf);
      setNotice("Designação salva.");
      reload(1);
    } catch (failure) {
      setError(failure instanceof ApiError && failure.status === 409
        ? "A designação mudou ou o instrutor ficou indisponível. Recarregue antes de tentar novamente."
        : "Não foi possível salvar a designação.");
    } finally {
      setBusy(false);
    }
  }

  if (!view && loadFailed) return (
    <>
      <p role="alert">Não foi possível consultar a designação.</p>
      <button type="button" onClick={() => reload(query.page)}>Tentar novamente</button>
    </>
  );

  return (
    <>
      {notice && <p role="status">{notice}</p>}
      {error && (
        <>
          <p role="alert">{error}</p>
          <button type="button" onClick={() => { setError(""); reload(1); }}>Recarregar designação</button>
        </>
      )}
      {view ? (
        <>
          <h4>{view.cliente.nome}</h4>
          <p>Responsável atual: {view.vigente?.instrutor_nome ?? "Nenhum"}</p>
          {view.vigente && !view.instrutor_ativo && <p>O responsável cadastrado está indisponível.</p>}
          {view.cliente_elegivel
            ? <InstructorPicker busy={busy} onAssign={id => void assign(id)} />
            : <p>O perfil do cliente precisa estar habilitado para receber designação.</p>}
          <h4>Histórico</h4>
          {view.historico.itens.length ? (
            <ul>{view.historico.itens.map(item => (
              <li key={item.id}>
                {item.instrutor_nome} · {dateLabel(item.inicio)} até {item.fim && dateLabel(item.fim)}
              </li>
            ))}</ul>
          ) : <p>Nenhuma designação encerrada nesta página.</p>}
          <Pager label="Páginas do histórico" page={view.historico} onPage={reload} />
        </>
      ) : <p role="status">Carregando designação…</p>}
    </>
  );
}

export function AssignmentPage({ csrf }: { csrf: string }) {
  const [params] = useSearchParams();
  const id = params.get("cliente");
  return (
    <section className="assignments-panel" aria-labelledby="assignment-title">
      <h3 id="assignment-title">Instrutor responsável</h3>
      <Link to="/area/administracao/clientes">Voltar ao cadastro de clientes</Link>
      {id ? <ManageAssignments key={id} clientId={id} csrf={csrf} /> : <p>Selecione um cliente no cadastro.</p>}
    </section>
  );
}

export function MyAssignmentsPage() {
  const [query, setQuery] = useState({ page: 1 });
  const [records, setRecords] = useState<Page<AssignedClient> | null>(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void myAssignments(query.page, controller.signal).then(
      result => { if (!controller.signal.aborted) setRecords(result); },
      () => { if (!controller.signal.aborted) setFailed(true); },
    );
    return () => controller.abort();
  }, [query]);

  function load(page: number) {
    setRecords(null);
    setFailed(false);
    setQuery({ page });
  }

  return (
    <section className="assignments-panel" aria-labelledby="my-clients-title">
      <h3 id="my-clients-title">Meus clientes</h3>
      {records ? (
        <>
          {records.itens.length ? (
            <ul>{records.itens.map(item => (
              <li key={item.id}>
                {item.nome} · Desde {dateLabel(item.inicio)}{" "}
                <Link to={encodeURIComponent(item.id) + "/avaliacoes"} aria-label={"Avaliações de " + item.nome}>
                  Avaliações
                </Link>{" "}
                <Link to={encodeURIComponent(item.id) + "/treinos"} aria-label={"Fichas de " + item.nome}>
                  Fichas de treino
                </Link>
              </li>
            ))}</ul>
          ) : <p>Nenhum cliente designado nesta página.</p>}
          <Pager label="Páginas dos meus clientes" page={records} onPage={load} />
        </>
      ) : failed ? (
        <>
          <p role="alert">Não foi possível carregar os clientes designados.</p>
          <button type="button" onClick={() => load(query.page)}>Tentar novamente</button>
        </>
      ) : <p role="status">Carregando clientes designados…</p>}
    </section>
  );
}
