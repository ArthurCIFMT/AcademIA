import { requestApi } from "../../lib/api/auth";
import type { Source } from "../ai-training/api";
import type { Detail } from "../training-review/api";
export type Turn={solicitacao_id:string;pergunta:string;criada_em:string;finalidade:string;estado:string;motivo:string;resposta:{idioma:"pt-BR";tipo:string;texto:string;evidencias_ids:string[]}|null;fontes:Source[];versao_publicada_id:string|null};
export type Ask={solicitacao_id:string;mensagem:string;finalidade:"DUVIDA"|"ADAPTACAO";versao_base_id?:string;onboarding_id?:string;dia_alvo?:number};
export type AdaptContext={versao_base_id:string;onboarding_id:string;snapshot_numero:number;dias:string[]};
export type Diff={anterior:Detail;atual:Detail;conteudo_expirado:boolean};
export async function history(page:number,signal:AbortSignal):Promise<Turn[]> {return (await requestApi("/v1/ia/chat?page="+page,{signal})).json() as Promise<Turn[]>;}
export async function ask(body:Ask,csrf:string,signal:AbortSignal):Promise<Turn>{return (await requestApi("/v1/ia/chat",{method:"POST",signal,headers:{"Content-Type":"application/json","X-CSRF-Token":csrf},body:JSON.stringify(body)})).json() as Promise<Turn>;}
export async function read(id:string,signal:AbortSignal):Promise<Turn>{return (await requestApi("/v1/ia/chat/"+encodeURIComponent(id),{signal})).json() as Promise<Turn>;}
export async function context(signal:AbortSignal):Promise<AdaptContext>{return (await requestApi("/v1/ia/chat/contexto/adaptacao",{signal})).json() as Promise<AdaptContext>;}
export async function differences(id:string,signal:AbortSignal):Promise<Diff>{return (await requestApi("/v1/ia/chat/"+encodeURIComponent(id)+"/diferencas",{signal})).json() as Promise<Diff>;}
