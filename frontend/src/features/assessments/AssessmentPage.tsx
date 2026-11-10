import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
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
    if (!snapshot || busy) return;
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
    try {
      await createAssessment(clientId, csrf, lastRequest.current);
      lastRequest.current = null;
      setNote("");
      setNotice("Avaliação registrada.");
      load(1);
    } catch (failure) {
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
      setBusy(false);
    }
  }

  if (loadError === "denied") return <p role="alert">Seu acesso à avaliação deste cliente não está disponível.</p>;
  if (loadError === "network") return (
    <>
      <p role="alert">Não foi possível consultar as avaliações.</p>
      <button type="button" onClick={() => load(query.page)}>Tentar novamente</button>
    </>
  );
  if (!view) return <p role="status">Carregando avaliações…</p>;
  const { historico, snapshot } = view;
  return (
    <div className="onboarding-form">
      <h4>{view.cliente_nome}</h4>
      {notice && <p role="status">{notice}</p>}
      {snapshot ? (
        <>
          <details>
            <summary>Onboarding concluído · versão {snapshot.numero}</summary>
            <OnboardingFields data={snapshot.dados} />
          </details>
          <form onSubmit={(event) => void submit(event)}>
            <div className="onboarding-field">
              <label htmlFor="assessment-note">Observação da avaliação</label>
              <textarea id="assessment-note" maxLength={1000} required disabled={busy} value={note}
                onChange={(event) => setNote(event.target.value)} />
            </div>
            {error && <p role="alert">{error}</p>}
            <div className="onboarding-actions">
              <button type="submit" disabled={busy}>{busy ? "Registrando…" : "Registrar avaliação"}</button>
              <button type="button" disabled={busy} onClick={() => load(1)}>Recarregar dados</button>
            </div>
          </form>
        </>
      ) : <p>O cliente ainda não concluiu o onboarding.</p>}

      <section aria-label="Histórico de avaliações">
        <h3>Histórico de avaliações</h3>
        {historico.itens.length ? (
          <ul>{historico.itens.map((item) => (
            <li key={item.id}>
              <strong>{item.instrutor_nome}</strong> · <time dateTime={item.registrado_em}>
                {dateFormat.format(new Date(item.registrado_em))}
              </time>
              <p className="onboarding-field">{item.observacao ?? "Observação indisponível"}</p>
            </li>
          ))}</ul>
        ) : <p>Nenhuma avaliação nesta página.</p>}
        <nav aria-label="Páginas das avaliações" className="onboarding-actions">
          <button type="button" disabled={busy || historico.pagina <= 1}
            onClick={() => load(historico.pagina - 1)}>Anterior</button>
          <button type="button" disabled={busy || historico.pagina * historico.limite >= historico.total}
            onClick={() => load(historico.pagina + 1)}>Próxima</button>
        </nav>
      </section>
    </div>
  );
}

export function AssessmentPage({ csrf }: { csrf: string }) {
  const { clientId } = useParams();
  return (
    <>
      <h3>Avaliações do cliente</h3>
      <p><Link to="/area/instrutor/clientes">Voltar a meus clientes</Link></p>
      {clientId && <Assessments key={clientId} clientId={clientId} csrf={csrf} />}
    </>
  );
}
