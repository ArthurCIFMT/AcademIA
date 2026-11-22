import { Link } from "react-router-dom";

import { Button, StatusMessage } from "../../ui/primitives";
import { SourceList } from "../ai-training/SourceList";
import type { Diff, Turn } from "./api";

const date = new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo" });
const states: Record<string, string> = {
  PUBLICADA: "Nova versão publicada com parecer pendente",
  RESPOSTA_PRONTA: "Resposta disponível",
  ABSTENCAO: "As fontes não sustentaram esta adaptação",
  CONFLITO: "As fontes apresentam conflito",
  BLOQUEADA: "Adaptação bloqueada pela triagem",
  DADOS_INSUFICIENTES: "Confira e complete seus dados de treino",
  FALHA: "O serviço não conseguiu concluir a resposta",
  JSON_INVALIDO: "A resposta da IA não pôde ser utilizada",
  SCHEMA_INVALIDO: "A proposta não passou pela validação",
  TIMEOUT: "O tempo da execução foi excedido",
  LIMITE_EXCEDIDO: "A solicitação ultrapassou o limite de informações",
  INTERROMPIDA: "Solicitação interrompida",
  CANCELADA: "Solicitação cancelada",
  EM_EXECUCAO: "Solicitação em andamento",
  AGUARDANDO: "Aguardando execução",
};
const reasons: Record<string, string> = {
  QUOTA_EXCEDIDA: "O limite de uso da IA gratuita foi atingido. Tente mais tarde.",
  PROVEDOR_INDISPONIVEL: "O assistente está indisponível no momento. Tente mais tarde.",
  RAG_INDISPONIVEL: "A consulta às fontes está indisponível no momento. Tente mais tarde.",
  EVIDENCIA_SUPERADA: "Uma fonte consultada deixou de estar disponível.",
  SUPORTE_SAUDE_INSUFICIENTE: "As fontes não sustentaram uma adaptação para as informações de saúde enviadas.",
  SEM_ALTERACOES: "A proposta manteve os exercícios do dia escolhido. Nenhuma versão foi publicada.",
  CONTEXTO_OU_FONTES_SUPERADOS: "A resposta anterior perdeu seu contexto ou suas fontes.",
};

export function ChatTurn({ turn, onCompare, announce = false }: {
  turn: Turn; onCompare: (turn: Turn) => Promise<void>; announce?: boolean;
}) {
  const question = turn.finalidade === "DUVIDA";
  const status = reasons[turn.motivo] ?? (question && turn.estado === "ABSTENCAO"
    ? "As fontes consultadas não sustentaram uma resposta para esta pergunta."
    : states[turn.estado] ?? "Consulte o estado salvo");
  return <article className="assistant-panel chat-turn">
    <div className="assistant-row chat-meta">
      <strong>{question ? "Dúvida" : "Adaptação"}</strong>
      <time dateTime={turn.criada_em}>{date.format(new Date(turn.criada_em))}</time>
    </div>
    {turn.contexto_anterior && <p className="chat-meta">Conversa anterior à ficha atual.</p>}
    <p className="chat-question"><strong>Você:</strong> {turn.pergunta}</p>
    <div className="chat-answer">
      {announce ? <StatusMessage state={
        turn.estado === "RESPOSTA_PRONTA" || turn.estado === "PUBLICADA" ? "success" :
          turn.estado === "EM_EXECUCAO" || turn.estado === "AGUARDANDO" ? "loading" : "conflict"
      } title={status} /> : <p><strong>{status}</strong></p>}
      {turn.resposta && <p className="chat-text">{turn.resposta.texto}</p>}
      {turn.fontes.length > 0 && <details open>
        <summary>Fontes consultadas</summary>
        <SourceList sources={turn.fontes} />
      </details>}
      {["DADOS_INSUFICIENTES", "BLOQUEADA"].includes(turn.estado) && !question &&
        <p><Link to="/area/cliente/onboarding">Conferir meus dados de treino</Link></p>}
      {turn.versao_publicada_id && <div className="assistant-row">
        <Link to={"/area/cliente/treino-ia?solicitacao=" + encodeURIComponent(turn.solicitacao_id)}>Consultar versão e parecer</Link>
        <Button variant="secondary" onClick={() => void onCompare(turn)}>Comparar versões</Button>
      </div>}
    </div>
  </article>;
}

export function Comparison({ diff }: { diff: Diff }) {
  return <section aria-label="Diferenças da adaptação" className="assistant-panel" tabIndex={0}>
    <h4>Comparação das versões {diff.anterior.ficha.numero} e {diff.atual.ficha.numero}</h4>
    {diff.conteudo_expirado ? <p>Parte do conteúdo expirou pela retenção. Os metadados foram preservados.</p> :
      <div className="assistant-comparison">{([
        ["Antes", diff.anterior], ["Depois", diff.atual],
      ] as const).map(([label, detail]) => <div key={label}>
        <h5>{label}</h5>
        {detail.ficha.dias.map((day, index) => <section key={index}>
          <h6>{day.titulo}</h6>
          <ul>{day.itens.map((item, position) => <li key={position}>
            {String(item.exercicio_snapshot?.nome ?? "Exercício")} · {item.series} séries · {item.repeticoes} repetições · {item.intervalo_segundos}s
          </li>)}</ul>
        </section>)}
      </div>)}</div>}
  </section>;
}
