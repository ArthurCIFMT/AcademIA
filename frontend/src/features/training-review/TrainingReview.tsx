import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { ClientWorkspaceNav } from "../assignments/ClientWorkspaceNav";
import { loadContext } from "../training-editor/api";
import { publish, readDetail, readQueue, resend, review, type Detail, type MailStatus, type Queue } from "./api";
import { versionContext, type Context } from "../ai-training/api";
import { GenerationDetails } from "../ai-training/GenerationDetails";
import "../ai-training/ai-training.css";
import "./training-review.css";

export const reviewPath = (client: string, version: string) =>
  "/area/instrutor/clientes/" + encodeURIComponent(client) + "/treinos/" + encodeURIComponent(version) + "/revisao";
const denied = (error: unknown) => error instanceof ApiError && [401, 403].includes(error.status);

function failureMessage(error: unknown) {
  const status = error instanceof ApiError ? error.status : 0;
  if (status === 401 || status === 403) return "Seu acesso a esta ficha não está disponível.";
  if (status === 409) return "A ficha, o onboarding, o parecer ou os recursos mudaram. Recarregue e confira o conteúdo salvo.";
  if (status === 422) return "Confira os dias, os exercícios e o motivo do parecer.";
  return "Não foi possível confirmar a operação. Recarregue para consultar o estado salvo.";
}

export function TrainingQueuePage() {
  const [page, setPage] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [data, setData] = useState<Queue | null>(null);
  const [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    void readQueue(page, controller.signal).then(
      (value) => { if (!controller.signal.aborted) { setData(value); setError(""); } },
      (failure: unknown) => { if (!controller.signal.aborted) { setData(null); setError(failureMessage(failure)); } },
    );
    const focus = () => setRefresh((value) => value + 1);
    window.addEventListener("focus", focus);
    return () => { controller.abort(); window.removeEventListener("focus", focus); };
  }, [page, refresh]);
  return <section className="instructor-workspace">
    <h2>Fichas aguardando parecer</h2>
    <div className="instructor-actions">
      <Link to="/area/instrutor/clientes">Meus clientes</Link>
      <Button variant="secondary" disabled={!data && !error} onClick={() => {
        setData(null); setError(""); setRefresh(value => value + 1);
      }}>Atualizar fila</Button>
    </div>
    {error && <StatusMessage state="error" title={error} />}
    {!data && !error && <StatusMessage state="loading" title="Carregando fila…" />}
    {data && <>
      {data.itens.length === 0 && <StatusMessage state="empty" title="Nenhuma ficha aguardando parecer." />}
      <ul className="instructor-cards">{data.itens.map((item) => <li key={item.versao_id} className="instructor-card">
        <Link to={reviewPath(item.cliente_id, item.versao_id)}>{item.cliente_nome} · Versão {item.numero}</Link>
        <p>Publicada em {new Date(item.publicada_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}</p>
      </li>)}</ul>
      {(data.total > data.limite || page > 1) && <nav className="instructor-actions" aria-label="Páginas de pareceres">
        <button type="button" disabled={page === 1} onClick={() => { setData(null); setPage(page - 1); }}>Anterior</button>
        <button type="button" disabled={page * data.limite >= data.total} onClick={() => { setData(null); setPage(page + 1); }}>Próxima</button>
      </nav>}
    </>}
  </section>;
}

