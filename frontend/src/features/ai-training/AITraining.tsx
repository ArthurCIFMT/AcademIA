import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError } from "../../lib/api/auth";
import { cancel, followup, generate, type Followup, type Receipt } from "./api";
import { GenerationDetails } from "./GenerationDetails";
import "./ai-training.css";

const labels: Record<string, string> = {
  EM_EXECUCAO: "Geração em andamento", PUBLICADA: "Ficha publicada",
  BLOQUEADA: "Geração bloqueada pela triagem", DADOS_INSUFICIENTES: "É necessário completar ou conferir o onboarding",
  ABSTENCAO: "Não há suporte suficiente para gerar esta ficha", CONFLITO: "As fontes apresentam conflito",
  FALHA: "O serviço não conseguiu concluir a geração", JSON_INVALIDO: "A resposta da IA não pôde ser utilizada",
  SCHEMA_INVALIDO: "A proposta não passou pela validação", TIMEOUT: "O tempo da geração foi excedido",
  CANCELADA: "Solicitação cancelada", LIMITE_EXCEDIDO: "O contexto excedeu os limites da geração",
  INTERROMPIDA: "O contexto mudou ou a execução foi interrompida",
};
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const when = (value: string) => new Date(value).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
function errorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if ([401, 403].includes(error.status)) return "Seu acesso a esta solicitação não está disponível.";
    if (error.status === 404) return "A solicitação não foi encontrada nesta conta. Consulte novamente antes de criar outro pedido.";
    if (error.status === 409) return "A mesma solicitação possui outro contexto. Consulte o resultado salvo.";
    if (error.status === 429) return "O limite de solicitações foi atingido. Aguarde antes de uma nova tentativa.";
  }
  return "Não foi possível confirmar o resultado. Consulte o estado salvo; a geração não será repetida automaticamente.";
}

