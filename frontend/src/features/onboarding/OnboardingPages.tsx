import { useEffect, useState, type FormEvent, type ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import {
  confirmUpdate, finishDraft, invitedDraft, InviteSessionChanged, openInvitation,
  ownOnboarding, saveDraft, WebLocksUnavailable,
  type Draft, type Scope, type Snapshot,
} from "./api";
import { prepareForm, type FormData } from "./form";
import { OnboardingFields } from "./OnboardingFields";
import "./onboarding.css";

const unavailableInvite = "O convite é inválido, expirou ou já foi usado. Solicite um novo link à academia.";
const unavailableBrowser = "Abra o convite em um navegador atualizado, por uma conexão segura.";
const dateFormat = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo",
});

function loadError(error: unknown, invite: boolean) {
  if (error instanceof ApiError && (error.status === 401 || error.status === 403)) {
    return invite ? unavailableInvite : "Sua sessão perdeu o acesso ao onboarding. Entre novamente.";
  }
  return null;
}

function Loader<T>({ load, invite = false, children }: {
  load: (signal: AbortSignal) => Promise<T>;
  invite?: boolean;
  children: (value: T, reload: () => void) => ReactNode;
}) {
  const [attempt, setAttempt] = useState(0);
  const [state, setState] = useState<
    { kind: "loading" } | { kind: "ready"; value: T } | { kind: "failed"; error: unknown }
  >({ kind: "loading" });
  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal).then(
      (value) => { if (!controller.signal.aborted) setState({ kind: "ready", value }); },
      (error: unknown) => { if (!controller.signal.aborted) setState({ kind: "failed", error }); },
    );
    return () => controller.abort();
  }, [load, attempt]);

  function reload() {
    setState({ kind: "loading" });
    setAttempt((count) => count + 1);
  }

  if (state.kind === "loading") return <p role="status">Carregando onboarding…</p>;
  if (state.kind === "ready") return children(state.value, reload);
  const denied = loadError(state.error, invite);
  return (
    <>
      <p role="alert">{denied ?? "Não foi possível carregar o formulário. Tente novamente."}</p>
      {!denied && <button type="button" onClick={reload}>Tentar novamente</button>}
      {denied && !invite && <Link to="/login">Entrar</Link>}
    </>
  );
}

function mutationError(error: unknown, invite: boolean) {
  if (error instanceof InviteSessionChanged) {
    return "Outro convite foi aberto neste navegador. Este rascunho não será enviado. Solicite outro link para retomá-lo.";
  }
  if (error instanceof WebLocksUnavailable) return unavailableBrowser;
  const denied = loadError(error, invite);
  if (denied) return denied;
  if (error instanceof ApiError && error.status === 409) {
    return "Há uma versão salva mais recente. Suas alterações continuam nesta tela.";
  }
  if (error instanceof ApiError && error.status === 422) {
    return "A API recusou os dados. Revise os campos e tente novamente.";
  }
  return "Não foi possível confirmar a operação. Seus dados continuam nesta tela. Tente novamente.";
}

