import { useCallback, useRef, useState, type FormEvent } from "react";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager } from "../clients/directory-ui";
import { memberships, saveCharge, type Charge, type ChargeState, type Membership } from "./api";
import { civilDate } from "./format";
import { useBillingPage } from "./useBillingPage";

function membershipLabel(item: Membership) {
  return item.modalidade + " · " + civilDate(item.inicio) + " a " + civilDate(item.fim);
}

function MembershipInput({ clientId, initial }: { clientId: string; initial?: string | null }) {
  const load = useCallback((page: number, signal: AbortSignal) => memberships(clientId, page, signal), [clientId]);
  const { result, reload } = useBillingPage(load);
  const [choice, setChoice] = useState<{ id: string; label: string } | null>(
    initial ? { id: initial, label: "Matrícula atual" } : null,
  );

  return <div>
    <label className="ac-field">Matrícula vinculada (opcional)
      <select className="ac-field-control" name="matricula_id" value={choice?.id ?? ""} onChange={event => {
        const id = event.target.value;
        const item = result?.itens.find(option => option.id === id);
        setChoice(item ? { id, label: membershipLabel(item) } : null);
      }}>
        <option value="">Sem vínculo</option>
        {choice && !result?.itens.some(item => item.id === choice.id) &&
          <option value={choice.id}>{choice.label}</option>}
        {result?.itens.map(item => <option key={item.id} value={item.id}>{membershipLabel(item)}</option>)}
      </select>
    </label>
    {result === undefined && <p role="status">Carregando matrículas…</p>}
    {result === null && <Button variant="secondary" onClick={() => reload()}>Recarregar matrículas</Button>}
    {result && <DirectoryPager page={result} label="Páginas de matrículas" changePage={reload} />}
  </div>;
}

export function ChargeForm({ clientId, csrf, item, close, saved }: {
  clientId: string; csrf: string; item?: Charge; close: () => void; saved: () => void;
}) {
  const [requestId, setRequestId] = useState(() => crypto.randomUUID());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    pending.current = true;
    setBusy(true);
    setError("");
    const form = new FormData(event.currentTarget);
    const read = (name: string) => String(form.get(name) ?? "").trim();

    try {
      await saveCharge(clientId, {
        competencia: read("competencia") + "-01", vencimento: read("vencimento"),
        valor: read("valor").replace(",", "."), matricula_id: read("matricula_id") || null,
      }, csrf, item
        ? { id: item.id, revisao: item.revisao, estado: read("estado") as ChargeState }
        : { solicitacao_id: requestId });
      saved();
    } catch (reason) {
      const status = reason instanceof ApiError ? reason.status : 0;
      if (status === 409) setError("A cobrança mudou. Volte à lista e consulte a versão atual.");
      else if (status === 422) setError("Confira o valor, as datas e a matrícula selecionada.");
      else setError("Não foi possível confirmar a cobrança. Tente novamente.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return <form className="directory-form" onSubmit={event => void submit(event)}
    onChange={() => setRequestId(crypto.randomUUID())}>
    <fieldset className="directory-group" disabled={busy}>
      <legend>Dados da cobrança</legend>
      <label className="ac-field">Competência
        <input className="ac-field-control" type="month" name="competencia" max="9999-12" required
          defaultValue={item?.competencia.slice(0, 7)} />
      </label>
      <label className="ac-field">Vencimento
        <input className="ac-field-control" type="date" name="vencimento" max="9999-12-31" required
          defaultValue={item?.vencimento} />
      </label>
      <label className="ac-field">Valor em reais
        <input className="ac-field-control" inputMode="decimal" name="valor" required
          pattern="[0-9]{1,10}([.,][0-9]{1,2})?" defaultValue={item?.valor.replace(".", ",")} />
      </label>
      <MembershipInput clientId={clientId} initial={item?.matricula_id} />
      {item && <label className="ac-field">Estado do lançamento
        <select className="ac-field-control" name="estado" defaultValue={item.estado}>
          <option value="ABERTA">Disponível para pagamento</option>
          <option value="CANCELADA">Cancelada</option>
        </select>
      </label>}
    </fieldset>
    {error && <StatusMessage state="error" title={error} />}
    <div className="directory-actions">
      <Button type="submit" pending={busy}>Salvar cobrança</Button>
      <Button variant="secondary" onClick={close} disabled={busy}>Voltar à lista</Button>
    </div>
  </form>;
}
