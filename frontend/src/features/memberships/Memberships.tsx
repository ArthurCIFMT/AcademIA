import { useCallback, useEffect, useRef, useState, type FormEvent, type ReactNode } from "react";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { ClientBiometrics } from "../biometrics/ClientBiometrics";
import { listClients, type ClientSummary } from "../clients/api";
import { DirectoryPager, DirectoryTag } from "../clients/directory-ui";
import {
  listActivePlans, listManagedPlans, listMemberships, registerMembership, savePlan,
  type Membership, type Page, type Plan,
} from "./api";
import "./memberships.css";

type Loader<Item> = (page: number, signal: AbortSignal) => Promise<Page<Item>>;

function usePage<Item>(load: Loader<Item>) {
  const [query, setQuery] = useState({ page: 1 });
  const [outcome, setOutcome] = useState<{
    load: Loader<Item>; query: { page: number }; page: Page<Item> | null;
  }>();
  useEffect(() => {
    const controller = new AbortController();
    void load(query.page, controller.signal).then(
      page => { if (!controller.signal.aborted) setOutcome({ load, query, page }); },
      () => { if (!controller.signal.aborted) setOutcome({ load, query, page: null }); },
    );
    return () => controller.abort();
  }, [load, query]);
  const current = outcome?.load === load && outcome.query === query ? outcome : undefined;
  return {
    page: current?.page,
    reload: (page = query.page) => setQuery({ page }),
  };
}

function PageResult<Item>({ result, labels, children }: {
  result: ReturnType<typeof usePage<Item>>;
  labels: { loading: string; error: string; empty: string; pager: string };
  children: (items: Item[]) => ReactNode;
}) {
  const { page, reload } = result;
  if (page === undefined) return <StatusMessage state="loading" title={labels.loading} />;
  if (page === null) return <>
    <StatusMessage state="error" title={labels.error} />
    <Button variant="secondary" onClick={() => reload()}>Tentar novamente</Button>
  </>;
  return <>
    {page.itens.length ? children(page.itens) : <StatusMessage state="empty" title={labels.empty} />}
    <DirectoryPager page={page} label={labels.pager} changePage={reload} />
  </>;
}

const plansLabels = {
  loading: "Carregando planos…", error: "Não foi possível consultar os planos.",
  empty: "Nenhum plano cadastrado.", pager: "Páginas de planos",
};

function accessLimit(limit: number | null) {
  return limit === null ? "Sem limite diário" : limit === 1 ? "1 entrada por dia" : limit + " entradas por dia";
}

