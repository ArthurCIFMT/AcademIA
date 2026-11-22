import { useEffect, useRef, useState, type FormEvent } from "react";

import { ApiError, type Session } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager, DirectoryTag, FirstAccessInvite, useDirectoryFocus } from "../clients/directory-ui";
import {
  createStaff,
  getStaff,
  listStaff,
  resendStaffInvite,
  staffRoles,
  updateStaff,
  type StaffDetail,
  type StaffPage,
  type StaffRole,
} from "./api";

const roleLabels = {
  ADMINISTRADOR: "Administrador",
  ATENDENTE: "Atendente",
  INSTRUTOR: "Instrutor",
};
const accountLabels = {
  CONVIDADO: "Aguardando primeiro acesso",
  ATIVO: "Conta ativa",
  INATIVO: "Conta inativa",
  BLOQUEADO: "Conta bloqueada",
};

function errorMessage(failure: unknown) {
  if (failure instanceof ApiError) {
    if (failure.status === 409) {
      return "Operação em conflito. Verifique o vínculo, recarregue os dados e preserve um administrador ativo.";
    }
    if (failure.status === 422) return "Confira os dados preenchidos.";
    if (failure.status === 429) return "Limite de convites atingido. Tente novamente mais tarde.";
    if (failure.status === 401 || failure.status === 403) return "Acesso à administração de funcionários indisponível.";
  }
  return "Não foi possível concluir a operação. Tente novamente.";
}

