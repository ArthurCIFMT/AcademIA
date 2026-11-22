import { TrainingChatPage } from "../features/training-chat/TrainingChat";
import { AITrainingPage } from "../features/ai-training/AITraining";
import { Link, Navigate, Outlet, Route, Routes, useLocation, useMatch, useOutletContext } from "react-router-dom";

import { AssessmentPage } from "../features/assessments/AssessmentPage";
import { AssignmentPage, MyAssignmentsPage } from "../features/assignments/AssignmentPages";
import { LoginForm } from "../features/auth/LoginForm";
import { RequestRecoveryPage, ResetPasswordPage } from "../features/auth/RecoveryPages";
import { useSession, type SessionController } from "../features/auth/useSession";
import { EquipmentCatalogPage, EquipmentInventoryPage } from "../features/equipment/EquipmentPages";
import { TrainingQueuePage, TrainingReviewPage } from "../features/training-review/TrainingReview";
import { CorpusPage } from "../features/corpus/CorpusPage";
import { MyTrainingPage } from "../features/my-training/MyTraining";
import { WorkoutEditorPage } from "../features/training-editor/WorkoutEditor";
import { ExerciseCatalog } from "../features/exercises/ExerciseCatalog";
import { InviteOnboardingPage, OwnOnboardingPage } from "../features/onboarding/OnboardingPages";
import { PendingNotices } from "../features/notifications/PendingNotices";
import { ClientDirectory } from "../features/clients/ClientDirectory";
import { StaffDirectory } from "../features/staff/StaffDirectory";
import { ServiceStatus } from "../features/status/ServiceStatus";
import { roles, type Role, type Session } from "../lib/api/auth";
import { Button, StatusMessage } from "../ui/primitives";
import { areas, paths } from "./areaNavigation";
import { AreaFrame, PublicFrame, PublicLayout } from "./Frames";

function SessionBoundary() {
  const isOnboarding = useMatch(paths.clientOnboarding) !== null;
  const isEquipmentAdmin = useMatch(paths.equipment) !== null;
  const isAdminExercises = useMatch(paths.adminExercises) !== null;
  const isInstructorExercises = useMatch(paths.instructorExercises) !== null;
  const isWorkoutEditor = useMatch("/area/instrutor/clientes/:clientId/treinos") !== null;
  const isTrainingReview = useMatch("/area/instrutor/clientes/:clientId/treinos/:versionId/revisao") !== null;
  const isTechnicalCorpus = useMatch(paths.corpus) !== null;
  const isCorpus = useMatch("/area/administracao/corpus") !== null || isTechnicalCorpus;
  const isAIGeneration = useMatch(paths.clientGeneration) !== null;
  const isChat = useMatch(paths.clientAssistant) !== null;
  const session = useSession(isChat || isAIGeneration || isCorpus || isOnboarding || isEquipmentAdmin || isAdminExercises || isInstructorExercises || isWorkoutEditor || isTrainingReview);
  const { state } = session;

  if (state.status === "checking") return <PublicFrame><StatusMessage state="loading" title="Verificando sessão…" /></PublicFrame>;
  if (state.status === "signingOut") return <PublicFrame><StatusMessage state="loading" title="Encerrando sessão…" /></PublicFrame>;
  if (state.status === "unavailable") {
    return (
      <PublicFrame>
        <StatusMessage state="error" title="Não foi possível verificar sua sessão." />
        <Button onClick={() => void session.retrySession()}>Tentar novamente</Button>
      </PublicFrame>
    );
  }
  if (state.status === "logoutFailed") {
    return (
      <PublicFrame>
        <StatusMessage state="error" title="Não foi possível confirmar a saída." />
        <Button onClick={() => void session.signOut()}>Tentar novamente</Button>
      </PublicFrame>
    );
  }
  return <Outlet context={session} />;
}

function LoginPage() {
  const { state, signIn } = useOutletContext<SessionController>();

  if (state.status === "active") return <Navigate to="/area" replace />;
  return (
    <PublicFrame>
      <LoginForm onLogin={signIn} notice={state.status === "expired"
        ? <p role="status">Sua sessão expirou. Entre novamente.</p>
        : state.status === "denied"
          ? <StatusMessage state="error" title="Acesso não permitido. Entre novamente." /> : null} />
    </PublicFrame>
  );
}

function AccessDenied() {
  return (
    <section className="site-denied" role="alert">
      <h1>Acesso não permitido</h1>
      <p>Você precisa de permissão para acessar esta área.</p>
    </section>
  );
}

type Feature = "training-chat" | "ai-training" | "staff" | "clients" | "assignments" | "my-assignments"
  | "onboarding" | "assessments" | "equipment" | "exercises" | "training-editor" | "training-review"
  | "training-queue" | "my-training" | "corpus";

function AreaContent({ feature, role, session, retrySession }: {
  feature?: Feature; role: Role; session: Session; retrySession: () => Promise<void>;
}) {
  const { user_id: userId, csrf_token: csrf } = session;
  switch (feature) {
    case "equipment": return <EquipmentInventoryPage key={userId} csrf={csrf} />;
    case "exercises": return <ExerciseCatalog key={userId} csrf={csrf} />;
    case "onboarding": return <OwnOnboardingPage key={userId} csrf={csrf} />;
    case "staff": return <StaffDirectory key={userId} session={session} onAccessChange={retrySession} />;
    case "assignments": return <AssignmentPage csrf={csrf} />;
    case "training-review": return <TrainingReviewPage key={userId} csrf={csrf} userId={userId} />;
    case "training-queue": return <TrainingQueuePage key={userId} />;
    case "training-chat": return <TrainingChatPage key={userId} csrf={csrf} />;
    case "ai-training": return <AITrainingPage key={userId} csrf={csrf} />;
    case "my-training": return <MyTrainingPage key={userId} clientId={userId} />;
    case "training-editor": return <WorkoutEditorPage key={userId} csrf={csrf} userId={userId} />;
    case "assessments": return <AssessmentPage key={userId} csrf={csrf} />;
    case "my-assignments": return <MyAssignmentsPage />;
    case "clients": return <ClientDirectory key={userId} session={session} onAccessChange={retrySession} />;
    case "corpus": return <CorpusPage key={userId} csrf={csrf} />;
    default: return role === "ADMINISTRADOR" || role === "INSTRUTOR"
      ? <PendingNotices key={userId} /> : <p>Escolha uma tarefa no menu da área.</p>;
  }
}