function PlanForm({ plan, csrf, close, saved }: {
  plan?: Plan; csrf: string; close: () => void; saved: () => void;
}) {
  const [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const [error, setError] = useState("");
  const [requestId, setRequestId] = useState(() => crypto.randomUUID());

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (locked.current) return;
    const data = new FormData(event.currentTarget);
    const limit = data.get("limite");
    locked.current = true;
    setBusy(true);
    setError("");
    try {
      await savePlan({
        nome: String(data.get("nome")).trim(), modalidade: String(data.get("modalidade")).trim(),
        duracao_dias: Number(data.get("duracao")), limite_acessos: limit ? Number(limit) : null,
        ativo: data.has("ativo"),
      }, csrf, requestId, plan);
      saved();
    } catch (reason) {
      setError(reason instanceof ApiError && reason.status === 409
        ? "Os dados do plano mudaram. Feche o formulário e consulte a versão atual."
        : "Não foi possível salvar o plano. Confira os dados e tente novamente.");
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }

  return <form className="directory-form" aria-label={plan ? "Editar plano" : "Novo plano"}
    onSubmit={event => void submit(event)} onChange={() => setRequestId(crypto.randomUUID())}>
    <fieldset className="directory-group" disabled={busy}>
      <legend>{plan ? "Editar plano" : "Novo plano"}</legend>
      <label>Nome <input name="nome" defaultValue={plan?.nome} required maxLength={100} /></label>
      <label>Modalidade <input name="modalidade" defaultValue={plan?.modalidade} required maxLength={80} /></label>
      <label>Duração em dias <input name="duracao" type="number" required min={1} max={2147483647} defaultValue={plan?.duracao_dias} /></label>
      <label>Entradas por dia <input name="limite" type="number" min={1} max={2147483647} defaultValue={plan?.limite_acessos ?? ""} /></label>
      <p className="directory-meta">Deixe as entradas por dia em branco para acesso sem limite diário.</p>
      <label className="directory-choice"><input type="checkbox" name="ativo" defaultChecked={plan?.ativo ?? true} /> Plano ativo</label>
      <div className="directory-actions">
        <Button type="submit">{busy ? "Salvando…" : "Salvar plano"}</Button>
        <Button variant="secondary" onClick={close}>Cancelar</Button>
      </div>
    </fieldset>
    {error && <StatusMessage state="error" title={error} />}
  </form>;
}

export function PlansPage({ csrf }: { csrf: string }) {
  const plans = usePage(listManagedPlans);
  const [edit, setEdit] = useState<Plan | "new" | null>(null);
  const [notice, setNotice] = useState("");
  return <section className="directory" aria-labelledby="plans-title">
    <h2 id="plans-title">Planos da academia</h2>
    {notice && <p role="status">{notice}</p>}
    {edit === null ? <>
      <Button onClick={() => { setNotice(""); setEdit("new"); }}>Novo plano</Button>
      <PageResult result={plans} labels={plansLabels}>{items => (
        <ul className="directory-cards">{items.map(plan => <li className="directory-card" key={plan.id}>
          <h3>{plan.nome}</h3>
          <DirectoryTag tone={plan.ativo ? "positive" : "neutral"}>{plan.ativo ? "Ativo" : "Inativo"}</DirectoryTag>
          <p>{plan.modalidade} · {plan.duracao_dias} dias · {accessLimit(plan.limite_acessos)}</p>
          <Button variant="secondary" onClick={() => { setNotice(""); setEdit(plan); }}
            aria-label={"Editar plano " + plan.nome}>Editar</Button>
        </li>)}</ul>
      )}</PageResult>
    </> : <PlanForm plan={edit === "new" ? undefined : edit} csrf={csrf}
      close={() => { setEdit(null); plans.reload(); }}
      saved={() => { setEdit(null); setNotice("Plano salvo."); plans.reload(1); }} />}
  </section>;
}

const labels: Record<Membership["situacao"], string> = {
  VIGENTE: "Vigente", FUTURA: "Futura", VENCIDA: "Vencida", ENCERRADA: "Encerrada",
};

function civilLabel(value: string) {
  return value.split("-").reverse().join("/");
}

function shiftDate(value: string, days: number) {
  if (!value) return "";
  const date = new Date(value + "T00:00:00Z");
  date.setUTCDate(date.getUTCDate() + days);
  if (!Number.isFinite(date.getTime()) || date.getUTCFullYear() > 9999) return "";
  return date.toISOString().slice(0, 10);
}

function EnrollForm({ client, csrf, latestEnd, saved }: {
  client: ClientSummary; csrf: string; latestEnd?: string; saved: (message: string) => void;
}) {
  const plans = usePage(listActivePlans);
  const earliest = latestEnd ? shiftDate(latestEnd, 1) : "";
  const [start, setStart] = useState(earliest);
  const [plan, setPlan] = useState<Plan>();
  const [busy, setBusy] = useState(false);
  const locked = useRef(false);
  const [error, setError] = useState("");
  const [requestId, setRequestId] = useState(() => crypto.randomUUID());
  const end = plan ? shiftDate(start, plan.duracao_dias - 1) : "";

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!plan || !start || !end || locked.current) return;
    locked.current = true;
    setBusy(true);
    setError("");
    try {
      const result = await registerMembership(client.id, plan, start, csrf, requestId);
      saved("Matrícula registrada até " + civilLabel(result.fim) + ".");
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        setError("A matrícula não foi registrada. Confira o histórico e selecione um plano atualizado.");
        setPlan(undefined);
        plans.reload(1);
      } else {
        setError("Não foi possível registrar a matrícula. Confira os dados e tente novamente.");
      }
    } finally {
      locked.current = false;
      setBusy(false);
    }
  }

  return <form className="directory-form membership-form" onSubmit={event => void submit(event)}
    onChange={() => setRequestId(crypto.randomUUID())}>
    <fieldset className="directory-group" disabled={busy}>
      <legend>{latestEnd ? "Renovar matrícula" : "Nova matrícula"}</legend>
      <PageResult result={plans} labels={{ ...plansLabels, empty: "Nenhum plano ativo disponível." }}>
        {items => <label>Plano <select value={plan?.id ?? ""} required
          onChange={event => setPlan(items.find(item => item.id === event.target.value))}>
          <option value="">Selecione um plano</option>
          {plan && !items.some(item => item.id === plan.id) && <option value={plan.id}>{plan.nome}</option>}
          {items.map(item => <option key={item.id} value={item.id}>{item.nome} · {item.modalidade}</option>)}
        </select></label>}
      </PageResult>
      <label>Início <input type="date" required value={start} min={earliest || undefined} max="9999-12-31"
        onChange={event => setStart(event.target.value)} /></label>
      {plan && <p>{accessLimit(plan.limite_acessos)}. {end && "Válida até " + civilLabel(end) + ", inclusive."}</p>}
      <Button type="submit" disabled={!plan || !end}>{busy ? "Registrando…" : "Registrar matrícula"}</Button>
    </fieldset>
    {error && <StatusMessage state="error" title={error} />}
  </form>;
}

