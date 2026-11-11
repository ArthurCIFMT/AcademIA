import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useParams } from "react-router-dom";
import { ApiError } from "../../lib/api/auth";
import { publish, readDetail, readQueue, resend, review, type Detail, type MailStatus, type Queue } from "./api";
import "./training-review.css";

export const reviewPath = (client: string, version: string) =>
  "/area/instrutor/clientes/" + encodeURIComponent(client) + "/treinos/" + encodeURIComponent(version) + "/revisao";

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
  return <section className="training-review">
    <h3>Fichas aguardando parecer</h3>
    <p>A publicação permite a consulta pelo cliente antes da avaliação do instrutor.</p>
    <button type="button" onClick={() => { setData(null); setRefresh((value) => value + 1); }}>Atualizar fila</button>
    {error && <p role="alert">{error}</p>}
    {!data && !error && <p role="status">Carregando fila…</p>}
    {data && <>
      {data.total === 0 && <p>Nenhuma ficha aguardando parecer.</p>}
      <ul>{data.itens.map((item) => <li key={item.versao_id}>
        <Link to={reviewPath(item.cliente_id, item.versao_id)}>{item.cliente_nome} · Versão {item.numero}</Link>
        <p>Publicada em {new Date(item.publicada_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}</p>
      </li>)}</ul>
      <nav aria-label="Páginas de pareceres">
        <button type="button" disabled={page === 1} onClick={() => { setData(null); setPage(page - 1); }}>Anterior</button>
        <button type="button" disabled={page * data.limite >= data.total} onClick={() => { setData(null); setPage(page + 1); }}>Próxima</button>
      </nav>
    </>}
  </section>;
}

