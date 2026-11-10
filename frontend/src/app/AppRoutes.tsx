import type { ReactNode } from "react";
import { Link, NavLink, Navigate, Outlet, Route, Routes, useOutletContext } from "react-router-dom";

import { LoginForm } from "../features/auth/LoginForm";
import { RequestRecoveryPage, ResetPasswordPage } from "../features/auth/RecoveryPages";
import { useSession, type SessionController } from "../features/auth/useSession";
import { PendingNotices } from "../features/notifications/PendingNotices";
import { ClientDirectory } from "../features/clients/ClientDirectory";
import { StaffDirectory } from "../features/staff/StaffDirectory";
import { ServiceStatus } from "../features/status/ServiceStatus";
import { roles, type Role } from "../lib/api/auth";
import "../features/auth/auth.css";

const areas = {
  ADMINISTRADOR: { path: "administracao", link: "Administração", title: "Área administrativa" },
  ATENDENTE: { path: "atendimento", link: "Atendimento", title: "Área de atendimento" },
  INSTRUTOR: { path: "instrutor", link: "Instrutor", title: "Área do instrutor" },
  CLIENTE: { path: "cliente", link: "Cliente", title: "Área do cliente" },
} satisfies Record<Role, { path: string; link: string; title: string }>;

function SessionBoundary() {
  const session = useSession();
  const { state } = session;

  if (state.status === "checking") return <p role="status">Verificando sessão…</p>;
  if (state.status === "signingOut") return <p role="status">Encerrando sessão…</p>;
  if (state.status === "unavailable") {
    return (
      <>
        <p role="alert">Não foi possível verificar sua sessão.</p>
        <button type="button" onClick={() => void session.retrySession()}>Tentar novamente</button>
      </>
    );
  }
  if (state.status === "logoutFailed") {
    return (
      <>
        <p role="alert">Não foi possível confirmar a saída.</p>
        <button type="button" onClick={() => void session.signOut()}>Tentar novamente</button>
      </>
    );
  }
  return <Outlet context={session} />;
}

function LoginPage() {
  const { state, signIn } = useOutletContext<SessionController>();

  if (state.status === "active") return <Navigate to="/area" replace />;
  return (
    <>
      {state.status === "expired" && <p role="status">Sua sessão expirou. Entre novamente.</p>}
      {state.status === "denied" && <p role="alert">Acesso não permitido. Entre novamente.</p>}
      <LoginForm onLogin={signIn} />
    </>
  );
}

function AccessDenied() {
  return (
    <section role="alert">
      <h2>Acesso não permitido</h2>
      <p>Você precisa de permissão para acessar esta área.</p>
    </section>
  );
}

function AreaPage({ requiredRole, feature }: { requiredRole?: Role; feature?: "staff" | "clients" }) {
  const { state, signOut, retrySession } = useOutletContext<SessionController>();

  if (state.status === "denied") {
    return (
      <>
        <AccessDenied />
        <Link to="/login">Entrar novamente</Link>
      </>
    );
  }
  if (state.status !== "active") return <Navigate to="/login" replace />;

  const allowed = roles.filter((role) => state.session.roles.includes(role));
  if (!requiredRole && allowed.length > 0) {
    return <Navigate to={areas[allowed[0]].path} replace />;
  }

  const isAdmin = requiredRole === "ADMINISTRADOR" && allowed.includes("ADMINISTRADOR");
  const canManageClients = (requiredRole === "ADMINISTRADOR" || requiredRole === "ATENDENTE") && allowed.includes(requiredRole);
  const staffContent: ReactNode = feature === "staff" && isAdmin
    ? <StaffDirectory key={state.session.user_id} session={state.session} onAccessChange={retrySession} />
    : null;
  return (
    <>
      {requiredRole && allowed.includes(requiredRole)
        ? <h2>{areas[requiredRole].title}</h2>
        : <AccessDenied />}
      {allowed.length > 0 && (
        <nav aria-label="Áreas disponíveis">
          <ul className="area-links">
            {allowed.map((role) => (
              <li key={role}><NavLink to={"/area/" + areas[role].path}>{areas[role].link}</NavLink></li>
            ))}
          </ul>
        </nav>
      )}
      {isAdmin && <p><Link to="/area/administracao/funcionarios">Gerenciar funcionários</Link></p>}
      {canManageClients && <p>
        <Link to={"/area/" + areas[requiredRole].path + "/clientes"}>Gerenciar clientes</Link>
      </p>}
      {staffContent}
      {feature === "clients" && canManageClients &&
        <ClientDirectory key={state.session.user_id} session={state.session} onAccessChange={retrySession} />}
      {!feature && (requiredRole === "ADMINISTRADOR" || requiredRole === "INSTRUTOR") &&
        allowed.includes(requiredRole) && <PendingNotices key={state.session.user_id} />}
      <button type="button" onClick={() => void signOut()}>Sair</button>
    </>
  );
}

export function AppRoutes() {
  return (
    <>
      <h1>AcademIA</h1>
      <Routes>
        <Route path="/" element={
          <>
            <p>Gestão de academia e acompanhamento de treinos.</p>
            <Link to="/login">Entrar</Link>
            <ServiceStatus />
          </>
        } />
        <Route path="/recuperar-acesso" element={<RequestRecoveryPage />} />
        <Route path="/redefinir-senha" element={<ResetPasswordPage />} />
        <Route path="/primeiro-acesso" element={<ResetPasswordPage firstAccess />} />
        <Route element={<SessionBoundary />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/area" element={<AreaPage />} />
          <Route path="/area/administracao/funcionarios" element={<AreaPage requiredRole="ADMINISTRADOR" feature="staff" />} />
          <Route path="/area/administracao/clientes" element={<AreaPage requiredRole="ADMINISTRADOR" feature="clients" />} />
          <Route path="/area/atendimento/clientes" element={<AreaPage requiredRole="ATENDENTE" feature="clients" />} />
          {roles.map((role) => (
            <Route key={role} path={"/area/" + areas[role].path} element={<AreaPage requiredRole={role} />} />
          ))}
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
