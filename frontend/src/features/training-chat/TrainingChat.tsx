import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";

import { ApiError } from "../../lib/api/auth";
import { Button, FormField, StatusMessage } from "../../ui/primitives";
import { requestIdPattern } from "../ai-training/requestId";
import { useAssistantRequests } from "../ai-training/useAssistantRequests";
import { ask, context, differences, history, read, type Ask, type AdaptContext, type Diff, type Turn } from "./api";
import { ChatTurn, Comparison } from "./ChatTurn";
import "./training-chat.css";

function failure(error: unknown) {
  if (error instanceof ApiError) {
    if (error.status === 429) return "Limite de seis solicitações por minuto atingido. Aguarde antes de enviar novamente.";
    if (error.status === 409) return "A ficha ou o onboarding mudou ou está indisponível. Confira seus dados antes de adaptar.";
    if (error.status === 422) return "Confira a mensagem e o contexto da adaptação.";
    if (error.status === 404) return "A solicitação não está disponível nesta conta.";
    if (error.status === 503) return "O assistente está indisponível no momento. Tente mais tarde.";
  }
  return "Não foi possível confirmar a resposta. Consulte o estado salvo antes de repetir o mesmo pedido.";
}

type Adaptation = { revision: number; value: AdaptContext } | { revision: number; error: string };

