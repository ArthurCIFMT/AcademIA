import { useEffect, useState, type FormEvent } from "react";

import { ApiError, type Session } from "../../lib/api/auth";
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
import "./staff.css";

const roleLabels = {
  ADMINISTRADOR: "Administrador",
  ATENDENTE: "Atendente",
  INSTRUTOR: "Instrutor",
};
const deliveryLabels = {
  ENVIANDO: "Envio em andamento",
  ENVIADO: "Enviado à caixa de e-mail",
  FALHOU: "Falha no envio",
  INCERTO: "Envio incerto",
  SEM_CONFIRMACAO: "Envio sem confirmação",
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
  const [notice, setNotice] = useState("");

  useEffect(() => {
    const controller = new AbortController();
    void listStaff(page, controller.signal).then(
      data => { if (!controller.signal.aborted) setDirectory(data); },
      failure => {
        if (!controller.signal.aborted) {
          setDirectory(null);
          setError(errorMessage(failure));
        }
      },
    );
    return () => controller.abort();
  }, [page, revision]);

  async function run(operation: () => Promise<void>) {
    setBusy(true);
    setError("");
    setNotice("");
    try {
      await operation();
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
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
      setError("Selecione pelo menos um papel.");
      return;
    }
    const data = {
      nome: String(fields.get("nome") ?? ""),
      cargo: String(fields.get("cargo") ?? ""),
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
      setNotice("Novo convite processado.");
    });
  }

  function changePage(nextPage: number) {
    setError("");
    setDirectory(null);
    setPage(nextPage);
  }

  return (
    <section className="staff-panel" aria-labelledby="staff-title">
      <h3 id="staff-title">Funcionários</h3>
      {notice && <p role="status">{notice}</p>}
      {error && <p role="alert">{error}</p>}

      {form === undefined ? (
        <>
          <button type="button" disabled={busy} onClick={() => {
            setError(""); setNotice(""); setForm(null);
          }}>Cadastrar funcionário</button>
          {directory ? (
            <>
              {directory.itens.length === 0 && <p>Nenhum funcionário nesta página.</p>}
              <ul className="staff-list">
                {directory.itens.map(item => (
                  <li key={item.id}>
                    <span>{item.nome} · {item.cargo} · {item.ativo ? "Perfil ativo" : "Perfil inativo"}</span>
                    <button type="button" disabled={busy} onClick={() => open(item.id)}>
                      Consultar {item.nome}
                    </button>
                  </li>
                ))}
              </ul>
              <div className="staff-pages">
                <button type="button" disabled={busy || page <= 1} onClick={() => changePage(page - 1)}>
                  Anterior
                </button>
                <span>Página {page}</span>
                <button type="button" disabled={busy || page * directory.limite >= directory.total}
                  onClick={() => changePage(page + 1)}>Próxima</button>
              </div>
            </>
          ) : error
            ? <button type="button" onClick={() => {
                setError(""); setRevision(value => value + 1);
              }}>Recarregar lista</button>
            : <p role="status">Carregando funcionários…</p>}
        </>
      ) : (
        <>
          <h4>{form ? "Editar funcionário" : "Novo funcionário"}</h4>
          {form && <p>{form.email} · {accountLabels[form.estado_conta]}</p>}
          <form key={form ? form.id + "/" + form.revisao : "new"} className="staff-form" onSubmit={save}>
            <fieldset disabled={busy}>
              <label>Nome<input name="nome" defaultValue={form?.nome} maxLength={120} required /></label>
              <label>Cargo<input name="cargo" defaultValue={form?.cargo} maxLength={80} required /></label>
              <label>Data de admissão<input name="data_admissao" type="date" defaultValue={form?.data_admissao} required /></label>
              {form ? (
                <label><input name="ativo" type="checkbox" defaultChecked={form.ativo} /> Perfil de funcionário ativo</label>
              ) : (
                <>
                  <label>E-mail<input name="email" type="email" maxLength={254} required /></label>
                  <label><input name="vincular" type="checkbox" /> Vincular a conta de cliente já existente com este e-mail</label>
                </>
              )}
              <fieldset>
                <legend>Papéis de funcionário</legend>
                {staffRoles.map(role => (
                  <label key={role}>
                    <input name="papel" type="checkbox" value={role} defaultChecked={form?.papeis.includes(role)} />
                    {roleLabels[role]}
                  </label>
                ))}
              </fieldset>
              <button type="submit">{form ? "Salvar alterações" : "Salvar cadastro"}</button>
            </fieldset>
          </form>
          {form?.convite && <p>
            {deliveryLabels[form.convite.estado]} · Validade até{" "}
            <time dateTime={form.convite.expira_em}>
              {new Date(form.convite.expira_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}
            </time>
          </p>}
          {form?.ativo && form.estado_conta === "CONVIDADO" && (
            <button type="button" disabled={busy} onClick={() => resend(form)}>Reenviar convite</button>
          )}
          {" "}
          <button type="button" disabled={busy} onClick={() => {
            setError(""); setNotice(""); setForm(undefined);
          }}>Voltar à lista</button>
        </>
      )}
    </section>
  );
}
