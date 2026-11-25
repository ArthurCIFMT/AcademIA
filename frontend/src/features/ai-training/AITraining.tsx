import { useEffect, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { healthFeedback, onboardingForReason } from "../onboarding/triageFeedback";
import { cancel, followup, generate, type Followup, type Receipt } from "./api";
import { GenerationDetails } from "./GenerationDetails";
import { requestIdPattern } from "./requestId";
import { useAssistantRequests } from "./useAssistantRequests";
import "./ai-training.css";

const labels: Record<string, string> = {
  EM_EXECUCAO: "Geração em andamento", PUBLICADA: "Ficha publicada", AGUARDANDO: "Aguardando execução",
  BLOQUEADA: "Geração bloqueada pela triagem", DADOS_INSUFICIENTES: "É necessário completar ou conferir o onboarding",
  ABSTENCAO: "Não há suporte suficiente para gerar esta ficha", CONFLITO: "As fontes apresentam conflito",
  FALHA: "O serviço não conseguiu concluir a geração", JSON_INVALIDO: "A resposta da IA não pôde ser utilizada",
  SCHEMA_INVALIDO: "A proposta não passou pela validação", TIMEOUT: "O tempo da geração foi excedido",
  CANCELADA: "Solicitação cancelada", LIMITE_EXCEDIDO: "O contexto excedeu os limites da geração",
  INTERROMPIDA: "O contexto mudou ou a execução foi interrompida",
};
const reasons = new Map([
  ["QUOTA_EXCEDIDA", "O limite de uso da IA gratuita foi atingido. Aguarde antes de preparar outra solicitação; atualizar a página não renova a quota."],
  ["PROVEDOR_INDISPONIVEL", "A IA está indisponível no momento. Tente mais tarde ou fale com seu instrutor sobre uma ficha manual."],
  ["RAG_INDISPONIVEL", "A consulta às fontes está indisponível no momento. Tente mais tarde."],
  ["REQUISICAO_PROVEDOR_RECUSADA", "O provedor recusou esta solicitação. O erro foi registrado para análise."],
  ["ESCOPO_ETARIO", "A geração automática está disponível a partir dos 18 anos, conforme a idade registrada no onboarding. O instrutor pode montar a ficha manualmente."],
  ["ALERTA_GRAVE_DECLARADO", "As respostas do onboarding indicam um alerta previsto na triagem. Confira se os dados estão corretos e fale com seu instrutor sobre uma ficha manual."],
  ["ALERTA_GRAVE_TEXTO", "A análise do texto do onboarding sinalizou um possível alerta. Isso não é um diagnóstico. Confira se as informações estão corretas e fale com seu instrutor sobre uma ficha manual."],
  ["SUPORTE_SAUDE_INSUFICIENTE", "A base do assistente não confirmou evidência suficiente para gerar uma ficha considerando as informações do seu onboarding. O instrutor pode montar a ficha manualmente."],
  ["DADO_DESCONHECIDO", "A triagem precisa de informações ainda marcadas como desconhecidas no onboarding."],
  ["LACUNA_OU_CONTRADICAO", "A triagem sinalizou informações incompletas ou contraditórias. Confira as respostas do onboarding."],
  ["SEM_EXERCICIOS_VIAVEIS", "O catálogo da academia não tem exercícios disponíveis para esta geração."],
]);
const reviews = { PENDENTE: "Pendente", ACEITO: "Aceito", REJEITADO: "Rejeitado" };
const when = (value: string) => new Date(value).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
function errorMessage(error: unknown) {
  if (error instanceof ApiError) {
    if (error.status === 404) return "A solicitação não foi encontrada nesta conta. Consulte novamente antes de criar outro pedido.";
    if (error.status === 409) return "A mesma solicitação possui outro contexto. Consulte o resultado salvo.";
    if (error.status === 429) return "O limite de solicitações foi atingido. Aguarde antes de uma nova tentativa.";
  }
  return "Não foi possível confirmar o resultado. Consulte o estado salvo; a geração não será repetida automaticamente.";
}

export function AITrainingPage({ csrf }: { csrf: string }) {
  const [params, setParams] = useSearchParams();
  const id = params.get("solicitacao");
  const valid = id === null || requestIdPattern.test(id);
  const [data, setData] = useState<{ id: string; value: Followup } | null>(null);
  const [receipt, setReceipt] = useState<{ id: string; value: Receipt } | null>(null);
  const [readError, setReadError] = useState<{ id: string; message: string } | null>(null);
  const [mutationError, setMutationError] = useState<{ id: string; message: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [cancelling, setCancelling] = useState(false);
  const [revision, setRevision] = useState(0);
  const posting = useRef(false);
  const stopping = useRef(false);
  const active = useRef(id);
  useEffect(() => { active.current = id; }, [id]);
  const { denied, start, release, handleDenial } = useAssistantRequests();
  useEffect(() => {
    if (!id || !valid) return;
    const controller = start();
    if (!controller) return;
    let timer: ReturnType<typeof setTimeout> | undefined;
    let reading = false;
    const read = async () => {
      if (reading || controller.signal.aborted) return;
      reading = true;
      clearTimeout(timer);
      try {
        const value = await followup(id, controller.signal);
        if (controller.signal.aborted) return;
        setData({ id, value });
        setReadError(null);
        if (value.execucao.estado === "EM_EXECUCAO") timer = setTimeout(() => void read(), 2000);
      } catch (failure) {
        if (handleDenial(failure, controller)) return;
        setData(null);
        if (posting.current && failure instanceof ApiError && failure.status === 404)
          timer = setTimeout(() => void read(), 2000);
        else setReadError({ id, message: errorMessage(failure) });
      } finally {
        reading = false;
      }
    };
    void read();
    const focus = () => void read();
    window.addEventListener("focus", focus);
    return () => { controller.abort(); release(controller); clearTimeout(timer); window.removeEventListener("focus", focus); };
  }, [id, valid, revision, start, release, handleDenial]);

  async function submit() {
    if (posting.current || id !== null) return;
    const controller = start();
    if (!controller) return;
    const requestId = crypto.randomUUID();
    active.current = requestId;
    posting.current = true;
    setBusy(true);
    setReadError(null);
    setMutationError(null);
    setData(null);
    setReceipt(null);
    setParams({ solicitacao: requestId });
    try {
      const value = await generate(requestId, csrf, controller.signal);
      if (!controller.signal.aborted && active.current === requestId) {
        setReceipt({ id: requestId, value }); setRevision((v) => v + 1);
      }
    } catch (failure) {
      if (!handleDenial(failure, controller) && active.current === requestId)
        setMutationError({ id: requestId, message: errorMessage(failure) });
    } finally { release(controller); posting.current = false; if (!controller.signal.aborted) setBusy(false); }
  }
  async function stop() {
    if (!id || !valid || stopping.current) return;
    const controller = start();
    if (!controller) return;
    stopping.current = true;
    setCancelling(true);
    setMutationError(null);
    try {
      const value = await cancel(id, csrf, controller.signal);
      if (!controller.signal.aborted && active.current === id) { setReceipt({ id, value }); setRevision((v) => v + 1); }
    } catch (failure) {
      if (!handleDenial(failure, controller) && active.current === id) setMutationError({ id, message: errorMessage(failure) });
    } finally { release(controller); stopping.current = false; if (!controller.signal.aborted) setCancelling(false); }
  }

  function prepareNext() {
    setParams({});
    setData(null);
    setReceipt(null);
    setReadError(null);
    setMutationError(null);
  }
  if (denied) return <StatusMessage state="error" title="Seu acesso a esta solicitação não está disponível.">
    Volte a entrar para consultar suas fichas.
  </StatusMessage>;
  const current = id && data?.id === id ? data.value : null;
  const result = current?.execucao ?? (receipt?.id === id ? receipt.value : null);
  const error = (mutationError?.id === id ? mutationError.message : "") || (readError?.id === id ? readError.message : "");
  const reason = result ? healthFeedback(result.motivo) ?? reasons.get(result.motivo) : undefined;
  const generation = current?.geracao;
  const training = generation?.contexto.treino;
  const expired = training?.ficha.estado_publicacao === "CONTEUDO_EXPIRADO";
  const running = result?.estado === "EM_EXECUCAO" || result?.estado === "AGUARDANDO";
  const published = result?.estado === "PUBLICADA";
  return <section className="ai-training">
    <h3>Gere uma ficha de treino</h3>
    <p>A ficha usa seus dados de treino, os exercícios disponíveis e referências de atividade física. Seu instrutor pode avaliá-la após a publicação.</p>
    <div className="assistant-row">
      <Link to={onboardingForReason(result?.motivo)}>Conferir meus dados de treino</Link>
      <Link to="/area/cliente/treinos">Meus treinos e histórico</Link>
    </div>
    <div className="assistant-panel">
      {id === null && <Button disabled={busy || cancelling} onClick={() => void submit()}>Solicitar geração</Button>}
      {!valid && <>
        <StatusMessage state="error" title="O identificador desta solicitação é inválido." />
        <Button variant="secondary" onClick={prepareNext}>Voltar à geração</Button>
      </>}
      {id && valid && <>
        {result && <StatusMessage state={published ? "success" : running ? "loading" : "conflict"}
          title={labels[result.estado] ?? "Consulte o estado da solicitação"}>{reason}</StatusMessage>}
        {!result && !error && <StatusMessage state="loading"
          title={busy ? "Solicitando geração…" : "Consultando solicitação…"} />}
        {error && <StatusMessage state="error" title={error} />}
        {result && !published && !running &&
          <p>Não foi publicada uma nova ficha por esta solicitação. Seus treinos já existentes continuam no histórico.</p>}
        <div className="assistant-row ai-receipt-actions">
          <Button variant="secondary" onClick={() => {
            setReadError(null);
            setMutationError(null);
            setRevision(v => v + 1);
          }}>Consultar estado salvo</Button>
          {((busy && !result) || running) && <Button variant="danger" pending={cancelling}
            pendingLabel="Cancelando…" onClick={() => void stop()}>Cancelar solicitação</Button>}
          {!busy && !cancelling && result && !running &&
            <Button variant="secondary" onClick={prepareNext}>Preparar nova solicitação</Button>}
          {!busy && !cancelling && !result && error &&
            <Button variant="secondary" onClick={prepareNext}>Voltar à geração</Button>}
        </div>
        <details><summary>Identificação da solicitação</summary><code>{id}</code></details>
      </>}
    </div>
    {training && <article className="assistant-panel" aria-label="Ficha gerada">
      <h4>Versão {training.ficha.numero} · {training.ficha.vigente ? "Vigente" : "Histórica"}</h4>
      <p>Parecer do instrutor · {reviews[training.parecer.estado]}</p>
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
    {generation && <GenerationDetails data={generation} technical={false} />}
  </section>;
}
