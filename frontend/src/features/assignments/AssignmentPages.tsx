import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager, DirectoryTag } from "../clients/directory-ui";
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
import "./client-workspace.css";

function dateLabel(value: string) {
  return new Date(value).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
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
      <form className="directory-actions directory-search" onSubmit={event => {
        event.preventDefault();
        load(String(new FormData(event.currentTarget).get("busca") ?? "").trim(), 1);
      }}>
        <label className="ac-field">Nome ou e-mail do instrutor<input className="ac-field-control" name="busca" type="search"
          maxLength={254} disabled={busy} /></label>
        <Button type="submit" variant="secondary" disabled={busy}>Buscar instrutor</Button>
      </form>
      {options ? (
        <>
          {options.itens.length ? (
            <fieldset className="directory-group" disabled={busy}>
              <legend>Instrutores ativos</legend>
              {options.itens.map(person => (
                <label className="directory-choice" key={person.id}>
                  <input type="radio" name="instrutor" checked={selected === person.id}
                    onChange={() => setSelected(person.id)} />
                  {person.nome} · {person.email}
                </label>
              ))}
              <Button disabled={busy || !selected} onClick={() => onAssign(selected)}>Salvar designação</Button>
            </fieldset>
          ) : <StatusMessage state="empty" title="Nenhum instrutor ativo encontrado." />}
          <DirectoryPager label="Páginas de instrutores" page={options} disabled={busy} changePage={page => load(filter.term, page)} />
        </>
      ) : failed ? (
        <>
          <StatusMessage state="error" title="Não foi possível carregar os instrutores." />
          <Button variant="secondary" onClick={() => load(filter.term, filter.page)}>Tentar novamente</Button>
        </>
      ) : <StatusMessage state="loading" title="Carregando instrutores…" />}
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
  const saving = useRef(false);

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
    if (!view || saving.current) return;
    saving.current = true;
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
      saving.current = false;
      setBusy(false);
    }
  }

  if (!view && loadFailed) return (
    <>
      <StatusMessage state="error" title="Não foi possível consultar a designação." />
      <Button variant="secondary" onClick={() => reload(query.page)}>Tentar novamente</Button>
    </>
  );

  return (
    <>
      {notice && <StatusMessage state="success" title={notice} />}
      {error && (
        <>
          <StatusMessage state="error" title={error} />
          <Button variant="secondary" onClick={() => { setError(""); reload(1); }}>Recarregar designação</Button>
        </>
      )}
      {view ? (
        <>
          <div className="directory-card">
            <h4>{view.cliente.nome}</h4>
            <p>Responsável atual: {view.vigente?.instrutor_nome ?? "Nenhum"}</p>
            {view.vigente && !view.instrutor_ativo && <DirectoryTag tone="attention">Responsável indisponível</DirectoryTag>}
          </div>
          {view.cliente_elegivel
            ? <InstructorPicker busy={busy} onAssign={id => void assign(id)} />
            : <StatusMessage state="empty" title="O perfil do cliente precisa estar habilitado para receber designação." />}
          <h4>Histórico</h4>
          {view.historico.itens.length ? (
            <ul className="directory-cards">{view.historico.itens.map(item => (
              <li className="directory-card" key={item.id}>
                {item.instrutor_nome} · {dateLabel(item.inicio)} até {item.fim && dateLabel(item.fim)}
              </li>
            ))}</ul>
          ) : <p>Nenhuma designação encerrada nesta página.</p>}
          <DirectoryPager label="Páginas do histórico" page={view.historico} disabled={busy} changePage={reload} />
        </>
      ) : <StatusMessage state="loading" title="Carregando designação…" />}
    </>
  );
}

export function AssignmentPage({ csrf }: { csrf: string }) {
  const [params] = useSearchParams();
  const id = params.get("cliente");
  return (
    <section className="directory" aria-labelledby="assignment-title">
      <h3 id="assignment-title">Instrutor responsável</h3>
      <div className="directory-actions"><Link to="/area/administracao/clientes">Voltar ao cadastro de clientes</Link></div>
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
    <section className="instructor-workspace" aria-labelledby="my-clients-title">
      <h2 id="my-clients-title">Meus clientes</h2>
      <div className="instructor-actions">
        <Link to="/area/instrutor/revisoes">Fichas aguardando parecer</Link>
        <Button variant="secondary" disabled={!records && !failed} onClick={() => load(query.page)}>Atualizar clientes</Button>
      </div>
      {records ? (
        <>
          {records.itens.length ? (
            <ul className="instructor-cards">{records.itens.map(item => (
              <li key={item.id} className="instructor-card">
                <h3>{item.nome}</h3>
                <p className="instructor-meta">Sob sua responsabilidade desde <time dateTime={item.inicio}>{dateLabel(item.inicio)}</time></p>
                <div className="instructor-actions">
                  <Link to={encodeURIComponent(item.id) + "/avaliacoes"} aria-label={"Avaliações de " + item.nome}>Avaliações</Link>
                  <Link to={encodeURIComponent(item.id) + "/treinos"} aria-label={"Fichas de " + item.nome}>Fichas de treino</Link>
                </div>
              </li>
            ))}</ul>
          ) : <StatusMessage state="empty" title="Nenhum cliente designado nesta página." />}
          <DirectoryPager label="Páginas dos meus clientes" page={records} changePage={load} />
        </>
      ) : failed ? (
        <>
          <StatusMessage state="error" title="Não foi possível carregar os clientes designados." />
          <Button variant="secondary" onClick={() => load(query.page)}>Tentar novamente</Button>
        </>
      ) : <StatusMessage state="loading" title="Carregando clientes designados…" />}
    </section>
  );
}
