import { useEffect, useState } from "react";

import { Button, StatusMessage } from "../../ui/primitives";
import { loadDashboard, type DashboardOverview, type Frequency, type Indicator } from "./api";
import { FinancialPanel } from "./FinancialPanel";
import "./dashboard.css";

const number = new Intl.NumberFormat("pt-BR");
const shortDate = new Intl.DateTimeFormat("pt-BR", { day: "2-digit", month: "2-digit", timeZone: "UTC" });
const refreshTime = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo",
});

function dateLabel(iso: string) {
  return shortDate.format(new Date(iso + "T00:00:00Z"));
}

function Metric({ label, result }: { label: string; result: Indicator<number> }) {
  return <div className="ac-card dashboard-metric">
    <dt>{label}</dt>
    <dd>{result.estado === "DISPONIVEL" ? number.format(result.valor)
      : <span className="dashboard-unavailable">Indisponível</span>}</dd>
  </div>;
}

function BarList({ rows, label }: { rows: { name: string; visits: number }[]; label: string }) {
  const max = Math.max(1, ...rows.map(row => row.visits));
  return <ul className="dashboard-bars" aria-label={label}>
    {rows.map(row => <li key={row.name}>
      <span>{row.name}</span>
      <div className="dashboard-bar" aria-hidden="true">
        <div style={{ inlineSize: 100 * row.visits / max + "%" }} />
      </div>
      <strong>{number.format(row.visits)}</strong>
    </li>)}
  </ul>;
}

function Activity({ data }: { data: Frequency }) {
  const [selectedDay, setSelectedDay] = useState("");
  const day = data.dias.find(row => row.data === selectedDay) ?? data.dias.at(-1);
  return <>
    <section className="ac-card" aria-labelledby="dashboard-week">
      <h3 id="dashboard-week">Frequência semanal</h3>
      <p className="dashboard-hint">Visitas confirmadas nas últimas quatro semanas, incluindo a atual.</p>
      <BarList label="Visitas por semana" rows={data.semanas.map(week => ({
        name: "Semana de " + dateLabel(week.inicio), visits: week.visitas,
      }))} />
    </section>
    <section className="ac-card" aria-labelledby="dashboard-days">
      <h3 id="dashboard-days">Frequência por dia e hora</h3>
      <p className="dashboard-hint">Últimos sete dias, no horário de São Paulo.</p>
      <BarList label="Visitas por dia" rows={data.dias.map(row => ({
        name: dateLabel(row.data), visits: row.visitas,
      }))} />
      {day && <div className="dashboard-hours">
        <label className="ac-field">Dia para detalhar
          <select className="ac-field-control" value={day.data} onChange={event => setSelectedDay(event.target.value)}>
            {data.dias.map(row => <option key={row.data} value={row.data}>{dateLabel(row.data)}</option>)}
          </select>
        </label>
        {day.por_hora.length > 0
          ? <BarList label="Visitas por faixa de uma hora" rows={day.por_hora.map(row => ({
            name: row.hora.toString().padStart(2, "0") + "h", visits: row.visitas,
          }))} />
          : <StatusMessage state="empty" title="Nenhuma visita registrada neste dia." />}
      </div>}
    </section>
  </>;
}

export function Dashboard() {
  const [attempt, setAttempt] = useState(0);
  const [result, setResult] = useState<DashboardOverview | null>();
  useEffect(() => {
    const controller = new AbortController();
    void loadDashboard(controller.signal).then(
      data => { if (!controller.signal.aborted) setResult(data); },
      () => { if (!controller.signal.aborted) setResult(null); },
    );
    return () => controller.abort();
  }, [attempt]);

  function refresh() {
    setResult(undefined);
    setAttempt(value => value + 1);
  }

  return <section className="dashboard" aria-labelledby="dashboard-title">
    <header className="dashboard-header">
      <div>
        <h2 id="dashboard-title">Indicadores da academia</h2>
        {result && <p className="dashboard-hint">Consulta em{" "}
          <time dateTime={result.consultado_em}>{refreshTime.format(new Date(result.consultado_em))}</time>
        </p>}
      </div>
      <Button variant="secondary" onClick={refresh} disabled={result === undefined}>Atualizar indicadores</Button>
    </header>
    {result === undefined ? <StatusMessage state="loading" title="Carregando indicadores…" />
      : result === null ? <StatusMessage state="error" title="Não foi possível consultar os indicadores." />
      : <>
        <dl className="dashboard-metrics">
          <Metric label="Clientes ativos" result={result.clientes_ativos} />
          <Metric label="Clientes com matrícula vigente" result={result.clientes_matriculados} />
          <Metric label="Funcionários cadastrados" result={result.funcionarios} />
          <Metric label="Pessoas presentes agora" result={result.lotacao} />
        </dl>
        {result.financeiro && <FinancialPanel result={result.financeiro} />}
        <div className="dashboard-activity">
          {result.frequencia.estado === "DISPONIVEL" ? <Activity data={result.frequencia.valor} />
            : <StatusMessage state="error" title="Frequência temporariamente indisponível." />}
        </div>
      </>}
  </section>;
}
