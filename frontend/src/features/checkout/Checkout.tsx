import { useRef, useState, type FormEvent } from "react";
import { Link } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { money } from "../billing/format";
import { useBillingPage } from "../billing/useBillingPage";
import { DirectoryPager, DirectoryTag } from "../clients/directory-ui";
import { offers, receipts, simulate, type Outcome, type Receipt } from "./api";

const labels: Record<Outcome, string> = {
  CONFIRMADO: "Confirmado", PENDENTE: "Pendente", RECUSADO: "Recusado",
};
const timestamp = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo",
});

export function Checkout({ csrf, billingPath }: { csrf: string; billingPath: string }) {
  const plans = useBillingPage(offers);
  const history = useBillingPage(receipts);
  const [planId, setPlanId] = useState("");
  const [outcome, setOutcome] = useState<Outcome | "">("");
  const [id, setId] = useState(() => crypto.randomUUID());
  const [saved, setSaved] = useState<Receipt>();
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const submitting = useRef(false);
  const plan = plans.result?.itens.find(item => item.id === planId);

  function changeSelection() {
    setId(crypto.randomUUID());
    setError("");
    setSaved(undefined);
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!plan || !outcome || submitting.current) return;
    submitting.current = true;
    setBusy(true);
    setError("");
    setSaved(undefined);
    try {
      const receipt = await simulate({ solicitacao_id: id, plano_id: plan.id, resultado: outcome }, csrf);
      setPlanId("");
      setOutcome("");
      setId(crypto.randomUUID());
      setSaved(receipt);
      history.reload(1);
    } catch (reason) {
      if (reason instanceof ApiError && reason.status === 409) {
        setError("O plano ou a solicitação mudou. Selecione o plano atualizado.");
        setPlanId("");
        setId(crypto.randomUUID());
        plans.reload(1);
      } else {
        setError("Não foi possível confirmar o registro da simulação. Tente novamente.");
      }
    } finally {
      submitting.current = false;
      setBusy(false);
    }
  }

  return <section className="directory" aria-labelledby="checkout-title">
    <h2 id="checkout-title">Compra simulada de plano</h2>
    <p className="directory-meta">Escolha um plano e um cenário. Os valores são fictícios e a matrícula é feita pelo atendente.</p>
    <Link to={billingPath}>Minhas cobranças</Link>
    {plans.result === undefined ? <StatusMessage state="loading" title="Carregando planos…" />
      : plans.result === null ? <>
        <StatusMessage state="error" title="Não foi possível consultar os planos." />
        <Button variant="secondary" onClick={() => plans.reload()}>Tentar carregar planos</Button>
      </> : plans.result.itens.length === 0
        ? <StatusMessage state="empty" title="Nenhum plano disponível para simulação." />
        : <>
          <form className="directory-form" onSubmit={event => void submit(event)}>
            <fieldset className="directory-group" disabled={busy}>
              <legend>Nova simulação</legend>
              <label className="ac-field">Plano
                <select className="ac-field-control" value={planId}
                  onChange={event => { setPlanId(event.target.value); changeSelection(); }} required>
                  <option value="">Selecione um plano</option>
                  {plans.result.itens.map(item => <option key={item.id} value={item.id}>
                    {item.nome} · {item.modalidade} · {money(item.preco_base)}
                  </option>)}
                </select>
              </label>
              {plan && <p>{plan.duracao_dias} dias · Valor simulado {money(plan.preco_base)}</p>}
              <label className="ac-field">Resultado da simulação
                <select className="ac-field-control" value={outcome}
                  onChange={event => { setOutcome(event.target.value as Outcome | ""); changeSelection(); }} required>
                  <option value="">Selecione um resultado</option>
                  <option value="CONFIRMADO">Confirmado</option>
                  <option value="PENDENTE">Pendente</option>
                  <option value="RECUSADO">Recusado</option>
                </select>
              </label>
              <Button type="submit" pending={busy} disabled={!plan || !outcome}>Registrar simulação</Button>
            </fieldset>
          </form>
          <DirectoryPager page={plans.result} label="Páginas de planos" disabled={busy}
            changePage={page => { setPlanId(""); changeSelection(); plans.reload(page); }} />
        </>}
    {saved && <p role="status">Simulação registrada · {labels[saved.estado]} · {money(saved.valor)}</p>}
    {error && <StatusMessage state="error" title={error} />}
    <h3>Histórico de compras simuladas</h3>
    {history.result === undefined ? <StatusMessage state="loading" title="Carregando histórico…" />
      : history.result === null ? <>
        <StatusMessage state="error" title="Não foi possível consultar o histórico." />
        <Button variant="secondary" onClick={() => history.reload()}>Tentar carregar histórico</Button>
      </> : <>
        {history.result.itens.length === 0 ? <StatusMessage state="empty" title="Nenhuma compra simulada neste histórico." />
          : <ul className="directory-cards" aria-label="Compras simuladas">{history.result.itens.map(receipt =>
            <li className="directory-card" key={receipt.id}>
              <h4>{receipt.plano_nome_snapshot}</h4>
              <DirectoryTag tone={receipt.estado === "CONFIRMADO" ? "positive" : "neutral"}>{labels[receipt.estado]}</DirectoryTag>
              <p>Valor simulado {money(receipt.valor)} · <time dateTime={receipt.simulado_em}>
                {timestamp.format(new Date(receipt.simulado_em))}
              </time></p>
              <p className="directory-meta">Referência <code>{receipt.id}</code></p>
            </li>)}</ul>}
        <DirectoryPager page={history.result} label="Páginas de compras simuladas" changePage={history.reload} />
      </>}
  </section>;
}