function Editor({ initial, scope, onSaved, onComplete, onReload, onBack }: {
  initial: Draft | null;
  scope: Scope;
  onSaved?: (draft: Draft) => void;
  onComplete: (snapshot: Snapshot | null) => void;
  onReload: () => void;
  onBack?: () => void;
}) {
  const base = scope.kind === "own" ? scope.base : null;
  const [data, setData] = useState<FormData>(() => initial?.dados ?? base?.dados ?? {});
  const [revision, setRevision] = useState(initial?.revisao ?? null);
  const [candidate, setCandidate] = useState<FormData | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [conflict, setConflict] = useState(false);
  const [notice, setNotice] = useState("");

  function prepare(complete: boolean) {
    setError("");
    setNotice("");
    try {
      return prepareForm(data, complete);
    } catch (failure) {
      setError(failure instanceof Error ? failure.message : "Revise o formulário.");
    }
  }

  async function persist(values: FormData, finish: boolean) {
    setBusy(true);
    setConflict(false);
    try {
      if (finish && scope.kind === "own" && scope.base) {
        onComplete(await confirmUpdate(scope, revision, values));
        return;
      }
      const saved = await saveDraft(scope, revision, values);
      setRevision(saved.revisao);
      setData(saved.dados);
      onSaved?.(saved);
      if (finish) onComplete(await finishDraft(scope, saved.revisao));
      else setNotice("Rascunho salvo.");
    } catch (failure) {
      setError(mutationError(failure, scope.kind === "invite"));
      setConflict(failure instanceof ApiError && failure.status === 409);
    } finally {
      setBusy(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (busy || candidate) return;
    const values = prepare(true);
    if (!values) return;
    if (base) setCandidate(values);
    else void persist(values, true);
  }

  return (
    <form className="onboarding-form" autoComplete="off" noValidate onSubmit={handleSubmit}>
      <p>Preencha os dados para concluir. Se tiver dúvida sobre uma resposta de saúde, selecione “Não sei”.</p>
      <fieldset className="onboarding-editor" disabled={busy || candidate !== null}>
        <legend className="onboarding-legend">Formulário de onboarding</legend>
        <OnboardingFields data={data} onChange={(next) => { setData(next); setNotice(""); }} />
      </fieldset>
      {error && <p role="alert">{error}</p>}
      {notice && <p role="status">{notice}</p>}
      {busy && <p role="status">Salvando…</p>}
      {candidate ? (
        <section aria-label="Confirmar atualização">
          <p>Confirme a atualização para publicar uma nova versão dos seus dados. As versões anteriores ficam no histórico.</p>
          <div className="onboarding-actions">
            <button type="button" disabled={busy} onClick={() => {
              setError("");
              void persist(candidate, true);
            }}>Confirmar nova versão</button>
            <button type="button" disabled={busy} onClick={() => setCandidate(null)}>Voltar à edição</button>
          </div>
        </section>
      ) : (
        <div className="onboarding-actions">
          <button type="button" disabled={busy} onClick={() => {
            const values = prepare(false);
            if (values) void persist(values, false);
          }}>Salvar rascunho</button>
          <button type="submit" disabled={busy}>{base ? "Revisar atualização" : "Concluir onboarding"}</button>
          {onBack && <button type="button" disabled={busy} onClick={onBack}>
            Descartar alterações não salvas e voltar
          </button>}
        </div>
      )}
      {conflict && <p><button type="button" disabled={busy} onClick={onReload}>
        Descartar alterações locais e recarregar
      </button></p>}
    </form>
  );
}

function OwnForm({ initialDraft, initialSnapshot, csrf, reload }: {
  initialDraft: Draft | null; initialSnapshot: Snapshot | null; csrf: string; reload: () => void;
}) {
  const [snapshot, setSnapshot] = useState(initialSnapshot);
  const [draft, setDraft] = useState(initialDraft);
  const [editing, setEditing] = useState(initialSnapshot === null);

  if (!editing && snapshot) {
    return (
      <div className="onboarding-form">
        <p>Versão {snapshot.numero} concluída em {dateFormat.format(new Date(snapshot.concluido_em))}.</p>
        <button type="button" onClick={() => setEditing(true)}>{draft ? "Continuar atualização" : "Atualizar meus dados"}</button>
        <OnboardingFields data={snapshot.dados} />
      </div>
    );
  }
  return <Editor
    initial={draft} scope={{ kind: "own", csrf, base: snapshot }}
    onSaved={setDraft} onReload={reload} onBack={snapshot ? () => setEditing(false) : undefined}
    onComplete={(next) => { setSnapshot(next); setDraft(null); setEditing(false); }}
  />;
}

export function OwnOnboardingPage({ csrf }: { csrf: string }) {
  return (
    <>
      <h3>Meu onboarding</h3>
      <Loader load={ownOnboarding}>{(value, reload) =>
        <OwnForm initialDraft={value.rascunho} initialSnapshot={value.concluido} csrf={csrf} reload={reload} />
      }</Loader>
    </>
  );
}

function RestrictedForm({ initial, reload }: { initial: Draft; reload: () => void }) {
  const [done, setDone] = useState(false);
  if (done) return (
    <>
      <p role="status">Onboarding concluído.</p>
      <Link to="/login">Entrar para consultar meus dados</Link>
    </>
  );
  return <Editor initial={initial} scope={{ kind: "invite", draftId: initial.id }}
    onReload={reload} onComplete={() => setDone(true)} />;
}

function InviteFlow({ token, forget }: { token: string | null; forget: () => void }) {
  const [state, setState] = useState<"ready" | "opening" | "invalid" | "resume">(
    token === null ? "resume" : "ready",
  );
  const [opened, setOpened] = useState<Draft | null>(null);
  const [error, setError] = useState("");

  async function exchange() {
    if (!token || state === "opening") return;
    setState("opening");
    setError("");
    try {
      setOpened(await openInvitation(token));
      forget();
    } catch (failure) {
      if (loadError(failure, true)) {
        setState("invalid");
        forget();
      } else {
        setError(failure instanceof WebLocksUnavailable ? unavailableBrowser :
          "Não foi possível abrir o convite. Tente novamente. Se ele já tiver sido usado, solicite outro link.");
        setState("ready");
      }
    }
  }

  if (opened) return <RestrictedForm initial={opened} reload={() => {
    setOpened(null);
    setState("resume");
  }} />;
  if (state === "resume") return <Loader load={invitedDraft} invite>
    {(value, reload) => <RestrictedForm initial={value} reload={reload} />}
  </Loader>;
  if (state === "invalid" || !token || !/^[A-Za-z0-9_-]{43}$/.test(token)) {
    return <p role="alert">{unavailableInvite}</p>;
  }
  return (
    <>
      <p>Use seu convite para preencher os dados iniciais do AcademIA.</p>
      <button type="button" disabled={state === "opening"} onClick={() => void exchange()}>
        {state === "opening" ? "Abrindo…" : "Abrir formulário"}
      </button>
      {error && <p role="alert">{error}</p>}
    </>
  );
}

function readToken(hash: string) {
  if (!hash) return null;
  const tokens = new URLSearchParams(hash.slice(1)).getAll("token");
  return tokens.length === 1 ? tokens[0] : "";
}

export function InviteOnboardingPage() {
  const { hash, pathname } = useLocation();
  const navigate = useNavigate();
  const [link, setLink] = useState(() => ({ hash, attempt: 0, token: readToken(hash) }));
  if (hash !== link.hash) {
    setLink(hash ? { hash, attempt: link.attempt + 1, token: readToken(hash) } : { ...link, hash });
  }

  useEffect(() => {
    if (hash) void navigate(pathname, { replace: true });
  }, [hash, navigate, pathname]);

  return (
    <>
      <h2>Convite de onboarding</h2>
      <InviteFlow key={link.attempt} token={link.token} forget={() =>
        setLink((current) => current.attempt === link.attempt ? { ...current, token: null } : current)
      } />
    </>
  );
}
