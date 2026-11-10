import { useEffect, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError, type Session } from "../../lib/api/auth";
import { changeClient, getClient, listClients, type ClientDetail, type ClientPage } from "./api";
import "./clients.css";

const accountLabels = {
  CONVIDADO: "Aguardando primeiro acesso",
  ATIVO: "Conta ativa",
  INATIVO: "Conta inativa",
  BLOQUEADO: "Conta bloqueada",
};
const inviteLabels = {
  ENVIANDO: "Envio em andamento",
  ENVIADO: "Convite enviado",
  FALHOU: "Falha no envio do convite",
  INCERTO: "Envio incerto",
  SEM_CONFIRMACAO: "Envio sem confirmação",
};

function message(failure: unknown) {
  if (failure instanceof ApiError) {
    if (failure.status === 409) return "Operação em conflito. Confira o e-mail e o vínculo ou recarregue o cadastro.";
    if (failure.status === 422) return "Confira os dados preenchidos.";
    if (failure.status === 429) return "Limite de convites atingido. Tente novamente mais tarde.";
    if (failure.status === 401 || failure.status === 403) return "Acesso ao cadastro de clientes indisponível.";
  }
  return "Não foi possível concluir a operação. Tente novamente.";
}

export function ClientDirectory({
  session,
  onAccessChange,
}: {
  session: Session;
  onAccessChange: () => Promise<void>;
}) {
  const [filter, setFilter] = useState({ term: "", page: 1 });
  const [directory, setDirectory] = useState<ClientPage | null>(null);
  const [listError, setListError] = useState("");
  const [form, setForm] = useState<ClientDetail | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

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
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (failure) {
      setError(message(failure));
    } finally {
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
    };
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
    <section className="clients-panel" aria-labelledby="clients-title">
      <h3 id="clients-title">Clientes</h3>
      {notice && <p role="status">{notice}</p>}
      {error && <p role="alert">{error}</p>}
      {form === undefined ? (
        <>
          <button type="button" disabled={busy} onClick={() => openForm(null)}>Cadastrar cliente</button>
          <form className="clients-search" onSubmit={event => {
            event.preventDefault();
            load(String(new FormData(event.currentTarget).get("busca") ?? "").trim(), 1);
          }}>
            <label>Nome ou e-mail<input name="busca" type="search" maxLength={254} defaultValue={filter.term} /></label>
            <button type="submit">Pesquisar</button>
          </form>
          {directory ? (
            <>
              {directory.itens.length === 0 && <p>Nenhum cliente encontrado.</p>}
              <ul className="clients-list">
                {directory.itens.map(item => (
                  <li key={item.id}>
                    <span>{item.nome} · {item.email} · {item.ativo ? "Perfil ativo" : "Perfil inativo"}</span>
                    <button type="button" disabled={busy}
                      onClick={() => void run(async () => setForm(await getClient(item.id)))}>
                      Consultar {item.nome}
                    </button>
                  </li>
                ))}
              </ul>
              <div className="clients-pages">
                <button type="button" disabled={filter.page <= 1} onClick={() => load(filter.term, filter.page - 1)}>Anterior</button>
                <span>Página {filter.page}</span>
                <button type="button" disabled={filter.page * directory.limite >= directory.total}
                  onClick={() => load(filter.term, filter.page + 1)}>Próxima</button>
              </div>
            </>
          ) : listError ? (
            <>
              <p role="alert">{listError}</p>
              <button type="button" onClick={() => load(filter.term, filter.page)}>Recarregar lista</button>
            </>
          ) : <p role="status">Carregando clientes…</p>}
        </>
      ) : (
        <>
          <h4>{form ? "Editar cliente" : "Novo cliente"}</h4>
          {form && <p>{form.email} · {accountLabels[form.estado_conta]}</p>}
          {form && session.roles.includes("ADMINISTRADOR") && (
            <p><Link to={"/area/administracao/designacoes?cliente=" + encodeURIComponent(form.id)}>
              Gerenciar instrutor responsável
            </Link></p>
          )}
          <form key={form ? form.id + "/" + form.revisao : "new"} className="clients-form" onSubmit={save}>
            <fieldset disabled={busy}>
              <label>Nome<input name="nome" maxLength={120} required defaultValue={form?.nome} /></label>
              <label>Data de nascimento<input name="data_nascimento" type="date" required defaultValue={form?.data_nascimento} /></label>
              <label>Telefone<input name="telefone" type="tel" maxLength={25} defaultValue={form?.telefone ?? ""} /></label>
              {form ? (
                <label><input name="ativo" type="checkbox" defaultChecked={form.ativo} /> Perfil de cliente ativo</label>
              ) : (
                <>
                  <label>E-mail<input name="email" type="email" maxLength={254} required /></label>
                  <label><input name="vincular" type="checkbox" /> Vincular à conta de funcionário já existente com este e-mail</label>
                </>
              )}
              <button type="submit">{form ? "Salvar alterações" : "Salvar cadastro"}</button>
            </fieldset>
          </form>
          {form?.convite && <p>
            {inviteLabels[form.convite.estado]} · Validade até{" "}
            <time dateTime={form.convite.expira_em}>
              {new Date(form.convite.expira_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}
            </time>
          </p>}
          {form?.ativo && form.estado_conta === "CONVIDADO" && (
            <button type="button" disabled={busy} onClick={() => void run(async () => {
              setForm(await changeClient("/" + encodeURIComponent(form.id) + "/convite", "POST",
                { revisao: form.revisao }, session.csrf_token));
              setNotice("Novo convite processado.");
            })}>Reenviar convite</button>
          )}
          {" "}
          <button type="button" disabled={busy} onClick={() => openForm(undefined)}>Voltar à lista</button>
        </>
      )}
    </section>
  );
}
