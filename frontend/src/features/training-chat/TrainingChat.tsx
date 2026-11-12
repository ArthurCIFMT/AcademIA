import { useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { ApiError } from "../../lib/api/auth";
import { ask, context, differences, history, read, type Ask, type AdaptContext, type Diff, type Turn } from "./api";
import "./training-chat.css";

const states:Record<string,string>={PUBLICADA:"Nova versão publicada com parecer pendente",RESPOSTA_PRONTA:"Resposta disponível",ABSTENCAO:"Não há evidência suficiente para responder ou adaptar",CONFLITO:"As fontes apresentam conflito",BLOQUEADA:"Adaptação bloqueada pela triagem",DADOS_INSUFICIENTES:"Confira e complete o onboarding",FALHA:"O serviço não conseguiu concluir a resposta",JSON_INVALIDO:"A resposta da IA não pôde ser utilizada",SCHEMA_INVALIDO:"A proposta não passou pela validação",TIMEOUT:"O tempo da execução foi excedido",LIMITE_EXCEDIDO:"O contexto excedeu o limite",INTERROMPIDA:"O contexto foi alterado",CANCELADA:"Solicitação cancelada",EM_EXECUCAO:"Solicitação em andamento",AGUARDANDO:"Aguardando execução"};
function failure(error:unknown) {
 if(error instanceof ApiError) {
  if([401,403].includes(error.status))return "Seu acesso ao chat não está disponível.";
  if(error.status===429)return "Limite de seis solicitações por minuto atingido. Aguarde antes de enviar novamente.";
  if(error.status===409)return "O contexto mudou ou ainda não há ficha/onboarding concluído. Confira seus dados e consulte o estado salvo.";
  if(error.status===422)return "Confira a mensagem e o contexto da adaptação.";
  if(error.status===404)return "A solicitação não está disponível nesta conta.";
 }
 return "Não foi possível confirmar a resposta. Consulte o estado salvo antes de repetir o mesmo pedido.";
}
function safeLink(value:string) {try {const url=new URL(value);return ["https:","http:"].includes(url.protocol)?url.href:undefined;}catch{return undefined;}}
const uuid=/^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$/i;

export function TrainingChatPage({csrf}:{csrf:string}) {
 const [params,setParams]=useSearchParams();
 const id=params.get("solicitacao");
 const [turns,setTurns]=useState<Turn[]>([]);
 const [latest,setLatest]=useState<Turn|null>(null);
 const [text,setText]=useState("");
 const [mode,setMode]=useState<"DUVIDA"|"ADAPTACAO">("DUVIDA");
 const [adapt,setAdapt]=useState<AdaptContext|null>(null);
 const [confirmed,setConfirmed]=useState(false);
 const [day,setDay]=useState(1);
 const [busy,setBusy]=useState(false);
 const [error,setError]=useState("");
 const [sendError,setSendError]=useState("");
 const [page,setPage]=useState(1);
 const [refresh,setRefresh]=useState(0);
 const [diff,setDiff]=useState<Diff|null>(null);
 const pending=useRef<Ask|null>(null), writing=useRef(false);
 const adaptRef=useRef<AdaptContext|null>(null);
 const controllers=useRef(new Set<AbortController>());
 useEffect(()=>{const set=controllers.current;return()=>{for(const c of set)c.abort();};},[]);
 useEffect(()=>{
  const c=new AbortController();
  void history(page,c.signal).then(v=>{if(!c.signal.aborted){setTurns(v);}},e=>{if(!c.signal.aborted){setTurns([]);setLatest(null);setDiff(null);setError(failure(e));}});
  const focus=()=>setRefresh(v=>v+1);
  window.addEventListener("focus",focus);
  return()=>{c.abort();window.removeEventListener("focus",focus);};
 },[page,refresh]);
 useEffect(()=>{
  if(!id || !uuid.test(id) || (writing.current && pending.current?.solicitacao_id===id))return;
  const c=new AbortController();
  void read(id,c.signal).then(v=>{if(!c.signal.aborted)setLatest(v);},e=>{if(!c.signal.aborted){setLatest(null);setError(failure(e));}});
  return()=>c.abort();
 },[id,refresh]);
 useEffect(()=>{
  if(mode!=="ADAPTACAO")return;
  const c=new AbortController();
  void context(c.signal).then(v=>{if(!c.signal.aborted){if(JSON.stringify(adaptRef.current)!==JSON.stringify(v)){setConfirmed(false);setDay(1);pending.current=null;} adaptRef.current=v;setAdapt(v);}},e=>{if(!c.signal.aborted){setAdapt(null);setConfirmed(false);setError(failure(e));}});
  return()=>c.abort();
 },[mode,refresh]);
 async function send(event:FormEvent) {
  event.preventDefault();
  if(writing.current || !text.trim() || (mode==="ADAPTACAO" && (!adapt||!confirmed)))return;
  const body=pending.current??{solicitacao_id:crypto.randomUUID(),mensagem:text.trim(),finalidade:mode,...(mode==="ADAPTACAO"&&adapt?{versao_base_id:adapt.versao_base_id,onboarding_id:adapt.onboarding_id,dia_alvo:day}:{})};
  pending.current=body;writing.current=true;setBusy(true);setError("");setSendError("");setDiff(null);
  setParams({solicitacao:body.solicitacao_id});
  const c=new AbortController();controllers.current.add(c);
  try {
   const value=await ask(body,csrf,c.signal);
   if(!c.signal.aborted){setError("");setSendError("");setLatest(value);setText("");setPage(1);pending.current=null;setRefresh(v=>v+1);}
  } catch(e) {if(!c.signal.aborted){if(e instanceof ApiError&&[401,403].includes(e.status)){setTurns([]);setLatest(null);setDiff(null);}setSendError(failure(e));}}
  finally{controllers.current.delete(c);writing.current=false;if(!c.signal.aborted)setBusy(false);}
 }
 async function compare(turn:string) {
  const c=new AbortController();controllers.current.add(c);
  try {const value=await differences(turn,c.signal);if(!c.signal.aborted)setDiff(value);}
  catch(e){if(!c.signal.aborted){setDiff(null);setError(failure(e));}}
  finally{controllers.current.delete(c);}
 }
 const shown=latest&&!turns.some(t=>t.solicitacao_id===latest.solicitacao_id)?[...turns,latest]:turns;
 return <section className="training-chat">
  <h3>Assistente de treino</h3>
  <p>Tire dúvidas sobre exercícios e atividade física. O assistente usa fontes e não fornece diagnóstico médico. Conversar não altera sua ficha.</p>
  <p><Link to="/area/cliente/treinos">Meus treinos</Link> · <Link to="/area/cliente/treino-ia">Gerar uma ficha</Link> · <Link to="/area/cliente/onboarding">Conferir meu onboarding</Link></p>
  <button type="button" onClick={()=>{setError("");setSendError("");setRefresh(v=>v+1);}}>Consultar estado e histórico</button>
  {(sendError||error)&&<p role="alert">{sendError||error}</p>}
  <ol aria-label="Histórico do assistente">{shown.map(turn=><li key={turn.solicitacao_id}>
   <p><strong>Você:</strong> {turn.pergunta}</p><p role="status">{states[turn.estado]??"Consulte o estado salvo"}</p>
   {turn.resposta&&<p className="chat-text">{turn.resposta.texto}</p>}
   <ul>{turn.fontes.map(source=><li key={source.fragmento_id}>{safeLink(source.origem_url)?<a href={safeLink(source.origem_url)} target="_blank" rel="noopener noreferrer">{source.titulo}</a>:source.titulo}<span>{source.pagina!==null?" · Página "+source.pagina:source.linha_inicio!==null?" · Linhas "+source.linha_inicio+"–"+source.linha_fim:""}</span></li>)}</ul>
   {turn.versao_publicada_id&&<><p><Link to={"/area/cliente/treino-ia?solicitacao="+encodeURIComponent(turn.solicitacao_id)}>Consultar versão e parecer</Link></p><button type="button" onClick={()=>void compare(turn.solicitacao_id)}>Comparar versões</button></>}
  </li>)}</ol>
  <nav aria-label="Páginas da conversa"><button type="button" disabled={page===1||busy} onClick={()=>{setLatest(null);setPage(v=>v-1);}}>Mais recentes</button><button type="button" disabled={turns.length<20||busy} onClick={()=>{setLatest(null);setPage(v=>v+1);}}>Mais antigas</button></nav>
  {diff&&<section aria-label="Diferenças da adaptação"><h4>Comparação das versões {diff.anterior.ficha.numero} e {diff.atual.ficha.numero}</h4>
   {diff.conteudo_expirado?<p>Parte do conteúdo expirou pela retenção. Os metadados foram preservados.</p>:[["Antes",diff.anterior],["Depois",diff.atual]].map(([label,detail])=>typeof detail!=="string"&&<div key={String(label)}><h5>{String(label)}</h5>{detail.ficha.dias.map((d,i)=><section key={i}><h6>{d.titulo}</h6><ul>{d.itens.map((item,n)=><li key={n}>{String(item.exercicio_snapshot?.nome??"Exercício")} · {item.series} séries · {item.repeticoes} repetições · {item.intervalo_segundos}s</li>)}</ul></section>)}</div>)}
  </section>}
  <form onSubmit={e=>void send(e)}><fieldset disabled={busy}>
   <legend>Nova mensagem</legend>
   <label htmlFor="chat-mode">Objetivo</label><select id="chat-mode" value={mode} onChange={e=>{setMode(e.target.value as typeof mode);setConfirmed(false);pending.current=null;setDiff(null);}}><option value="DUVIDA">Tirar uma dúvida</option><option value="ADAPTACAO">Adaptar um dia da ficha</option></select>
   {mode==="ADAPTACAO"&&<div><p>Registre qualquer novo relato de saúde no onboarding antes de adaptar. O backend fará nova triagem e exigirá evidência pertinente.</p><p>Os outros dias devem permanecer iguais. A versão nova começa com parecer pendente.</p>
    {adapt&&<><p>Onboarding confirmado disponível · Versão {adapt.snapshot_numero}</p><label htmlFor="chat-day">Dia que desejo adaptar</label><select id="chat-day" value={day} onChange={e=>{setDay(Number(e.target.value));pending.current=null;}}>{adapt.dias.map((title,i)=><option key={i} value={i+1}>{title}</option>)}</select><label><input type="checkbox" checked={confirmed} onChange={e=>{setConfirmed(e.target.checked);pending.current=null;}}/>Conferi e confirmei no onboarding os dados relevantes para esta adaptação</label></>}
   </div>}
   <label htmlFor="chat-message">Mensagem</label><textarea id="chat-message" required maxLength={1000} value={text} onChange={e=>{setText(e.target.value);pending.current=null;}}/>
   <button type="submit" disabled={mode==="ADAPTACAO"&&(!adapt||!confirmed)}>{busy?"Enviando…":mode==="DUVIDA"?"Enviar dúvida":"Solicitar adaptação"}</button>
  </fieldset></form>
 </section>;
}
