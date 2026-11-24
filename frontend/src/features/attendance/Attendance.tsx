import { useCallback, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager } from "../clients/directory-ui";
import { loadAttendance } from "./api";
import { useAccessQuery } from "./useAccessQuery";
import "./attendance.css";

const academyZone = "America/Sao_Paulo";
const civilDate = new Intl.DateTimeFormat("sv-SE", { timeZone: academyZone });
const visitTime = new Intl.DateTimeFormat("pt-BR", {
  timeZone: academyZone, dateStyle: "short", timeStyle: "short",
});

function defaultPeriod() {
  const ate = civilDate.format(new Date());
  const start = new Date(ate + "T00:00:00Z");
  start.setUTCDate(start.getUTCDate() - 29);
  return { de: start.toISOString().slice(0, 10), ate, pagina: 1 };
}

export function StaffAttendance({ back }: { back: string }) {
  const { clientId } = useParams();
  return <Attendance key={clientId} clientId={clientId} back={back} />;
}

export function Attendance({ clientId, back }: { clientId?: string; back?: string }) {
  const [query, setQuery] = useState(defaultPeriod);
  const [invalidPeriod, setInvalidPeriod] = useState(false);
  const load = useCallback((signal: AbortSignal) => loadAttendance(query, signal, clientId), [query, clientId]);
  const { data, reload } = useAccessQuery(load);

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    const de = String(form.get("de") ?? "");
    const ate = String(form.get("ate") ?? "");
    if (!de || !ate || de > ate) {
      setInvalidPeriod(true);
      return;
    }
    setInvalidPeriod(false);
    setQuery({ de, ate, pagina: 1 });
  }

  return <section className="directory" aria-labelledby="attendance-title">
    <h2 id="attendance-title">{back ? "Frequência do cliente" : "Minha frequência"}</h2>
    {back && <p><Link to={back}>Voltar à lista de clientes</Link></p>}
    <p className="directory-meta">Horários de São Paulo.</p>
    <form className="directory-actions attendance-period" onSubmit={submit}>
      <label className="ac-field">Data inicial<input className="ac-field-control" type="date" name="de" required defaultValue={query.de} /></label>
      <label className="ac-field">Data final<input className="ac-field-control" type="date" name="ate" required defaultValue={query.ate} /></label>
      <Button type="submit" variant="secondary">Consultar frequência</Button>
    </form>
    {invalidPeriod && <StatusMessage state="error" title="A data inicial deve ser igual ou anterior à final." />}
    {data === undefined ? <StatusMessage state="loading" title="Carregando frequência…" />
      : data === null ? <>
        <StatusMessage state="error" title="Não foi possível consultar a frequência." />
        <Button variant="secondary" onClick={reload}>Tentar novamente</Button>
      </> : <>
        {back && <h3>{data.cliente_nome}</h3>}
        {data.itens.length === 0 ? <StatusMessage state="empty"
          title={data.total === 0 ? "Nenhuma visita registrada neste período." : "Nenhuma visita nesta página."} />
          : <ul className="directory-cards" aria-label="Visitas confirmadas">
            {data.itens.map(item => <li className="directory-card" key={item.id}>
              <dl className="attendance-visit">
                <div><dt>Entrada</dt><dd><time dateTime={item.entrada_em}>{visitTime.format(new Date(item.entrada_em))}</time></dd></div>
                <div><dt>Saída</dt><dd>{item.saida_em
                  ? <time dateTime={item.saida_em}>{visitTime.format(new Date(item.saida_em))}</time>
                  : "Sem saída confirmada"}</dd></div>
              </dl>
            </li>)}
          </ul>}
        <DirectoryPager page={data} label="Páginas de frequência"
          changePage={pagina => setQuery(current => ({ ...current, pagina }))} />
      </>}
  </section>;
}
