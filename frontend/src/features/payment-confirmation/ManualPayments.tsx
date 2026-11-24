import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager, DirectoryTag, useDirectoryFocus } from "../clients/directory-ui";
import { listPayments, methods, postPayment, type ManualPayment, type PaymentPage } from "./api";

type Draft = { kind: "register" } | { kind: "correct" | "void"; row: ManualPayment };

const currency = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const time = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo",
});
const dates = new Intl.DateTimeFormat("sv-SE", { timeZone: "America/Sao_Paulo" });
const civil = (iso: string) => iso.split("-").reverse().join("/");
const titles = { register: "Novo registro", correct: "Corrigir pagamento", void: "Anular registro" } as const;

function PaymentForm({ draft, clientId, csrf, close, saved }: {
  draft: Draft; clientId: string; csrf: string; close: () => void; saved: (message: string) => void;
}) {
  const [requestId, setRequestId] = useState(() => crypto.randomUUID());
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const pending = useRef(false);
  const previous = draft.kind === "register" ? undefined : draft.row;

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (pending.current) return;
    const form = new FormData(event.currentTarget);
    const read = (name: string) => String(form.get(name) ?? "").trim();
    const motivo = read("motivo");
    pending.current = true;
    setBusy(true);
    setError("");
    try {
      if (draft.kind === "void") {
        await postPayment(clientId, "/" + draft.row.id + "/anulacao", { motivo }, csrf);
        saved("Registro anulado.");
      } else {
        const payment = {
          solicitacao_id: requestId, valor: read("valor").replace(",", "."),
          metodo: read("metodo"), referencia_externa: read("referencia_externa"),
          pago_em: read("pago_em"),
        };
        if (draft.kind === "correct") {
          await postPayment(clientId, "/" + draft.row.id + "/correcao", { ...payment, motivo }, csrf);
          saved("Correção registrada. O pagamento anterior permanece no histórico.");
        } else {
          await postPayment(clientId, "", payment, csrf);
          saved("Pagamento registrado.");
        }
      }
    } catch (failure) {
      const status = failure instanceof ApiError ? failure.status : 0;
      if (status === 409) setError("A referência já está em uso ou o registro mudou. Confira o histórico.");
      else if (status === 422) setError("Confira o valor, a data e os campos obrigatórios.");
      else setError("Não foi possível confirmar a operação. Tente novamente.");
    } finally {
      pending.current = false;
      setBusy(false);
    }
  }

  return <form className="directory-form" onSubmit={event => void submit(event)}
    onChange={() => setRequestId(crypto.randomUUID())}>
    <fieldset className="directory-group" disabled={busy}>
      <legend>{titles[draft.kind]}</legend>
      {draft.kind === "void" ? <p>Anular este registro de {currency.format(Number(draft.row.valor))}?
        O histórico continuará disponível.</p> : <>
        <label className="ac-field">Valor em reais
          <input className="ac-field-control" name="valor" type="text" inputMode="decimal"
            required pattern="[0-9]{1,10}([.,][0-9]{1,2})?" defaultValue={previous?.valor.replace(".", ",")} />
        </label>
        <label className="ac-field">Data do pagamento
          <input className="ac-field-control" name="pago_em" type="date" required
            defaultValue={previous?.pago_em ?? dates.format(new Date())} max={dates.format(new Date())} />
        </label>
        <label className="ac-field">Forma de pagamento
          <select className="ac-field-control" name="metodo" defaultValue={previous?.metodo ?? ""} required>
            <option value="">Selecione</option>
            {Object.entries(methods).map(([key, value]) => <option key={key} value={key}>{value}</option>)}
          </select>
        </label>
        <label className="ac-field">Referência do comprovante
          <input className="ac-field-control" name="referencia_externa" required maxLength={150}
            defaultValue={previous?.referencia_externa} />
        </label>
      </>}
      {draft.kind !== "register" && <label className="ac-field">Motivo
        <textarea className="ac-field-control" name="motivo" required maxLength={240} />
      </label>}
    </fieldset>
    {error && <StatusMessage state="error" title={error} />}
    <div className="directory-actions">
      <Button type="submit" pending={busy} variant={draft.kind === "void" ? "danger" : "primary"}>
        {draft.kind === "void" ? "Confirmar anulação" : "Salvar registro"}
      </Button>
      <Button variant="secondary" onClick={close} disabled={busy}>Cancelar</Button>
    </div>
  </form>;
}