function VersionReview({ clientId, versionId, csrf, userId }: {
  clientId: string; versionId: string; csrf: string; userId: string;
}) {
  const [data, setData] = useState<Detail | null>(null);
  const [clientName, setClientName] = useState("");
  const [generation, setGeneration] = useState<Context | null>(null);
  const [contextError, setContextError] = useState("");
  const [refresh, setRefresh] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const writing = useRef<AbortController | null>(null);
  const reading = useRef<AbortController | null>(null);
  const revoked = useRef(false);
  const [accessLost, setAccessLost] = useState(false);
  const [notice, setNotice] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [decision, setDecision] = useState<"ACEITO" | "REJEITADO">("ACEITO");
  const [reason, setReason] = useState("");
  const [mail, setMail] = useState<MailStatus | null>(null);
  const [publishId] = useState(() => crypto.randomUUID());
  const [opinionId, setOpinionId] = useState(() => crypto.randomUUID());
  useEffect(() => () => writing.current?.abort(), []);
  const denyAccess = useCallback((failure: unknown) => {
    revoked.current = true;
    setAccessLost(true);
    reading.current?.abort();
    writing.current?.abort();
    setData(null); setGeneration(null); setClientName(""); setReason(""); setNotice(""); setConfirmed(false);
    setError(failureMessage(failure));
  }, []);
  useEffect(() => {
    if (revoked.current) return;
    const controller = new AbortController();
    reading.current = controller;
    void Promise.all([readDetail(clientId, versionId, controller.signal), loadContext(clientId, controller.signal)]).then(
      async ([value, context]) => {
        if (controller.signal.aborted) return;
        setClientName(context.cliente_nome);
        setData(value); setError(""); setConfirmed(false); setGeneration(null); setContextError("");
        if (value.ficha.origem === "IA") {
          try {
            const context = await versionContext(clientId, versionId, controller.signal);
            if (!controller.signal.aborted) {
              setGeneration(context);
              const notice = context.contexto.aviso;
              setMail(notice.email_estado ? { estado: notice.email_estado as MailStatus["estado"], tentativas: notice.email_tentativas } : null);
            }
          } catch (failure) {
            if (controller.signal.aborted) return;
            if (denied(failure)) denyAccess(failure);
            else setContextError("Não foi possível consultar as fontes e os avisos. Recarregue para conferir o contexto atual.");
          }
        }
      },
      (failure: unknown) => {
        if (controller.signal.aborted) return;
        if (denied(failure)) denyAccess(failure);
        else { setData(null); setError(failureMessage(failure)); }
      },
    );
    const focus = () => { if (!writing.current && !revoked.current) { setData(null); setRefresh(value => value + 1); } };
    window.addEventListener("focus", focus);
    return () => { controller.abort(); window.removeEventListener("focus", focus); };
  }, [clientId, versionId, refresh, denyAccess]);

  async function mutate(action: (signal: AbortSignal) => Promise<void>) {
    if (writing.current || revoked.current) return;
    const controller = new AbortController();
    writing.current = controller;
    setBusy(true); setError(""); setNotice("");
    try {
      await action(controller.signal);
    } catch (failure) {
      if (controller.signal.aborted) return;
      if (denied(failure)) denyAccess(failure);
      else setError(failureMessage(failure));
    } finally {
      writing.current = null;
      if (!controller.signal.aborted) setBusy(false);
    }
  }
  async function publishSaved() {
    if (!data || !confirmed) return;
    await mutate(async signal => {
      const result = await publish(clientId, data, csrf, publishId, signal);
      if (signal.aborted) return;
      setData(result.treino); setMail(result.aviso_email);
      setNotice("Ficha publicada. O cliente já pode consultá-la.");
    });
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!data) return;
    if (decision === "REJEITADO" && !reason.trim()) {
      setError("Informe o motivo para rejeitar a ficha.");
      return;
    }
    await mutate(async signal => {
      const reviewed = await review(clientId, versionId, csrf, {
        solicitacao_id: opinionId, estado: decision, motivo: reason.trim() || null,
      }, signal);
      if (signal.aborted) return;
      setData(reviewed);
      setNotice("Parecer registrado nesta versão.");
    });
  }
  async function sendNotice() {
    await mutate(async signal => {
      const delivered = await resend(clientId, versionId, csrf, mail?.tentativas ?? null, signal);
      if (signal.aborted) return;
      setMail(delivered);
      setGeneration((current) => current ? { ...current, contexto: { ...current.contexto, aviso: { ...current.contexto.aviso, email_estado: delivered?.estado ?? null, email_tentativas: delivered?.tentativas ?? 0 } } } : null);
    });
  }
  if (!data) return <>
    {error ? <StatusMessage state="error" title={error} /> : <StatusMessage state="loading" title="Carregando versão…" />}
    {error && !accessLost && <Button variant="secondary" onClick={() => {
      setError(""); setRefresh(value => value + 1);
    }}>Recarregar versão</Button>}
  </>;
  const draft = data.ficha.estado_publicacao === "RASCUNHO";
  const expired = data.ficha.estado_publicacao === "CONTEUDO_EXPIRADO";
  return <section className="training-review">
    <h3>{clientName} · Versão {data.ficha.numero}</h3>
    <div className="instructor-card">
      <p>{draft ? "Rascunho salvo" : expired ? "Conteúdo expirado" : data.ficha.vigente ? "Ficha vigente" : "Ficha histórica"}</p>
      <p className="review-status" data-decision={data.parecer.estado}>Parecer {data.parecer.estado}</p>
      <p className="instructor-meta">{data.ficha.origem === "MANUAL" ? "Ficha manual" : "Ficha gerada por IA"} · Revisão {data.ficha.revisao}</p>
      <details>
        <summary>Autoria e responsável pelo parecer</summary>
        {data.ficha.autor_id && <p>Autor da ficha · {data.ficha.autor_id === userId ? "Você" : data.ficha.autor_id}</p>}
        {data.parecer.criado_em && <p>Instrutor {data.parecer.instrutor_id === userId ? "responsável: você" : data.parecer.instrutor_id} · {new Date(data.parecer.criado_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}</p>}
        {!data.parecer.criado_em && <p>Parecer ainda não registrado.</p>}
      </details>
      {data.parecer.motivo && <p className="instructor-note">Motivo · {data.parecer.motivo}</p>}
    </div>
    {notice && <StatusMessage state="success" title={notice} />}
    {data.ficha.explicacao && !expired && <p>{data.ficha.explicacao}</p>}
    {generation && <><GenerationDetails data={generation} /><p><Link to={"/area/instrutor/clientes/" + encodeURIComponent(clientId) + "/avaliacoes"}>Conferir onboarding e avaliações atuais</Link></p></>}
    {contextError && <p role="status">{contextError}</p>}
    {expired ? <p>O conteúdo desta versão foi excluído pela retenção. Seus metadados permanecem registrados.</p> :
      data.ficha.dias.map((day, index) => <section key={index} className="instructor-card">
        <h4>{day.titulo}</h4>
        <ol>{day.itens.map((item, position) => <li key={position}>
          <strong>{String(item.exercicio_snapshot?.nome ?? "Exercício")}</strong>
          <p>{item.series} séries · {item.repeticoes} repetições · Intervalo {item.intervalo_segundos}s</p>
          <p>Carga {item.carga_kg === null ? "não informada" : item.carga_kg + " kg"} · Cadência {item.cadencia ?? "não informada"}</p>
          {item.observacoes && <p className="instructor-note">{item.observacoes}</p>}
        </li>)}</ol>
      </section>)}
    {error && <StatusMessage state="error" title={error} />}
    <Button variant="secondary" disabled={busy} onClick={() => {
      setData(null); setError(""); setNotice(""); setRefresh(value => value + 1);
    }}>Recarregar versão</Button>
    {draft && data.ficha.autor_id === userId && <section className="instructor-card">
      <h4>Publicar a ficha</h4>
      <p>A versão salva ficará disponível ao cliente com parecer pendente.</p>
      <p>Confira as restrições no <Link to={"/area/instrutor/clientes/" + encodeURIComponent(clientId) + "/avaliacoes"}>onboarding e avaliações do cliente</Link>.</p>
      <label><input type="checkbox" checked={confirmed} disabled={busy} onChange={(event) => setConfirmed(event.target.checked)} />
        Conferi as restrições e o conteúdo salvo desta versão</label>
      <Button disabled={busy || !confirmed} onClick={() => void publishSaved()}>Publicar versão salva</Button>
    </section>}
    {!draft && !expired && data.parecer.estado === "PENDENTE" && <>
      <p>Esta ficha já pode ser consultada pelo cliente. O parecer é posterior à publicação.</p>
      <form className="instructor-card" onSubmit={(event) => void submit(event)}>
        <fieldset disabled={busy}>
          <legend>Parecer desta versão</legend>
          <label htmlFor="review-decision">Decisão</label>
          <select id="review-decision" className="ac-field-control" value={decision} onChange={(event) => {
            setDecision(event.target.value as "ACEITO" | "REJEITADO"); setOpinionId(crypto.randomUUID());
          }}><option value="ACEITO">Aceitar</option><option value="REJEITADO">Rejeitar</option></select>
          <label htmlFor="review-reason">Motivo do parecer</label>
          <textarea id="review-reason" className="ac-field-control" rows={4} maxLength={1000} required={decision === "REJEITADO"}
            value={reason} onChange={(event) => { setReason(event.target.value); setOpinionId(crypto.randomUUID()); }} />
          <p>O parecer conclusivo fica registrado. Para corrigir a prescrição, crie uma nova versão no editor.</p>
          <Button type="submit" pending={busy} pendingLabel="Registrando…">Registrar parecer</Button>
        </fieldset>
      </form>
      {mail && !generation && <p role="status">Aviso por e-mail · {mail.estado} · Tentativa {mail.tentativas}</p>}
      {(!mail || (mail.estado === "FALHOU" && mail.tentativas < 3)) &&
        <Button variant="secondary" disabled={busy} onClick={() => void sendNotice()}>Tentar envio do aviso</Button>}
    </>}
  </section>;
}

export function TrainingReviewPage({ csrf, userId }: { csrf: string; userId: string }) {
  const { clientId, versionId } = useParams();
  return <section className="instructor-workspace">
    <h2>Publicação e parecer da ficha</h2>
    {clientId && <ClientWorkspaceNav clientId={clientId} />}
    <div className="instructor-actions"><Link to="/area/instrutor/revisoes">Fila de avaliação</Link></div>
    {clientId && versionId && <VersionReview key={clientId + versionId} clientId={clientId} versionId={versionId} csrf={csrf} userId={userId} />}
  </section>;
}
