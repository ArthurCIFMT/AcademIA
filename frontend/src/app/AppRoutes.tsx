import type { ReactNode } from "react";
import { Link, NavLink, Navigate, Outlet, Route, Routes, useMatch, useOutletContext } from "react-router-dom";

import { AssessmentPage } from "../features/assessments/AssessmentPage";
import { AssignmentPage, MyAssignmentsPage } from "../features/assignments/AssignmentPages";
import { LoginForm } from "../features/auth/LoginForm";
import { RequestRecoveryPage, ResetPasswordPage } from "../features/auth/RecoveryPages";
import { useSession, type SessionController } from "../features/auth/useSession";
import { EquipmentCatalogPage, EquipmentInventoryPage } from "../features/equipment/EquipmentPages";
import { TrainingQueuePage, TrainingReviewPage } from "../features/training-review/TrainingReview";
import { MyTrainingPage } from "../features/my-training/MyTraining";
import { WorkoutEditorPage } from "../features/training-editor/WorkoutEditor";
import { ExerciseCatalog } from "../features/exercises/ExerciseCatalog";
import { InviteOnboardingPage, OwnOnboardingPage } from "../features/onboarding/OnboardingPages";
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

const onboardingPath = "/area/cliente/onboarding";
const equipmentAdminPath = "/area/administracao/equipamentos";
const adminExercisePath = "/area/administracao/exercicios";
const instructorExercisePath = "/area/instrutor/exercicios";

