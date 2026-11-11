import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, test, vi } from "vitest";
import { App } from "../../App";
import { fileBase64, type Version } from "./api";

const route="/area/administracao/corpus";
const row: Version={ id:"versao",documento_id:"documento",catalogo_id:"LIVRO-001",ambiente:"LITERATURA",
  numero:1,sha256:"a".repeat(64),formato:"PDF",tamanho_bytes:30,estado:"PENDENTE",revisao:1,
  metadados:{titulo:"Literatura sintética",origem_url:"https://example.test/fonte",licenca:"Fixture",
    idioma:"pt-BR",autores:[],ano:null,paginas_declaradas:1,secao:null,finalidades:["DUVIDAS"],limites:"Somente teste"},
  aprovado_por:null,aprovado_em:null,revogado_por:null,revogado_em:null,motivo_revogacao:null };
const page=(entry: Version=row)=>Response.json({itens:[entry],pagina:1,limite:20,total:1});
const session=(role="ADMINISTRADOR")=>Response.json({user_id:"admin",roles:[role],csrf_token:"csrf",
  expires_at:new Date(Date.now()+60000).toISOString()});
function mount(...responses:Array<Response|Error>){
  const request=vi.fn<(url:string,options:RequestInit)=>Promise<Response>>();
  responses.forEach(r=>r instanceof Error?request.mockRejectedValueOnce(r):request.mockResolvedValueOnce(r));
  vi.stubGlobal("fetch",request);
  render(<MemoryRouter initialEntries={[route]}><App/></MemoryRouter>);
  return request;
}
const click=(name:string)=>fireEvent.click(screen.getByRole("button",{name}));
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
test("aprova e revoga a versão com revisão e motivo",async()=>{
  const approved:Version={...row,estado:"APROVADO",revisao:2,aprovado_por:"admin",aprovado_em:"2026-11-11T10:00:00Z"};
  const revoked:Version={...approved,estado:"REVOGADO",revisao:3,revogado_por:"admin",revogado_em:"2026-11-11T11:00:00Z",motivo_revogacao:"Fonte substituída"};
  const request=mount(session(),page(),Response.json(row),Response.json(approved),page(approved),
    Response.json(revoked),page(revoked));
  await screen.findByText(/Literatura sintética · LIVRO-001/);
  click("Detalhes LIVRO-001 versão 1");
  await screen.findByText("Estado · Quarentena");
  click("Aprovar esta versão");
  await screen.findByText("Estado · Aprovado");
  expect(screen.getByRole<HTMLButtonElement>("button",{name:"Revogar esta versão"}).disabled).toBe(true);
  fireEvent.change(screen.getByLabelText("Motivo da revogação"),{target:{value:"Fonte substituída"}});
  click("Revogar esta versão");
  await screen.findByText("Estado · Revogado");
  expect(screen.queryByRole("button",{name:"Aprovar esta versão"})).toBeNull();
  const writes=request.mock.calls.filter(([,opts])=>opts.method==="POST");
  expect(writes.map(([url])=>url)).toEqual(["/api/v1/corpus/versao/decisao","/api/v1/corpus/versao/decisao"]);
  expect(JSON.parse(String(writes[1][1].body))).toEqual({revisao:2,estado:"REVOGADO",motivo:"Fonte substituída"});
  expect(writes[1][1].headers).toMatchObject({"X-CSRF-Token":"csrf"});
});
test("importação explicita distingue seleção aprovada e quarentena",async()=>{
  mount(session(),Response.json({itens:[],total:0,pagina:1,limite:20}),
    Response.json({documentos:18,versoes_novas:18,aprovadas:7,pendentes:11,revogadas:0}),page());
  await screen.findByText("Nenhum documento cadastrado.");
  click("Importar acervo inicial versionado");
  await screen.findByText(/18 documentos, 18 versões novas, 7 aprovadas, 11 em quarentena/);
});
test("falha de decisão preserva motivo; perda de acesso limpa o acervo",async()=>{
  const approved:Version={...row,estado:"APROVADO",revisao:2};
  mount(session(),page(approved),Response.json(approved),new Error("offline"),new Response(null,{status:403}));
  await screen.findByText(/Literatura sintética · LIVRO-001/);
  click("Detalhes LIVRO-001 versão 1");
  await screen.findByText("Estado · Aprovado");
  fireEvent.change(screen.getByLabelText("Motivo da revogação"),{target:{value:"Motivo sintético"}});
  click("Revogar esta versão");
  await screen.findByText(/Não foi possível confirmar/);
  expect(screen.getByLabelText<HTMLTextAreaElement>("Motivo da revogação").value).toBe("Motivo sintético");
  click("Revogar esta versão");
  await screen.findByRole("alert");
  expect(screen.queryByText("Estado · Aprovado")).toBeNull();
});
test("instrutor sem permissão de curadoria não acessa manutenção",async()=>{
  const request=mount(session("INSTRUTOR"));
  await screen.findByRole("heading",{name:"Acesso não permitido"});
  expect(request).toHaveBeenCalledTimes(1);
});
test("arquivo é serializado em JSON base64 sem alterar conteúdo",async()=>{
  expect(await fileBase64(new File(["Texto sintético"],"teste.txt",{type:"text/plain"})))
    .toBe(btoa(unescape(encodeURIComponent("Texto sintético"))));
});