function PaymentCard({ row, edit }: { row: ManualPayment; edit: (draft: Draft) => void }) {
  return <li className="directory-card">
    <h3>{currency.format(Number(row.valor))} · {methods[row.metodo]}</h3>
    <DirectoryTag tone={row.estado === "CONFIRMADO" ? "positive" : "attention"}>
      {row.estado === "CONFIRMADO" ? "Confirmado" : "Anulado"}
    </DirectoryTag>
    <p>Pago em <time dateTime={row.pago_em}>{civil(row.pago_em)}</time> · Referência {row.referencia_externa}</p>
    <p className="directory-meta">Registro de {row.registrado_por_nome ?? "funcionário"} em{" "}
      <time dateTime={row.confirmado_em}>{time.format(new Date(row.confirmado_em))}</time>.</p>
    {row.substitui_id && <p>Correção de um registro anterior.</p>}
    {row.anulado_em && <p>Anulação por {row.anulado_por_nome ?? "funcionário"} em{" "}
      <time dateTime={row.anulado_em}>{time.format(new Date(row.anulado_em))}</time>. {row.motivo_anulacao}</p>}
    {row.estado === "CONFIRMADO" && <div className="directory-actions">
      <Button variant="secondary" onClick={() => edit({ kind: "correct", row })}>Corrigir</Button>
      <Button variant="secondary" onClick={() => edit({ kind: "void", row })}>Anular</Button>
    </div>}
  </li>;
}

function PaymentHistory({ clientId, back, csrf }: { clientId: string; back: string; csrf: string }) {
  const [draft, setDraft] = useState<Draft>();
  const [notice, setNotice] = useState("");
  const [query, setQuery] = useState({ page: 1 });
  const [data, setData] = useState<PaymentPage | null>();
  const heading = useDirectoryFocus(draft !== undefined);

  useEffect(() => {
    const controller = new AbortController();
    void listPayments(clientId, query.page, controller.signal).then(
      value => { if (!controller.signal.aborted) setData(value); },
      () => { if (!controller.signal.aborted) setData(null); },
    );
    return () => controller.abort();
  }, [clientId, query]);

  function reload(page = query.page) {
    setData(undefined);
    setQuery({ page });
  }

  function edit(next: Draft) {
    setNotice("");
    setDraft(next);
  }

  return <section className="directory" aria-labelledby="payments-title">
    <h2 id="payments-title" ref={heading} tabIndex={-1}>{draft ? titles[draft.kind] : "Pagamentos manuais"}</h2>
    <Link to={back}>Voltar à lista de clientes</Link>
    {data && <p>{data.cliente_nome}</p>}
    {notice && <StatusMessage state="success" title={notice} />}
    {draft ? <PaymentForm draft={draft} clientId={clientId} csrf={csrf}
      close={() => setDraft(undefined)}
      saved={message => { setDraft(undefined); setNotice(message); reload(1); }} />
      : data === undefined ? <StatusMessage state="loading" title="Carregando histórico…" />
      : data === null ? <>
        <StatusMessage state="error" title="Não foi possível consultar os pagamentos." />
        <Button variant="secondary" onClick={() => reload()}>Tentar novamente</Button>
      </> : <>
        <Button onClick={() => edit({ kind: "register" })}>Registrar pagamento</Button>
        {data.itens.length ? <ul className="directory-cards" aria-label="Histórico de pagamentos">
          {data.itens.map(row => <PaymentCard key={row.id} row={row} edit={edit} />)}
        </ul> : <StatusMessage state="empty" title="Nenhum pagamento manual neste histórico." />}
        <DirectoryPager page={data} label="Páginas de pagamentos" changePage={reload} />
      </>}
  </section>;
}

export function ManualPayments({ back, csrf }: { back: string; csrf: string }) {
  const { clientId } = useParams();
  if (!clientId) return <StatusMessage state="error" title="Cliente indisponível." />;
  return <PaymentHistory key={clientId} clientId={clientId} back={back} csrf={csrf} />;
}
