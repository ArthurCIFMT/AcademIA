import { StatusMessage } from "../../ui/primitives";
import { money } from "../billing/format";
import type { FinancialOverview, FinancialTotals, Indicator } from "./api";

const monthName = new Intl.DateTimeFormat("pt-BR", { month: "long", year: "numeric", timeZone: "UTC" });
const metrics = [
  ["cobrado", "Cobrado"],
  ["recebido", "Recebido"],
  ["pendente", "Saldo a vencer"],
  ["vencido", "Saldo vencido"],
] as const;

function Period({ title, totals }: { title: string; totals: FinancialTotals }) {
  return <section className="dashboard-finance-period" aria-label={title}>
    <h4>{title}</h4>
    <dl>
      {metrics.map(([field, label]) => <div key={field}>
        <dt>{label}</dt>
        <dd>{money(totals[field])}</dd>
      </div>)}
    </dl>
  </section>;
}

export function FinancialPanel({ result }: { result: Indicator<FinancialOverview> }) {
  return <section className="ac-card" aria-labelledby="dashboard-finance-title">
    <h3 id="dashboard-finance-title">Financeiro simulado</h3>
    <p className="dashboard-hint">
      Cobranças por competência e recebimentos pela data do pagamento. Os valores são didáticos.
    </p>
    {result.estado === "DISPONIVEL" ? <div className="dashboard-finance-periods">
      <Period title={"Mês atual · " + monthName.format(new Date(result.valor.competencia_atual + "T00:00:00Z"))}
        totals={result.valor.mes} />
      <Period title={"Ano atual · " + result.valor.competencia_atual.slice(0, 4)}
        totals={result.valor.ano} />
      <Period title="Total registrado" totals={result.valor.total} />
    </div> : <StatusMessage state="error" title="Financeiro temporariamente indisponível." />}
  </section>;
}
