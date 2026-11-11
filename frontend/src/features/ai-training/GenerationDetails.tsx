import type { Context } from "./api";

const date = (value: string) => new Date(value).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" });
const issues: Record<string, string> = {
  ONBOARDING_ATUALIZADO: "O onboarding foi atualizado após esta geração. Confira as informações atuais antes de orientar uma alteração.",
  CATALOGO_OU_RECURSOS_ALTERADOS: "O catálogo ou a disponibilidade dos equipamentos mudou. A ficha original foi preservada.",
  CONTEUDO_EXPIRADO: "O conteúdo desta ficha foi removido pela retenção; os metadados continuam disponíveis.",
};
function sourceLink(value: string): string | undefined {
  try { const url = new URL(value); return ["https:", "http:"].includes(url.protocol) ? url.href : undefined; }
  catch { return undefined; }
}

export function GenerationDetails({ data }: { data: Context }) {
  const { contexto } = data;
  const notice = contexto.aviso;
  return <section aria-label="Contexto da geração" className="ai-context">
    <h4>Contexto e fontes da geração</h4>
    <p>Gerado em {date(data.iniciada_em)}</p>
    <details><summary>Referências da geração</summary>
      <p>Modelo {data.modelo} · Prompts {data.versao_prompts}</p>
      <p>Onboarding utilizado · {contexto.onboarding_usado_id}</p>
      <p>Regra de triagem · {data.regra_versao ?? "Detalhes privados expirados"}</p>
    </details>
    {(contexto.pendencias.length > 0 || data.politica_alterada || data.fontes_alteradas) && <div role="note">
      <strong>Há informações atuais para conferir</strong>
      <ul>{contexto.pendencias.map((issue) => <li key={issue}>{issues[issue] ?? "O contexto atual precisa ser conferido."}</li>)}
        {data.politica_alterada && <li>A política de triagem mudou após esta geração.</li>}
        {data.fontes_alteradas && <li>Uma fonte utilizada não está mais aprovada para novas gerações. A referência histórica foi preservada.</li>}</ul>
      <p>O parecer registrado continua vinculado à versão que foi avaliada.</p>
    </div>}
    <h5>Acompanhamento do parecer</h5>
    {!notice.instrutor_designado_id
      ? <p>Aguardando designação de instrutor para revisão. A ficha já pode ser consultada.</p>
      : <><p>Instrutor designado · {notice.instrutor_designado_id}</p>
        <p>{notice.interno_registrado ? "Aviso interno registrado." : "A revisão está disponível na fila do instrutor atual."}</p>
        <p>{notice.email_estado ? "Aviso por e-mail · " + notice.email_estado + " · Tentativa " + notice.email_tentativas : "Ainda não há envio por e-mail registrado para o instrutor atual."}</p>
        <p>Uma falha no e-mail não impede a consulta nem o parecer.</p></>}
    <h5>Fontes recuperadas</h5>
    {data.fontes.length === 0 && <p>Não há referências disponíveis neste registro.</p>}
    <ul>{data.fontes.map((source) => <li key={source.fragmento_id}>
      {sourceLink(source.origem_url) ? <a href={sourceLink(source.origem_url)} target="_blank" rel="noopener noreferrer">{source.titulo}</a> : <span>{source.titulo}</span>}
      <p>Idioma {source.idioma}{source.pagina !== null ? " · Página " + source.pagina : source.linha_inicio !== null ? " · Linhas " + source.linha_inicio + "–" + source.linha_fim : ""}{source.secao ? " · " + source.secao : ""}</p>
      <details><summary>Identificação da fonte</summary><small>Versão documental {source.documento_versao_id} · Trecho {source.fragmento_id}</small></details>
    </li>)}</ul>
  </section>;
}