function ClientMemberships({ client, csrf }: { client: ClientSummary; csrf: string }) {
  const load = useCallback((page: number, signal: AbortSignal) =>
    listMemberships(client.id, page, signal), [client.id]);
  const history = usePage(load);
  const [notice, setNotice] = useState("");
  const eligible = client.ativo && ["ATIVO", "CONVIDADO"].includes(client.estado_conta);
  const firstPage = history.page?.pagina === 1 ? history.page : undefined;
  const latestEnd = firstPage?.itens[0]?.fim;
  return <>
    <h3>Matrículas de {client.nome}</h3>
    {notice && <p role="status">{notice}</p>}
    {eligible && firstPage && <EnrollForm key={latestEnd ?? "first"} client={client} csrf={csrf} latestEnd={latestEnd}
      saved={message => { setNotice(message); history.reload(1); }} />}
    {!eligible && <StatusMessage state="empty" title="O cadastro do cliente está inabilitado para novas matrículas." />}
    <PageResult result={history} labels={{
      loading: "Carregando histórico…", error: "Não foi possível consultar as matrículas.",
      empty: "Ainda não há matrículas para este cliente.", pager: "Páginas de matrículas",
    }}>{items => <ul className="directory-cards" aria-label="Histórico de matrículas">
      {items.map(item => <li className="directory-card" key={item.id}>
        <h4>{item.modalidade_contratada}</h4>
        <p><time dateTime={item.inicio}>{civilLabel(item.inicio)}</time> a <time dateTime={item.fim}>{civilLabel(item.fim)}</time></p>
        <p>{labels[item.situacao]} · {accessLimit(item.limites_snapshot.limite_acessos)}</p>
      </li>)}
    </ul>}</PageResult>
    <Button variant="secondary" onClick={() => history.reload(1)}>Atualizar histórico</Button>
    <ClientBiometrics key={notice} clientId={client.id} csrf={csrf} />
  </>;
}

export function MembershipsPage({ csrf }: { csrf: string }) {
  const [term, setTerm] = useState("");
  const [client, setClient] = useState<ClientSummary>();
  const load = useCallback((page: number, signal: AbortSignal) => listClients(term, page, signal), [term]);
  const clients = usePage(load);
  return <section className="directory" aria-labelledby="memberships-title">
    <h2 id="memberships-title">Matrículas</h2>
    {client ? <>
      <Button variant="secondary" onClick={() => setClient(undefined)}>Trocar cliente</Button>
      <ClientMemberships key={client.id} client={client} csrf={csrf} />
    </> : <>
      <form className="directory-form" onSubmit={event => {
        event.preventDefault();
        setTerm(String(new FormData(event.currentTarget).get("busca")).trim());
        clients.reload(1);
      }}>
        <label>Buscar cliente <input type="search" name="busca" defaultValue={term} maxLength={120} /></label>
        <Button type="submit">Buscar</Button>
      </form>
      <PageResult result={clients} labels={{
        loading: "Carregando clientes…", error: "Não foi possível consultar os clientes.",
        empty: "Nenhum cliente encontrado.", pager: "Páginas de clientes",
      }}>{items => <ul className="directory-cards" aria-label="Clientes">
        {items.map(item => <li className="directory-card" key={item.id}>
          <h3>{item.nome}</h3>
          <p className="directory-meta">{item.email}</p>
          <Button variant="secondary" onClick={() => setClient(item)}
            aria-label={"Ver matrículas de " + item.nome}>Ver matrículas</Button>
        </li>)}
      </ul>}</PageResult>
    </>}
  </section>;
}
