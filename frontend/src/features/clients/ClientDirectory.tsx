import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError, type Session } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { changeClient, getClient, listClients, type ClientDetail, type ClientPage } from "./api";
import { DirectoryPager, DirectoryTag, FirstAccessInvite, useDirectoryFocus } from "./directory-ui";

const ageFormat = new Intl.NumberFormat("pt-BR", { style: "unit", unit: "year", unitDisplay: "long" });

const accountLabels = {
  CONVIDADO: "Aguardando primeiro acesso",
  ATIVO: "Conta ativa",
  INATIVO: "Conta inativa",
  BLOQUEADO: "Conta bloqueada",
};
function clientBirthDateRange() {
  const today = new Intl.DateTimeFormat("sv-SE", { timeZone: "America/Sao_Paulo" }).format(new Date());
  const [year, month, day] = today.split("-").map(Number);
  const earliest = new Date(Date.UTC(year - 100, month - 1, day));
  if (earliest.getUTCMonth() === month - 1) earliest.setUTCDate(earliest.getUTCDate() + 1);
  return { min: earliest.toISOString().slice(0, 10), max: today };
}

function message(failure: unknown) {
  if (failure instanceof ApiError) {
    if (failure.status === 409) return "Operação em conflito. Confira o e-mail, o CPF e o vínculo ou recarregue o cadastro.";
    if (failure.status === 422) return "Confira os dados preenchidos, inclusive o CPF se informado.";
    if (failure.status === 429) return "Limite de convites atingido. Tente novamente mais tarde.";
    if (failure.status === 401 || failure.status === 403) return "Acesso ao cadastro de clientes indisponível.";
  }
  return "Não foi possível concluir a operação. Tente novamente.";
}