function VersionReview({ clientId, versionId, csrf, userId }: {
  clientId: string; versionId: string; csrf: string; userId: string;
}) {
  const [data, setData] = useState<Detail | null>(null);
  const [refresh, setRefresh] = useState(0);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const [confirmed, setConfirmed] = useState(false);
  const [decision, setDecision] = useState<"ACEITO" | "REJEITADO">("ACEITO");
  const [reason, setReason] = useState("");
  const [mail, setMail] = useState<MailStatus | null>(null);
  const [publishId] = useState(() => crypto.randomUUID());
  const [opinionId, setOpinionId] = useState(() => crypto.randomUUID());
  useEffect(() => {
    const controller = new AbortController();
    void readDetail(clientId, versionId, controller.signal).then(
      (value) => { if (!controller.signal.aborted) { setData(value); setError(""); setConfirmed(false); } },
      (failure: unknown) => { if (!controller.signal.aborted) { setData(null); setError(failureMessage(failure)); } },
    );
    const focus = () => { if (!busyRef.current) { setData(null); setRefresh((value) => value + 1); } };
    window.addEventListener("focus", focus);
    return () => { controller.abort(); window.removeEventListener("focus", focus); };
  }, [clientId, versionId, refresh]);

  async function publishSaved() {
    if (!data || !confirmed || busy) return;
    busyRef.current = true; setBusy(true); setError("");
    try {
      const result = await publish(clientId, data, csrf, publishId);
      setData(result.treino); setMail(result.aviso_email);
    } catch (failure) {
      if (failure instanceof ApiError && [401, 403].includes(failure.status)) setData(null);
      setError(failureMessage(failure));
    }
    finally { busyRef.current = false; setBusy(false); }
  }
  async function submit(event: FormEvent) {
    event.preventDefault();
    if (busy || !data) return;
    busyRef.current = true; setBusy(true); setError("");
    try {
      setData(await review(clientId, versionId, csrf, {
        solicitacao_id: opinionId, estado: decision, motivo: reason.trim() || null,
      }));
    } catch (failure) {
      if (failure instanceof ApiError && [401, 403].includes(failure.status)) setData(null);
      setError(failureMessage(failure));
    }
    finally { busyRef.current = false; setBusy(false); }
  }
  async function sendNotice() {
    if (busy) return;
    busyRef.current = true; setBusy(true); setError("");
    try { setMail(await resend(clientId, versionId, csrf, mail?.tentativas ?? 1)); }
    catch (failure) {
      if (failure instanceof ApiError && [401, 403].includes(failure.status)) setData(null);
      setError(failureMessage(failure));
    }
    finally { busyRef.current = false; setBusy(false); }
  }
  if (!data) return <>{error ? <p role="alert">{error}</p> : <p role="status">Carregando versão…</p>}
    <button type="button" disabled={busy} onClick={() => { setData(null); setRefresh((value) => value + 1); }}>Recarregar versão</button></>;
  const draft = data.ficha.estado_publicacao === "RASCUNHO";
  const expired = data.ficha.estado_publicacao === "CONTEUDO_EXPIRADO";
  return <section className="training-review">
    <h4>Versão {data.ficha.numero}</h4>
    <p>{draft ? "Rascunho salvo" : expired ? "Conteúdo expirado" : data.ficha.vigente ? "Ficha vigente" : "Ficha histórica"}</p>
    <p>Parecer {data.parecer.estado}</p>
    {data.parecer.criado_em && <p>Instrutor {data.parecer.instrutor_id} · {new Date(data.parecer.criado_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}</p>}
    {data.parecer.motivo && <p>Motivo · {data.parecer.motivo}</p>}
    {expired ? <p>O conteúdo desta versão foi excluído pela retenção. Seus metadados permanecem registrados.</p> :
      data.ficha.dias.map((day, index) => <section key={index}>
        <h5>{day.titulo}</h5>
        <ol>{day.itens.map((item, position) => <li key={position}>
          <strong>{String(item.exercicio_snapshot?.nome ?? "Exercício")}</strong>
          <p>{item.series} séries · {item.repeticoes} repetições · Intervalo {item.intervalo_segundos}s</p>
          <p>Carga {item.carga_kg ?? "não informada"} kg · Cadência {item.cadencia ?? "não informada"}</p>
          {item.observacoes && <p>{item.observacoes}</p>}
        </li>)}</ol>
      </section>)}
    {error && <p role="alert">{error}</p>}
    <button type="button" disabled={busy} onClick={() => { setData(null); setRefresh((value) => value + 1); }}>Recarregar versão</button>
    {draft && data.ficha.autor_id === userId && <>
      <p>Confira as restrições no <Link to={"/area/instrutor/clientes/" + encodeURIComponent(clientId) + "/avaliacoes"}>onboarding e avaliações do cliente</Link>.</p>
      <label><input type="checkbox" checked={confirmed} disabled={busy} onChange={(event) => setConfirmed(event.target.checked)} />
        Conferi as restrições e o conteúdo salvo desta versão</label>
      <button type="button" disabled={busy || !confirmed} onClick={() => void publishSaved()}>Publicar versão salva</button>
    </>}
    {!draft && !expired && data.parecer.estado === "PENDENTE" && <>
      <p>Esta ficha já pode ser consultada pelo cliente. O parecer é posterior à publicação.</p>
      <form onSubmit={(event) => void submit(event)}>
        <fieldset disabled={busy}>
          <legend>Parecer desta versão</legend>
          <label htmlFor="review-decision">Decisão</label>
          <select id="review-decision" value={decision} onChange={(event) => {
            setDecision(event.target.value as "ACEITO" | "REJEITADO"); setOpinionId(crypto.randomUUID());
          }}><option value="ACEITO">Aceitar</option><option value="REJEITADO">Rejeitar</option></select>
          <label htmlFor="review-reason">Motivo do parecer</label>
          <textarea id="review-reason" maxLength={1000} required={decision === "REJEITADO"}
            value={reason} onChange={(event) => { setReason(event.target.value); setOpinionId(crypto.randomUUID()); }} />
          <p>O parecer conclusivo fica registrado. Para corrigir a prescrição, crie uma nova versão no editor.</p>
          <button type="submit">Registrar parecer</button>
        </fieldset>
      </form>
      {mail && <p role="status">Aviso por e-mail · {mail.estado} · Tentativa {mail.tentativas}</p>}
      {(!mail || (mail.estado === "FALHOU" && mail.tentativas < 3)) &&
        <button type="button" disabled={busy} onClick={() => void sendNotice()}>Tentar envio do aviso</button>}
    </>}
  </section>;
}

export function TrainingReviewPage({ csrf, userId }: { csrf: string; userId: string }) {
  const { clientId, versionId } = useParams();
  return <>
    <h3>Publicação e parecer da ficha</h3>
    <p><Link to="/area/instrutor/revisoes">Fila de avaliação</Link></p>
    {clientId && <p><Link to={"/area/instrutor/clientes/" + encodeURIComponent(clientId) + "/treinos"}>Editar ou copiar para nova versão</Link></p>}
    {clientId && versionId && <VersionReview key={clientId + versionId} clientId={clientId} versionId={versionId} csrf={csrf} userId={userId} />}
  </>;
}
