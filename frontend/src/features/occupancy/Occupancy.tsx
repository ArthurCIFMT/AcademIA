import { requestApi } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { useAccessQuery } from "../attendance/useAccessQuery";

async function loadOccupancy(signal: AbortSignal) {
  return (await requestApi("/v1/acesso/lotacao", { signal })).json() as Promise<{ total_presentes: number }>;
}

export function Occupancy() {
  const { data, reload } = useAccessQuery(loadOccupancy);
  return <section className="directory" aria-labelledby="occupancy-title">
    <h2 id="occupancy-title">Lotação atual</h2>
    <div className="directory-card">
      {data === undefined ? <StatusMessage state="loading" title="Carregando lotação…" />
        : data === null ? <StatusMessage state="error" title="Não foi possível consultar a lotação." />
        : <p role="status"><strong>{data.total_presentes.toLocaleString("pt-BR")}</strong>
          {data.total_presentes === 1 ? " pessoa presente" : " pessoas presentes"}</p>}
      <div className="directory-actions">
        <Button variant="secondary" disabled={data === undefined} onClick={reload}>Atualizar lotação</Button>
      </div>
    </div>
  </section>;
}
