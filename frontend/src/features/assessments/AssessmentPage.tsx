import { useEffect, useRef, useState, type FormEvent } from "react";
import { useParams } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { ClientWorkspaceNav } from "../assignments/ClientWorkspaceNav";
import { OnboardingFields } from "../onboarding/OnboardingFields";
import { createAssessment, getAssessments, type AssessmentHistory, type AssessmentRequest } from "./api";
import "../onboarding/onboarding.css";

const dateFormat = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo",
});

function denied(error: unknown) {
  return error instanceof ApiError && (error.status === 401 || error.status === 403);
}

function Assessments({ clientId, csrf }: { clientId: string; csrf: string }) {
  const [query, setQuery] = useState({ page: 1 });
  const [view, setView] = useState<AssessmentHistory | null>(null);
  const [loadError, setLoadError] = useState<"denied" | "network" | null>(null);
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const lastRequest = useRef<AssessmentRequest | null>(null);
  const writing = useRef<AbortController | null>(null);
  useEffect(() => () => writing.current?.abort(), []);

  useEffect(() => {
    const controller = new AbortController();
    void getAssessments(clientId, query.page, controller.signal).then(
      (result) => { if (!controller.signal.aborted) setView(result); },
      (failure: unknown) => {
        if (controller.signal.aborted) return;
        if (denied(failure)) {
          setNote("");
          lastRequest.current = null;
        }
        setLoadError(denied(failure) ? "denied" : "network");
      },
    );
    return () => controller.abort();
  }, [clientId, query]);

  function load(page: number) {
    setView(null);
    setLoadError(null);
    setError("");
    setQuery({ page });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const snapshot = view?.snapshot;
    if (!snapshot || writing.current) return;
    const text = note.trim();
    if (!text) {
      setError("Preencha a observação para registrar a avaliação.");
      return;
    }
    if (lastRequest.current?.onboarding_id !== snapshot.id || lastRequest.current.observacao !== text) {
      lastRequest.current = { onboarding_id: snapshot.id, observacao: text, solicitacao_id: crypto.randomUUID() };
    }
    setError("");
    setNotice("");
    setBusy(true);
    const controller = new AbortController();
    writing.current = controller;
    try {
      await createAssessment(clientId, csrf, lastRequest.current, controller.signal);
      if (controller.signal.aborted) return;
      lastRequest.current = null;
      setNote("");
      setNotice("Avaliação registrada.");
      load(1);
    } catch (failure) {
      if (controller.signal.aborted) return;
      if (denied(failure)) {
        lastRequest.current = null;
        setNote("");
        setView(null);
        setLoadError("denied");
      } else {
        setError(failure instanceof ApiError && [404, 409].includes(failure.status)
          ? "O onboarding mudou. Recarregue e confira a versão antes de registrar."
          : "Não foi possível confirmar o registro. A observação continua nesta tela.");
      }
    } finally {
      writing.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  if (loadError === "denied") return <StatusMessage state="error" title="Seu acesso à avaliação deste cliente não está disponível." />;
  if (loadError === "network") return (
    <>
      <StatusMessage state="error" title="Não foi possível consultar as avaliações." />
      <Button variant="secondary" onClick={() => load(query.page)}>Tentar novamente</Button>
    </>
  );
  if (!view) return <StatusMessage state="loading" title="Carregando avaliações…" />;
  const { historico, snapshot } = view;
  return (
    <div>
      <h3>{view.cliente_nome}</h3>
      {notice && <StatusMessage state="success" title={notice} />}
      {snapshot ? (
        <>
          <details className="instructor-card onboarding-form">
            <summary>Onboarding concluído · versão {snapshot.numero}</summary>
            <OnboardingFields data={snapshot.dados} />
          </details>
          <form className="instructor-card" onSubmit={(event) => void submit(event)}>
            <h4>Registrar avaliação</h4>
            <div className="ac-field">
              <label className="ac-field-label" htmlFor="assessment-note">Observação da avaliação</label>
              <textarea id="assessment-note" className="ac-field-control" rows={4} maxLength={1000} required disabled={busy} value={note}
                onChange={(event) => setNote(event.target.value)} />
            </div>
            {error && <StatusMessage state="error" title={error} />}
            <div className="instructor-actions">
              <Button type="submit" pending={busy} pendingLabel="Registrando…">Registrar avaliação</Button>
              <Button variant="secondary" disabled={busy} onClick={() => load(1)}>Recarregar dados</Button>
            </div>
          </form>
        </>
      ) : <p>O cliente ainda não concluiu o onboarding.</p>}

      <section aria-label="Histórico de avaliações">
        <h3>Histórico de avaliações</h3>
        {historico.itens.length ? (
          <ul className="instructor-cards">{historico.itens.map((item) => (
            <li key={item.id} className="instructor-card">
              <strong>{item.instrutor_nome}</strong> · <time dateTime={item.registrado_em}>
                {dateFormat.format(new Date(item.registrado_em))}
              </time>
              <details>
                <summary>Ver observação</summary>
                <p className="instructor-note">{item.observacao ?? "Observação indisponível"}</p>
              </details>
            </li>
          ))}</ul>
        ) : <p>Nenhuma avaliação nesta página.</p>}
        {(historico.total > historico.limite || historico.pagina > 1) && <nav aria-label="Páginas das avaliações" className="instructor-actions">
          <Button variant="secondary" disabled={busy || historico.pagina <= 1}
            onClick={() => load(historico.pagina - 1)}>Anterior</Button>
          <Button variant="secondary" disabled={busy || historico.pagina * historico.limite >= historico.total}
            onClick={() => load(historico.pagina + 1)}>Próxima</Button>
        </nav>}
      </section>
    </div>
  );
}

export function AssessmentPage({ csrf }: { csrf: string }) {
  const { clientId } = useParams();
  return (
    <section className="instructor-workspace">
      <h2>Avaliações do cliente</h2>
      {clientId && <ClientWorkspaceNav clientId={clientId} />}
      {clientId && <Assessments key={clientId} clientId={clientId} csrf={csrf} />}
    </section>
  );
}
