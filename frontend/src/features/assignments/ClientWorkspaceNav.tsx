import { Link, NavLink } from "react-router-dom";
import "./client-workspace.css";

export function ClientWorkspaceNav({ clientId }: { clientId: string }) {
  const root = "/area/instrutor/clientes";
  const client = root + "/" + encodeURIComponent(clientId);
  return <nav aria-label="Área do cliente designado" className="instructor-actions">
    <Link to={root}>Meus clientes</Link>
    <NavLink to={client + "/avaliacoes"}>Avaliações do cliente</NavLink>
    <NavLink to={client + "/treinos"}>Fichas de treino</NavLink>
  </nav>;
}
