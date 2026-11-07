import { Route, Routes } from "react-router-dom";

import { ServiceStatus } from "./features/status/ServiceStatus";

export function App() {
  return (
    <main className="shell">
      <h1>AcademIA</h1>
      <p>Gestão de academia e acompanhamento de treinos.</p>
      <Routes>
        <Route path="/" element={<ServiceStatus />} />
      </Routes>
    </main>
  );
}