export function StaffDirectory({
  session,
  onAccessChange,
}: {
  session: Session;
  onAccessChange: () => Promise<void>;
}) {
  const [page, setPage] = useState(1);
  const [revision, setRevision] = useState(0);
  const [directory, setDirectory] = useState<StaffPage | null>(null);
  const [form, setForm] = useState<StaffDetail | null | undefined>(undefined);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [listError, setListError] = useState("");
  const [notice, setNotice] = useState("");
  const pending = useRef(false);
  const heading = useDirectoryFocus(form !== undefined);

  useEffect(() => {
    const controller = new AbortController();
    void listStaff(page, controller.signal).then(
      data => { if (!controller.signal.aborted) setDirectory(data); },
      failure => {
        if (!controller.signal.aborted) {
          setDirectory(null);
          setListError(errorMessage(failure));
        }
      },
    );
    return () => controller.abort();
  }, [page, revision]);

  async function run(operation: () => Promise<void>) {
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  function open(id: string) {
    void run(async () => setForm(await getStaff(id)));
  }

  function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const fields = new FormData(event.currentTarget);
    const papeis = fields.getAll("papel").filter((role): role is StaffRole =>
      staffRoles.some(allowed => allowed === role));
    if (papeis.length === 0) {
      setError("Selecione pelo menos um cargo.");
      return;
    }
    const data = {
      nome: String(fields.get("nome") ?? ""),
      data_admissao: String(fields.get("data_admissao") ?? ""),
      papeis,
    };
    void run(async () => {
      const result = form
        ? await updateStaff(form.id, {
            ...data, ativo: fields.has("ativo"), revisao: form.revisao,
          }, session.csrf_token)
        : await createStaff({
            ...data, email: String(fields.get("email") ?? ""),
            vincular_existente: fields.has("vincular"),
          }, session.csrf_token);
      setForm(result);
      setListError("");
      setRevision(value => value + 1);
      setNotice(form ? "Alterações salvas." : "Funcionário cadastrado.");
      if (result.id === session.user_id && (!result.ativo || !result.papeis.includes("ADMINISTRADOR"))) {
        await onAccessChange();
      }
    });
  }

  function resend(staff: StaffDetail) {
    void run(async () => {
      setForm(await resendStaffInvite(staff.id, staff.revisao, session.csrf_token));
    });
  }

  function changePage(nextPage: number) {
    setError("");
    setListError("");
    setDirectory(null);
    setPage(nextPage);
  }

  return (
    <section className="directory" aria-labelledby="staff-title">
      <h3 id="staff-title" ref={heading} tabIndex={-1}>
        {form === undefined ? "Funcionários" : form ? "Editar funcionário" : "Novo funcionário"}
      </h3>
      {notice && <StatusMessage state="success" title={notice} />}
      {error && <StatusMessage state="error" title={error} />}

      {form === undefined ? (
        <>
          <div className="directory-actions"><Button disabled={busy} onClick={() => {
            setError(""); setNotice(""); setForm(null);
          }}>Cadastrar funcionário</Button></div>
          {directory ? (
            <>
              {directory.itens.length === 0 && <StatusMessage state="empty" title="Nenhum funcionário nesta página." />}
              <ul className="directory-cards" aria-label="Funcionários cadastrados">
                {directory.itens.map(item => (
                  <li className="directory-card" key={item.id}>
                    <h4>{item.nome}</h4>
                    <p className="directory-meta">{item.papeis.map(role => roleLabels[role]).join(" / ")}</p>
                    <DirectoryTag tone={item.ativo ? "positive" : "attention"}>{item.ativo ? "Perfil ativo" : "Perfil inativo"}</DirectoryTag>
                    <div className="directory-actions"><Button variant="secondary" disabled={busy} onClick={() => open(item.id)}>
                      Consultar {item.nome}
                    </Button></div>
                  </li>
                ))}
              </ul>
              <DirectoryPager page={directory} disabled={busy} label="Páginas de funcionários" changePage={changePage} />
            </>
          ) : listError ? <>
              <StatusMessage state="error" title={listError} />
              <Button variant="secondary" onClick={() => {
                setListError(""); setRevision(value => value + 1);
              }}>Recarregar lista</Button>
            </> : <StatusMessage state="loading" title="Carregando funcionários…" />}
        </>
      ) : (
        <>
          {form && <div className="directory-card"><h4>{form.nome}</h4>
            <p className="directory-meta">{form.email} · {accountLabels[form.estado_conta]}</p>
          </div>}
          <form key={form ? form.id + "/" + form.revisao : "new"} className="directory-form" onSubmit={save}>
            <fieldset className="directory-fieldset" disabled={busy}>
              <fieldset className="directory-group">
                <legend>Dados do funcionário</legend>
                <label className="ac-field">Nome<input name="nome" defaultValue={form?.nome} maxLength={120} required /></label>
                <label className="ac-field">Data de admissão<input name="data_admissao" type="date" defaultValue={form?.data_admissao} required /></label>
                {form ? (
                  <label className="directory-choice"><input name="ativo" type="checkbox" defaultChecked={form.ativo} /> Perfil de funcionário ativo</label>
                ) : (
                  <>
                    <label className="ac-field">E-mail<input name="email" type="email" maxLength={254} required /></label>
                    <label className="directory-choice"><input name="vincular" type="checkbox" /> Vincular a conta de cliente já existente com este e-mail</label>
                  </>
                )}
              </fieldset>
              <fieldset className="directory-group" aria-describedby="staff-roles-help">
                <legend>Cargos do funcionário</legend>
                <p id="staff-roles-help">Selecione pelo menos um cargo. Os cargos selecionados definem o que o funcionário pode acessar.</p>
                {staffRoles.map(role => (
                  <label className="directory-choice" key={role}>
                    <input name="papel" type="checkbox" value={role} defaultChecked={form?.papeis.includes(role)} />
                    {roleLabels[role]}
                  </label>
                ))}
              </fieldset>
            </fieldset>
            <div className="directory-actions">
              <Button type="submit" pending={busy} pendingLabel="Salvando…">{form ? "Salvar alterações" : "Salvar cadastro"}</Button>
              <Button variant="secondary" disabled={busy} onClick={() => {
                setError(""); setNotice(""); setForm(undefined);
              }}>Voltar à lista</Button>
            </div>
          </form>
          {form && (form.convite || form.estado_conta === "CONVIDADO") &&
            <FirstAccessInvite invite={form.convite} busy={busy}
              onResend={form.ativo && form.estado_conta === "CONVIDADO" ? () => resend(form) : undefined} />}
        </>
      )}
    </section>
  );
}