function AreaPage({ requiredRole, feature }: { requiredRole?: Role; feature?: Feature }) {
  const { state, signOut, retrySession } = useOutletContext<SessionController>();
  const { pathname } = useLocation();

  if (state.status === "denied") {
    return (
      <PublicFrame>
        <AccessDenied />
        <Link to="/login">Entrar novamente</Link>
      </PublicFrame>
    );
  }
  if (state.status !== "active") return <Navigate to="/login" replace />;

  const allowed = roles.filter((role) => state.session.roles.includes(role));
  if (!requiredRole && allowed.length > 0) {
    return <Navigate to={areas[allowed[0]].path} replace />;
  }
  const role = requiredRole && allowed.includes(requiredRole) ? requiredRole : undefined;
  const maintenance = import.meta.env.VITE_CORPUS_MAINTENANCE_ENABLED === "true";
  const activePath = feature === "training-review" ? paths.reviews
    : feature === "training-editor" || feature === "assessments" ? paths.assignedClients
      : pathname.replace(/\/+$/, "").toLowerCase();
  return (
    <AreaFrame role={role} allowed={allowed} activePath={activePath} maintenance={maintenance} signOut={signOut}>
      {role && (feature !== "corpus" || maintenance)
        ? <AreaContent feature={feature} role={role} session={state.session} retrySession={retrySession} />
        : <AccessDenied />}
    </AreaFrame>
  );
}

export function AppRoutes() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={
          <section className="site-welcome">
            <h1>AcademIA</h1>
            <p>Gestão de academia e acompanhamento de treinos.</p>
            <div className="site-entry-links">
              <Link to="/login">Entrar</Link>
              <Link to={paths.equipmentCatalog}>Equipamentos disponíveis</Link>
            </div>
            <ServiceStatus />
          </section>
        } />
        <Route path={paths.equipmentCatalog} element={<EquipmentCatalogPage />} />
        <Route path="/recuperar-acesso" element={<RequestRecoveryPage />} />
        <Route path="/redefinir-senha" element={<ResetPasswordPage key="redefinir" />} />
        <Route path="/primeiro-acesso" element={<ResetPasswordPage key="primeiro-acesso" firstAccess />} />
        <Route path="/onboarding/convite" element={<div className="site-invitation"><InviteOnboardingPage /></div>} />
      </Route>
      <Route element={<SessionBoundary />}>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/area" element={<AreaPage />} />
        <Route path={paths.adminExercises} element={<AreaPage requiredRole="ADMINISTRADOR" feature="exercises" />} />
        <Route path={paths.instructorExercises} element={<AreaPage requiredRole="INSTRUTOR" feature="exercises" />} />
        <Route path="/area/administracao/corpus" element={<Navigate to={paths.corpus} replace />} />
        <Route path={paths.corpus} element={<AreaPage requiredRole="ADMINISTRADOR" feature="corpus" />} />
        <Route path={paths.equipment} element={<AreaPage requiredRole="ADMINISTRADOR" feature="equipment" />} />
        <Route path={paths.staff} element={<AreaPage requiredRole="ADMINISTRADOR" feature="staff" />} />
        <Route path={paths.adminClients} element={<AreaPage requiredRole="ADMINISTRADOR" feature="clients" />} />
        <Route path={paths.attendantClients} element={<AreaPage requiredRole="ATENDENTE" feature="clients" />} />
        <Route path={paths.assignments} element={<AreaPage requiredRole="ADMINISTRADOR" feature="assignments" />} />
        <Route path={paths.assignedClients} element={<AreaPage requiredRole="INSTRUTOR" feature="my-assignments" />} />
        <Route path={paths.reviews} element={<AreaPage requiredRole="INSTRUTOR" feature="training-queue" />} />
        <Route path="/area/instrutor/clientes/:clientId/treinos/:versionId/revisao" element={<AreaPage requiredRole="INSTRUTOR" feature="training-review" />} />
        <Route path="/area/instrutor/clientes/:clientId/treinos" element={<AreaPage requiredRole="INSTRUTOR" feature="training-editor" />} />
        <Route path="/area/instrutor/clientes/:clientId/avaliacoes" element={<AreaPage requiredRole="INSTRUTOR" feature="assessments" />} />
        <Route path={paths.clientAssistant} element={<AreaPage requiredRole="CLIENTE" feature="training-chat" />} />
        <Route path={paths.clientGeneration} element={<AreaPage requiredRole="CLIENTE" feature="ai-training" />} />
        <Route path={paths.clientTraining} element={<AreaPage requiredRole="CLIENTE" feature="my-training" />} />
        <Route path={paths.clientOnboarding} element={<AreaPage requiredRole="CLIENTE" feature="onboarding" />} />
        {roles.map(role => <Route key={role} path={areas[role].path} element={<AreaPage requiredRole={role} />} />)}
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
