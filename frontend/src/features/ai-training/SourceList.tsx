import type { Source } from "./api";

function safeLink(value: string) {
  try {
    const url = new URL(value);
    return ["https:", "http:"].includes(url.protocol) ? url.href : undefined;
  } catch {
    return undefined;
  }
}

export function SourceList({ sources, technical = false }: { sources: Source[]; technical?: boolean }) {
  return <ul className="assistant-sources">{sources.map(source => {
    const link = safeLink(source.origem_url);
    return <li key={source.fragmento_id}>
      {link ? <a href={link} target="_blank" rel="noopener noreferrer">{source.titulo}</a> : <span>{source.titulo}</span>}
      {source.pagina !== null ? " · Página " + source.pagina :
        source.linha_inicio !== null ? " · Linhas " + source.linha_inicio + "–" + source.linha_fim : ""}
      {source.secao && " · " + source.secao}
      {technical && <details><summary>Identificação da fonte</summary>
        <small>Idioma {source.idioma} · Versão documental {source.documento_versao_id} · Trecho {source.fragmento_id}</small>
      </details>}
    </li>;
  })}</ul>;
}