export function TrainingChatPage({ csrf, mode = "DUVIDA" }: { csrf: string; mode?: Ask["finalidade"] }) {
  const [params, setParams] = useSearchParams();
  const id = params.get("solicitacao");
  const adapting = mode === "ADAPTACAO";
  const [turns, setTurns] = useState<Turn[] | null>(null);
  const [latest, setLatest] = useState<Turn | null>(null);
  const [text, setText] = useState("");
  const [adaptation, setAdaptation] = useState<Adaptation | null>(null);
  const [confirmed, setConfirmed] = useState(false);
  const [day, setDay] = useState(1);
  const [busy, setBusy] = useState(false);
  const [sendError, setSendError] = useState("");
  const [readError, setReadError] = useState("");
  const [historyError, setHistoryError] = useState("");
  const [page, setPage] = useState(1);
  const [refresh, setRefresh] = useState(0);
  const [diff, setDiff] = useState<Diff | null>(null);
  const [compareError, setCompareError] = useState("");
  const pending = useRef<Ask | null>(null);
  const writing = useRef(false);
  const comparing = useRef<AbortController | null>(null);
  const adaptRef = useRef<AdaptContext | null>(null);
  const { denied, start, release, handleDenial } = useAssistantRequests();

  useEffect(() => {
    const controller = start();
    if (!controller) return;
    void history(page, controller.signal).then(value => {
      if (!controller.signal.aborted) { setTurns(value); setHistoryError(""); }
    }, error => {
      if (handleDenial(error, controller)) return;
      setTurns(null);
      setHistoryError("Não foi possível consultar o histórico. Atualize a consulta para tentar novamente.");
    }).finally(() => release(controller));
    return () => controller.abort();
  }, [page, refresh, start, release, handleDenial]);

  useEffect(() => {
    const focus = () => setRefresh(value => value + 1);
    window.addEventListener("focus", focus);
    return () => window.removeEventListener("focus", focus);
  }, []);

  useEffect(() => {
    if (!id || !requestIdPattern.test(id) || (writing.current && pending.current?.solicitacao_id === id)) return;
    const controller = start();
    if (!controller) return;
    void read(id, controller.signal).then(value => {
      if (controller.signal.aborted) return;
      setReadError("");
      setLatest(value);
      if (pending.current?.solicitacao_id === id) {
        pending.current = null;
        setSendError("");
        setText("");
      }
    }, error => {
      if (handleDenial(error, controller)) return;
      setLatest(null);
      if (error instanceof ApiError && error.status === 404 && pending.current?.solicitacao_id === id) {
        setReadError("Ainda não há resposta salva. Você pode reenviar o mesmo pedido.");
      } else setReadError(failure(error));
    }).finally(() => release(controller));
    return () => controller.abort();
  }, [id, refresh, start, release, handleDenial]);

  useEffect(() => {
    if (!adapting) return;
    const controller = start();
    if (!controller) return;
    void context(controller.signal).then(value => {
      if (controller.signal.aborted) return;
      const current = adaptRef.current;
      if (current?.versao_base_id !== value.versao_base_id || current?.onboarding_id !== value.onboarding_id) {
        setConfirmed(false);
        setDay(1);
        pending.current = null;
      }
      adaptRef.current = value;
      setAdaptation({ revision: refresh, value });
    }, error => {
      if (handleDenial(error, controller)) return;
      setConfirmed(false);
      setAdaptation({ revision: refresh, error: error instanceof ApiError && error.status === 409
        ? "Para adaptar um dia, você precisa de uma ficha vigente e dos dados de treino concluídos."
        : "Não foi possível conferir a ficha e os dados de treino. Atualize a consulta para tentar novamente." });
    }).finally(() => release(controller));
    return () => controller.abort();
  }, [adapting, refresh, start, release, handleDenial]);

  const currentAdaptation = adaptation?.revision === refresh ? adaptation : null;
  const adapt = currentAdaptation && "value" in currentAdaptation ? currentAdaptation.value : null;

  async function send(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (writing.current || !text.trim() || (adapting && (!adapt || !confirmed))) return;
    const controller = start();
    if (!controller) return;
    const body = pending.current ?? {
      solicitacao_id: crypto.randomUUID(), mensagem: text.trim(), finalidade: mode,
      ...(adapt && { versao_base_id: adapt.versao_base_id, onboarding_id: adapt.onboarding_id, dia_alvo: day }),
    };
    pending.current = body;
    writing.current = true;
    setBusy(true);
    setSendError("");
    setReadError("");
    comparing.current?.abort();
    setDiff(null);
    setCompareError("");
    setParams(adapting ? { modo: "adaptacao", solicitacao: body.solicitacao_id } : { solicitacao: body.solicitacao_id });
    try {
      const value = await ask(body, csrf, controller.signal);
      if (controller.signal.aborted) return;
      setLatest(value);
      setText("");
      setPage(1);
      pending.current = null;
      setRefresh(value => value + 1);
    } catch (error) {
      if (handleDenial(error, controller)) return;
      if (error instanceof ApiError && [409, 422, 429].includes(error.status)) pending.current = null;
      if (adapting && error instanceof ApiError && error.status === 409) {
        setConfirmed(false);
        setRefresh(value => value + 1);
      }
      setSendError(failure(error));
    } finally {
      release(controller);
      writing.current = false;
      if (!controller.signal.aborted) setBusy(false);
    }
  }

  async function compare(turn: Turn) {
    comparing.current?.abort();
    const controller = start();
    if (!controller) return;
    comparing.current = controller;
    setDiff(null);
    setCompareError("");
    try {
      const value = await differences(turn.solicitacao_id, controller.signal);
      if (!controller.signal.aborted) setDiff(value);
    } catch (error) {
      if (!handleDenial(error, controller)) setCompareError(failure(error));
    } finally {
      release(controller);
      if (comparing.current === controller) comparing.current = null;
    }
  }

  function changePage(next: number) {
    setTurns(null);
    setPage(next);
  }

  if (denied) return <StatusMessage state="error" title="Seu acesso ao chat não está disponível.">
    Volte a entrar para consultar sua conversa.
  </StatusMessage>;
  const selected = latest && latest.solicitacao_id === id ? latest : turns?.find(turn => turn.solicitacao_id === id);
  const archived = turns?.filter(turn => turn.solicitacao_id !== selected?.solicitacao_id) ?? [];
  return <section className="training-chat">
    <h3>{adapting ? "Adapte um dia da sua ficha" : "Tire uma dúvida sobre exercícios"}</h3>
    <p>{adapting ? "Escolha um dia da ficha vigente. Os outros dias permanecem iguais." :
      "O assistente responde com base em fontes sobre atividade física. A dúvida não altera sua ficha."}</p>
    <form className="assistant-panel" onSubmit={event => void send(event)}>
      <fieldset disabled={busy}>
        {adapting && <>
          <p><Link to="/area/cliente/onboarding">Conferir meus dados de treino</Link></p>
          {currentAdaptation && "error" in currentAdaptation
            ? <StatusMessage state="conflict" title={currentAdaptation.error}><Link to="/area/cliente/treino-ia">Gerar ficha</Link></StatusMessage>
            : !adapt && <p role="status">Conferindo sua ficha e seus dados de treino…</p>}
          {adapt && <div className="assistant-context">
            <p>Ficha vigente · Dados de treino confirmados, versão {adapt.snapshot_numero}</p>
            <details><summary>Identificação da ficha-base</summary><code>{adapt.versao_base_id}</code></details>
            <FormField label="Dia que desejo adaptar">{field => <select {...field} value={day} onChange={event => {
              setDay(Number(event.target.value));
              pending.current = null;
            }}>{adapt.dias.map((title, index) => <option key={index} value={index + 1}>{title}</option>)}</select>}</FormField>
            <label className="assistant-checkbox"><input type="checkbox" checked={confirmed} onChange={event => {
              setConfirmed(event.target.checked);
              pending.current = null;
            }} />Conferi e confirmei no onboarding os dados relevantes para esta adaptação</label>
          </div>}
        </>}
        <FormField label="Mensagem" required>{field =>
          <textarea {...field} rows={3} maxLength={1000} value={text} onChange={event => {
            setText(event.target.value);
            pending.current = null;
          }} />
        }</FormField>
        <Button type="submit" pending={busy} pendingLabel="Enviando…"
          disabled={!text.trim() || (adapting && (!adapt || !confirmed))}>
          {adapting ? "Solicitar adaptação" : "Enviar dúvida"}
        </Button>
      </fieldset>
    </form>
    {sendError && <StatusMessage state="error" title={sendError} />}
    {readError && <StatusMessage state="error" title={readError} />}
    {id && !requestIdPattern.test(id) && <StatusMessage state="error" title="O identificador da conversa é inválido." />}
    {selected && <section aria-label="Solicitação selecionada"><ChatTurn turn={selected} onCompare={compare} announce /></section>}
    {compareError && <StatusMessage state="error" title={compareError} />}
    {diff && <Comparison diff={diff} />}
    <section aria-labelledby="assistant-history">
      <div className="assistant-row">
        <h4 id="assistant-history">Histórico do assistente</h4>
        <Button variant="secondary" disabled={busy} onClick={() => {
          setReadError("");
          setRefresh(value => value + 1);
        }}>Consultar estado e histórico</Button>
      </div>
      {historyError ? <StatusMessage state="error" title={historyError} />
        : turns === null ? <p role="status">Carregando seu histórico…</p>
        : archived.length === 0 ? <p>{selected ? "Nenhuma outra mensagem nesta página." : "Nenhuma mensagem nesta página."}</p>
        : <ol className="chat-history" aria-labelledby="assistant-history">{archived.map(turn =>
          <li key={turn.solicitacao_id}><ChatTurn turn={turn} onCompare={compare} /></li>
        )}</ol>}
      {(page > 1 || (turns?.length ?? 0) >= 20) && <nav className="assistant-row" aria-label="Páginas da conversa">
        <Button variant="secondary" disabled={page === 1 || busy} onClick={() => changePage(page - 1)}>Mais recentes</Button>
        <span>Página {page}</span>
        <Button variant="secondary" disabled={(turns?.length ?? 0) < 20 || busy} onClick={() => changePage(page + 1)}>Mais antigas</Button>
      </nav>}
    </section>
  </section>;
}
