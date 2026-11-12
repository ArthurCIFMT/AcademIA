import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { TrainingChatPage } from "./TrainingChat";
import type { Turn } from "./api";
const id="11111111-1111-4111-8111-111111111111";
const turn:Turn={solicitacao_id:id,pergunta:"Dúvida sintética",criada_em:"2026-11-11T12:00:00Z",finalidade:"DUVIDA",estado:"RESPOSTA_PRONTA",motivo:"OK",resposta:{idioma:"pt-BR",tipo:"INFORMACAO",texto:"<script>alert(1)</script> [clique](javascript:alert(1))",evidencias_ids:["fragment"]},fontes:[{fragmento_id:"fragment",documento_versao_id:"doc",titulo:"Fonte sintética",origem_url:"https://example.test/fonte",idioma:"pt-BR",pagina:3,linha_inicio:null,linha_fim:null,secao:null}],versao_publicada_id:null};
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});
function mount(handler:(url:string,options:RequestInit)=>Promise<Response>, query="") {
 const fetcher=vi.fn(handler);vi.stubGlobal("fetch",fetcher);vi.spyOn(crypto,"randomUUID").mockReturnValue(id);
 render(<MemoryRouter initialEntries={["/area/cliente/assistente"+query]}><TrainingChatPage csrf="csrf-test"/></MemoryRouter>);
 return fetcher;
}
const click=(name:string)=>fireEvent.click(screen.getByRole("button",{name}));
test("dúvida sem ficha envia somente mensagem e texto retornado é inerte",async()=>{
 let sent=false;
 const fetcher=mount(async(url,options)=>{
  if(options.method==="POST"){sent=true;return Response.json(turn);}
  if(url.includes("?page="))return Response.json(sent?[turn]:[]);
  return Response.json(turn);
 });
 fireEvent.change(screen.getByLabelText("Mensagem"),{target:{value:"Dúvida sintética"}});
 click("Enviar dúvida");
 await screen.findByText(turn.resposta!.texto);
 expect(document.querySelector("script")).toBeNull();
 expect(screen.queryByRole("link",{name:"clique"})).toBeNull();
 expect(screen.getByRole("link",{name:"Fonte sintética"}).getAttribute("rel")).toBe("noopener noreferrer");
 const writes=fetcher.mock.calls.filter(([,o])=>o.method==="POST");
 expect(writes).toHaveLength(1);
 expect(JSON.parse(String(writes[0][1].body))).toEqual({solicitacao_id:id,mensagem:"Dúvida sintética",finalidade:"DUVIDA"});
 expect(writes[0][1].headers).toMatchObject({"X-CSRF-Token":"csrf-test"});
 expect(fetcher.mock.calls.some(([url])=>url.includes("/contexto/"))).toBe(false);
});
test("erro de transporte permite repetição explícita do mesmo ID sem loop",async()=>{
 let posts=0;
 const fetcher=mount(async(url,options)=>{
  if(options.method==="POST"){posts++;if(posts===1)throw Error("offline");return Response.json(turn);}
  return Response.json(url.includes("?page=")?[]:turn);
 });
 fireEvent.change(screen.getByLabelText("Mensagem"),{target:{value:"Dúvida sintética"}});
 click("Enviar dúvida");
 await screen.findByText(/Não foi possível confirmar a resposta/);
 expect(posts).toBe(1);
 click("Enviar dúvida");
 await screen.findByText(turn.resposta!.texto);
 const writes=fetcher.mock.calls.filter(([,o])=>o.method==="POST");
 expect(writes).toHaveLength(2);expect(writes[0][1].body).toBe(writes[1][1].body);
});
test("adaptação exige contexto e confirmação do onboarding, com alvo explícito",async()=>{
 let done=false;
 const adapted={...turn,finalidade:"ADAPTACAO",estado:"PUBLICADA",resposta:null,versao_publicada_id:"new-version"};
 const fetcher=mount(async(url,options)=>{
  if(url.endsWith("/contexto/adaptacao"))return Response.json({versao_base_id:"base",onboarding_id:"snapshot",snapshot_numero:2,dias:["Dia A","Dia B"]});
  if(options.method==="POST"){done=true;return Response.json(adapted);}
  return Response.json(url.includes("?page=")?done?[adapted]:[]:adapted);
 });
 fireEvent.change(screen.getByLabelText("Objetivo"),{target:{value:"ADAPTACAO"}});
 await screen.findByText(/Onboarding confirmado disponível/);
 fireEvent.change(screen.getByLabelText("Mensagem"),{target:{value:"Adaptar somente o dia A"}});
 expect(screen.getByRole<HTMLButtonElement>("button",{name:"Solicitar adaptação"}).disabled).toBe(true);
 fireEvent.click(screen.getByRole("checkbox"));
 click("Solicitar adaptação");
 await screen.findByText("Nova versão publicada com parecer pendente");
 expect(screen.getByRole("link",{name:"Consultar versão e parecer"})).toBeTruthy();
 const body=JSON.parse(String(fetcher.mock.calls.find(([,o])=>o.method==="POST")![1].body));
 expect(body).toMatchObject({finalidade:"ADAPTACAO",onboarding_id:"snapshot",versao_base_id:"base",dia_alvo:1});
});
test("perda de autorização limpa histórico e fonte, sem chamar LLM pelo navegador",async()=>{
 let denied=false;
 mount(async()=>denied?new Response(null,{status:403}):Response.json([turn]));
 await screen.findByText(turn.resposta!.texto);
 denied=true;click("Consultar estado e histórico");
 await screen.findByText(/Seu acesso ao chat/);
 expect(screen.queryByText(turn.resposta!.texto)).toBeNull();
 expect(screen.queryByRole("link",{name:"Fonte sintética"})).toBeNull();
});
test("429 não dispara repetição automática e fonte javascript não vira link",async()=>{
 const unsafe={...turn,fontes:[{...turn.fontes[0],origem_url:"javascript:alert(1)"}]};
 const fetcher=mount(async(url,options)=>options.method==="POST"?new Response(null,{status:429}):Response.json(url.includes("?page=")?[unsafe]:unsafe));
 await screen.findByText(turn.resposta!.texto);
 expect(screen.queryByRole("link",{name:"Fonte sintética"})).toBeNull();
 fireEvent.change(screen.getByLabelText("Mensagem"),{target:{value:"Nova dúvida"}});
 click("Enviar dúvida");
 await screen.findByText(/Limite de seis solicitações/);
 await waitFor(()=>expect(fetcher.mock.calls.filter(([,o])=>o.method==="POST")).toHaveLength(1));
});

test("não consulta UUID ainda em criação e retoma somente após o envio",async()=>{
 let finish!:(value:Response)=>void;
 const pending=new Promise<Response>(resolve=>{finish=resolve;});
 let done=false;
 const fetcher=mount(async(url,options)=>{
  if(options.method==="POST")return pending;
  if(url.includes("?page="))return Response.json(done?[turn]:[]);
  return done?Response.json(turn):new Response(null,{status:404});
 });
 fireEvent.change(screen.getByLabelText("Mensagem"),{target:{value:"Dúvida sintética"}});
 click("Enviar dúvida");
 await screen.findByRole("button",{name:"Enviando…"});
 expect(fetcher.mock.calls.some(([url,o])=>o.method!=="POST"&&url.endsWith("/"+id))).toBe(false);
 done=true;finish(Response.json(turn));
 await screen.findByText(turn.resposta!.texto);
 expect(screen.queryByRole("alert")).toBeNull();
 expect(fetcher.mock.calls.filter(([,o])=>o.method==="POST")).toHaveLength(1);
});