export function ClientDirectory({
  session,
  onAccessChange,
  attendanceBase,
  paymentsBase,
}: {
  session: Session;
  onAccessChange: () => Promise<void>;
  attendanceBase?: string;
  paymentsBase?: string;
}) {
  const [filter, setFilter] = useState({ term: "", page: 1 });
  const [directory, setDirectory] = useState<ClientPage | null>(null);
  const [listError, setListError] = useState("");
  const [form, setForm] = useState<ClientDetail | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const pending = useRef(false);
  const heading = useDirectoryFocus(form !== undefined);
  const birthDateRange = clientBirthDateRange();

  useEffect(() => {
    const controller = new AbortController();
    void listClients(filter.term, filter.page, controller.signal).then(
      data => { if (!controller.signal.aborted) setDirectory(data); },
      failure => { if (!controller.signal.aborted) setListError(message(failure)); },
    );
    return () => controller.abort();
  }, [filter]);

  function load(term: string, page: number) {
    setDirectory(null);
    setListError("");
    setFilter({ term, page });
  }

  async function run(operation: () => Promise<void>) {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (failure) {
      setError(message(failure));
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  function openForm(next: ClientDetail | null | undefined) {
    setError("");
    setNotice("");
    setForm(next);
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const data = {
      nome: String(fields.get("nome") ?? ""),
      data_nascimento: String(fields.get("data_nascimento") ?? ""),
      telefone: String(fields.get("telefone") ?? "").trim() || null,
      cpf: String(fields.get("cpf") ?? "").trim() || null,
    };
    const { min, max } = clientBirthDateRange();
    if (!data.data_nascimento || data.data_nascimento < min || data.data_nascimento > max) {
      setError("Informe uma data de nascimento válida.");
      return;
    }
    void run(async () => {
      const updated = form
        ? await changeClient("/" + encodeURIComponent(form.id), "PUT", {
            ...data, revisao: form.revisao, ativo: fields.has("ativo"),
          }, session.csrf_token)
        : await changeClient("", "POST", {
            ...data, email: String(fields.get("email") ?? ""), vincular_existente: fields.has("vincular"),
          }, session.csrf_token);
      setForm(updated);
      setNotice(form ? "Alterações salvas." : "Cliente cadastrado.");
      load(filter.term, filter.page);
      if (updated.id === session.user_id && updated.ativo !== form?.ativo) await onAccessChange();
    });
  }

  return (
    <section className="directory" aria-labelledby="clients-title">
      <h3 id="clients-title" ref={heading} tabIndex={-1}>
        {form === undefined ? "Clientes" : form ? "Editar cliente" : "Novo cliente"}
      </h3>
      {notice && <StatusMessage state="success" title={notice} />}
      {error && <StatusMessage state="error" title={error} />}
      {form === undefined ? (
        <>
          <div className="directory-actions">
            <Button disabled={busy} onClick={() => openForm(null)}>Cadastrar cliente</Button>
          </div>
          <form className="directory-actions directory-search" onSubmit={event => {
            event.preventDefault();
            load(String(new FormData(event.currentTarget).get("busca") ?? "").trim(), 1);
          }}>
            <label className="ac-field">Nome ou e-mail<input className="ac-field-control" name="busca" type="search"
              maxLength={254} defaultValue={filter.term} disabled={busy} /></label>
            <Button type="submit" variant="secondary" disabled={busy}>Pesquisar</Button>
          </form>
          {directory ? (
            <>
              {directory.itens.length === 0 && <StatusMessage state="empty" title="Nenhum cliente encontrado." />}
              <ul className="directory-cards" aria-label="Clientes encontrados">
                {directory.itens.map(item => (
                  <li className="directory-card" key={item.id}>
                    <h4>{item.nome}</h4>
                    <p className="directory-meta">{ageFormat.format(item.idade)} · {item.email}</p>
                    <DirectoryTag tone={item.ativo ? "positive" : "attention"}>{item.ativo ? "Perfil ativo" : "Perfil inativo"}</DirectoryTag>
                    <div className="directory-actions"><Button variant="secondary" disabled={busy}
                      onClick={() => void run(async () => setForm(await getClient(item.id)))}>
                      Consultar {item.nome}
                    </Button>
                      {attendanceBase && <Link to={attendanceBase + "/" + encodeURIComponent(item.id)}>Frequência de {item.nome}</Link>}
                      {paymentsBase && <Link to={paymentsBase + "/" + encodeURIComponent(item.id) + "/pagamentos"}>Pagamentos de {item.nome}</Link>}
                    </div>
                  </li>
                ))}
              </ul>
              <DirectoryPager page={directory} disabled={busy} label="Páginas de clientes"
                changePage={page => load(filter.term, page)} />
            </>
          ) : listError ? (
            <>
              <StatusMessage state="error" title={listError} />
              <Button variant="secondary" onClick={() => load(filter.term, filter.page)}>Recarregar lista</Button>
            </>
          ) : <StatusMessage state="loading" title="Carregando clientes…" />}
        </>
      ) : (
        <>
          {form && <div className="directory-card">
            <h4>{form.nome}</h4>
            <p>Idade atual · {ageFormat.format(form.idade)}</p>
            <p className="directory-meta">{form.email} · {accountLabels[form.estado_conta]}</p>
            {session.roles.includes("ADMINISTRADOR") && <Link to={"/area/administracao/designacoes?cliente=" + encodeURIComponent(form.id)}>
              Gerenciar instrutor responsável
            </Link>}
          </div>}
          <form key={form ? form.id + "/" + form.revisao : "new"} className="directory-form" onSubmit={save}>
            <fieldset className="directory-fieldset" disabled={busy}>
              <fieldset className="directory-group">
                <legend>Dados do cliente</legend>
                <label className="ac-field">Nome<input name="nome" maxLength={120} required defaultValue={form?.nome} /></label>
                <label className="ac-field">Data de nascimento<input name="data_nascimento" type="date" required
                  min={birthDateRange.min} max={birthDateRange.max} defaultValue={form?.data_nascimento} /></label>
                <label className="ac-field">CPF (opcional)<input name="cpf" type="text" inputMode="numeric"
                  autoComplete="off" maxLength={14} defaultValue={form?.cpf ?? ""} /></label>
                <label className="ac-field">Telefone<input name="telefone" type="tel" maxLength={25} defaultValue={form?.telefone ?? ""} /></label>
              </fieldset>
              <fieldset className="directory-group">
                <legend>{form ? "Situação do perfil" : "Conta de acesso"}</legend>
                {form ? (
                  <label className="directory-choice"><input name="ativo" type="checkbox" defaultChecked={form.ativo} /> Perfil de cliente ativo</label>
                ) : (
                  <>
                    <label className="ac-field">E-mail<input name="email" type="email" maxLength={254} required /></label>
                    <label className="directory-choice"><input name="vincular" type="checkbox" /> Vincular à conta de funcionário já existente com este e-mail</label>
                  </>
                )}
              </fieldset>
            </fieldset>
            <div className="directory-actions">
              <Button type="submit" pending={busy} pendingLabel="Salvando…">{form ? "Salvar alterações" : "Salvar cadastro"}</Button>
              <Button variant="secondary" disabled={busy} onClick={() => openForm(undefined)}>Voltar à lista</Button>
            </div>
          </form>
          {form && (form.convite || form.estado_conta === "CONVIDADO") &&
            <FirstAccessInvite invite={form.convite} busy={busy}
              onResend={form.ativo && form.estado_conta === "CONVIDADO" ? () => void run(async () => {
                setForm(await changeClient("/" + encodeURIComponent(form.id) + "/convite", "POST",
                  { revisao: form.revisao }, session.csrf_token));
              }) : undefined} />}
        </>
      )}
    </section>
  );
}