function SessionBoundary() {
  const isOnboarding = useMatch(onboardingPath) !== null;
  const isEquipmentAdmin = useMatch(equipmentAdminPath) !== null;
  const isAdminExercises = useMatch(adminExercisePath) !== null;
  const isInstructorExercises = useMatch(instructorExercisePath) !== null;
  const isWorkoutEditor = useMatch("/area/instrutor/clientes/:clientId/treinos") !== null;
  const isTrainingReview = useMatch("/area/instrutor/clientes/:clientId/treinos/:versionId/revisao") !== null;
  const session = useSession(isOnboarding || isEquipmentAdmin || isAdminExercises || isInstructorExercises || isWorkoutEditor || isTrainingReview);
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

function AreaPage({ requiredRole, feature }: { requiredRole?: Role; feature?: "staff" | "clients" | "assignments" | "my-assignments" | "onboarding" | "assessments" | "equipment" | "exercises" | "training-editor" | "training-review" | "training-queue" | "my-training" }) {
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
  const isInstructor = requiredRole === "INSTRUTOR" && allowed.includes("INSTRUTOR");
  const isClient = requiredRole === "CLIENTE" && allowed.includes("CLIENTE");
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
      {isAdmin && feature !== "equipment" && <p><Link to={equipmentAdminPath}>Gerenciar equipamentos</Link></p>}
      {isClient && <p><Link to="/equipamentos">Equipamentos disponíveis</Link></p>}
      {isClient && feature !== "my-training" && <p><Link to="/area/cliente/treinos">Meus treinos</Link></p>}
      {feature === "equipment" && isAdmin && <EquipmentInventoryPage key={state.session.user_id} csrf={state.session.csrf_token} />}
      {canManageClients && <p>
        <Link to={"/area/" + areas[requiredRole].path + "/clientes"}>Gerenciar clientes</Link>
      </p>}
      {isInstructor && <p><Link to="/area/instrutor/clientes">Meus clientes</Link></p>}
      {isInstructor && <p><Link to="/area/instrutor/revisoes">Avaliar fichas publicadas</Link></p>}
      {(isAdmin || isInstructor) && feature !== "exercises" && (
        <p><Link to={isAdmin ? adminExercisePath : instructorExercisePath}>Catálogo de exercícios</Link></p>
      )}
      {feature === "exercises" && (isAdmin || isInstructor) &&
        <ExerciseCatalog key={state.session.user_id} csrf={state.session.csrf_token} />}
      {isClient && feature !== "onboarding" && <p><Link to={onboardingPath}>Meu onboarding</Link></p>}
      {feature === "onboarding" && isClient && <OwnOnboardingPage key={state.session.user_id} csrf={state.session.csrf_token} />}
      {staffContent}
      {feature === "assignments" && isAdmin && <AssignmentPage csrf={state.session.csrf_token} />}
      {feature === "training-review" && isInstructor && <TrainingReviewPage key={state.session.user_id} csrf={state.session.csrf_token} userId={state.session.user_id} />}
      {feature === "training-queue" && isInstructor && <TrainingQueuePage key={state.session.user_id} />}
      {feature === "my-training" && isClient && <MyTrainingPage key={state.session.user_id} clientId={state.session.user_id} />}
      {feature === "training-editor" && isInstructor && <WorkoutEditorPage key={state.session.user_id} csrf={state.session.csrf_token} userId={state.session.user_id} />}
      {feature === "assessments" && isInstructor && <AssessmentPage key={state.session.user_id} csrf={state.session.csrf_token} />}
      {feature === "my-assignments" && isInstructor && <MyAssignmentsPage />}
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
            <p><Link to="/equipamentos">Equipamentos disponíveis</Link></p>
            <ServiceStatus />
          </>
        } />
        <Route path="/equipamentos" element={<EquipmentCatalogPage />} />
        <Route path="/recuperar-acesso" element={<RequestRecoveryPage />} />
        <Route path="/redefinir-senha" element={<ResetPasswordPage />} />
        <Route path="/primeiro-acesso" element={<ResetPasswordPage firstAccess />} />
        <Route path="/onboarding/convite" element={<InviteOnboardingPage />} />
        <Route element={<SessionBoundary />}>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/area" element={<AreaPage />} />
          <Route path={adminExercisePath} element={<AreaPage requiredRole="ADMINISTRADOR" feature="exercises" />} />
          <Route path={instructorExercisePath} element={<AreaPage requiredRole="INSTRUTOR" feature="exercises" />} />
          <Route path={equipmentAdminPath} element={<AreaPage requiredRole="ADMINISTRADOR" feature="equipment" />} />
          <Route path="/area/administracao/funcionarios" element={<AreaPage requiredRole="ADMINISTRADOR" feature="staff" />} />
          <Route path="/area/administracao/clientes" element={<AreaPage requiredRole="ADMINISTRADOR" feature="clients" />} />
          <Route path="/area/atendimento/clientes" element={<AreaPage requiredRole="ATENDENTE" feature="clients" />} />
          <Route path="/area/administracao/designacoes" element={<AreaPage requiredRole="ADMINISTRADOR" feature="assignments" />} />
          <Route path="/area/instrutor/clientes" element={<AreaPage requiredRole="INSTRUTOR" feature="my-assignments" />} />
          <Route path="/area/instrutor/revisoes" element={<AreaPage requiredRole="INSTRUTOR" feature="training-queue" />} />
          <Route path="/area/instrutor/clientes/:clientId/treinos/:versionId/revisao" element={<AreaPage requiredRole="INSTRUTOR" feature="training-review" />} />
          <Route path="/area/instrutor/clientes/:clientId/treinos" element={<AreaPage requiredRole="INSTRUTOR" feature="training-editor" />} />
          <Route path="/area/instrutor/clientes/:clientId/avaliacoes" element={<AreaPage requiredRole="INSTRUTOR" feature="assessments" />} />
          <Route path="/area/cliente/treinos" element={<AreaPage requiredRole="CLIENTE" feature="my-training" />} />
          <Route path={onboardingPath} element={<AreaPage requiredRole="CLIENTE" feature="onboarding" />} />
          {roles.map((role) => (
            <Route key={role} path={"/area/" + areas[role].path} element={<AreaPage requiredRole={role} />} />
          ))}
        </Route>
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  );
}