export function AITrainingPage({ csrf }: { csrf: string }) {
  const [params, setParams] = useSearchParams();
  const id = params.get("solicitacao");
  const valid = !id || uuid.test(id);
  const [data, setData] = useState<{ id: string; value: Followup } | null>(null);
  const [receipt, setReceipt] = useState<{ id: string; value: Receipt } | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);
  const [revision, setRevision] = useState(0);
  const posting = useRef(false);
  const active = useRef(id);
  useEffect(() => { active.current = id; }, [id]);
  const controllers = useRef(new Set<AbortController>());
  useEffect(() => { const set = controllers.current; return () => { for (const controller of set) controller.abort(); }; }, []);
  useEffect(() => {
    if (!id || !valid) return;
    const controller = new AbortController();
    const set = controllers.current;
    set.add(controller);
    let timer: ReturnType<typeof setTimeout> | undefined;
    const read = async () => {
      try {
        const value = await followup(id, controller.signal);
        if (controller.signal.aborted) return;
        setData({ id, value }); setError("");
        if (value.execucao.estado === "EM_EXECUCAO") timer = setTimeout(() => void read(), 2000);
      } catch (failure) {
        if (controller.signal.aborted) return;
        setData(null);
        if (posting.current && failure instanceof ApiError && failure.status === 404)
          timer = setTimeout(() => void read(), 2000);
        else setError(errorMessage(failure));
      }
    };
    void read();
    const focus = () => { clearTimeout(timer); void read(); };
    window.addEventListener("focus", focus);
    return () => { controller.abort(); set.delete(controller); clearTimeout(timer); window.removeEventListener("focus", focus); };
  }, [id, valid, revision]);

  async function submit() {
    if (posting.current || id) return;
    const requestId = crypto.randomUUID();
    active.current = requestId;
    posting.current = true; setBusy(true); setError(""); setData(null); setReceipt(null);
    setParams({ solicitacao: requestId });
    const controller = new AbortController();
    controllers.current.add(controller);
    try {
      const value = await generate(requestId, csrf, controller.signal);
      if (!controller.signal.aborted && active.current === requestId) {
        setReceipt({ id: requestId, value }); setRevision((v) => v + 1);
      }
    } catch (failure) {
      if (!controller.signal.aborted && active.current === requestId) setError(errorMessage(failure));
    } finally { controllers.current.delete(controller); posting.current = false; if (!controller.signal.aborted) setBusy(false); }
  }
  async function stop() {
    if (!id) return;
    const controller = new AbortController();
    controllers.current.add(controller);
    try {
      const value = await cancel(id, csrf, controller.signal);
      if (!controller.signal.aborted && active.current === id) { setReceipt({ id, value }); setRevision((v) => v + 1); }
    } catch (failure) { if (!controller.signal.aborted) setError(errorMessage(failure)); }
    finally { controllers.current.delete(controller); }
  }
  const current = id && data?.id === id ? data.value : null;
  const result = current?.execucao ?? (receipt?.id === id ? receipt.value : null);
  const generation = current?.geracao;
  const training = generation?.contexto.treino;
  const expired = training?.ficha.estado_publicacao === "CONTEUDO_EXPIRADO";
  return <section className="ai-training">
    <h3>Gerar treino com IA</h3>
    <p>A geração utiliza seu onboarding, exercícios disponíveis e fontes recuperadas. O instrutor pode avaliar depois da publicação.</p>
    <p><Link to="/area/cliente/onboarding">Conferir meu onboarding</Link> · <Link to="/area/cliente/treinos">Meus treinos e histórico</Link></p>
    {!valid && <p role="alert">O identificador desta solicitação é inválido.</p>}
    {!id && <button type="button" disabled={busy} onClick={() => void submit()}>Solicitar geração</button>}
    {id && valid && <>
      <p>Solicitação · {id}</p>
      <p role="status">{result ? labels[result.estado] ?? "Consulte o estado da solicitação" : busy ? "Solicitando geração…" : "Consultando solicitação…"}</p>
      <button type="button" onClick={() => setRevision((v) => v + 1)}>Consultar estado salvo</button>
      {((busy && !result) || result?.estado === "EM_EXECUCAO") && <button type="button" onClick={() => void stop()}>Cancelar solicitação</button>}
      {!busy && result && result.estado !== "EM_EXECUCAO" && <button type="button" onClick={() => { setParams({}); setData(null); setReceipt(null); setError(""); }}>Preparar nova solicitação</button>}
      {!busy && !result && error && <button type="button" onClick={() => { setParams({}); setError(""); }}>Voltar sem repetir a geração</button>}
    </>}
    {error && <p role="alert">{error}</p>}
    {result && result.estado !== "PUBLICADA" && result.estado !== "EM_EXECUCAO" && <p>Não foi publicada uma nova ficha por esta solicitação. Seus treinos já existentes continuam no histórico.</p>}
    {training && <article aria-label="Ficha gerada">
      <h4>Versão {training.ficha.numero} · {training.ficha.vigente ? "Vigente" : "Histórica"}</h4>
      <p>Parecer {training.parecer.estado} — a consulta não depende do aceite.</p>
      {training.parecer.instrutor_id && <p>Responsável pelo parecer · {training.parecer.instrutor_id}</p>}
      {training.parecer.criado_em && <p>Registrado em {when(training.parecer.criado_em)}</p>}
      {training.parecer.motivo && <p>Motivo · {training.parecer.motivo}</p>}
      {expired ? <p>Conteúdo removido pela retenção. Consulte as versões disponíveis em Meus treinos.</p> : <>
        {training.ficha.explicacao && <p>{training.ficha.explicacao}</p>}
        {training.ficha.dias.map((day, index) => <section key={index}><h5>{day.titulo}</h5><ol>
          {day.itens.map((item, position) => <li key={position}>
            <strong>{String(item.exercicio_snapshot?.nome ?? "Exercício")}</strong>
            <p>{item.series} séries · {item.repeticoes} repetições · Intervalo {item.intervalo_segundos}s</p>
            <p>Carga {item.carga_kg === null ? "não informada" : item.carga_kg + " kg"} · Cadência {item.cadencia ?? "não informada"}</p>
            {item.observacoes && <p>{item.observacoes}</p>}
          </li>)}
        </ol></section>)}
      </>}
    </article>}
    {generation && <GenerationDetails data={generation} />}
  </section>;
}
