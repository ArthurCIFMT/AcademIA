import { useEffect, useState, type FormEvent } from "react";
import { ApiError, requestApi } from "../../lib/api/auth";
import { fileBase64, list, mutate, type Page, type Version } from "./api";
import "./corpus.css";
const labels = { PENDENTE: "Quarentena", APROVADO: "Aprovado", REVOGADO: "Revogado" };
function message(error: unknown) {
  if (error instanceof ApiError && [401, 403].includes(error.status)) return "Seu acesso à curadoria não está disponível.";
  if (error instanceof ApiError && error.status === 409) return "A revisão ou o arquivo mudou. Atualize e confira a integridade do acervo.";
  if (error instanceof ApiError && [413, 422].includes(error.status)) return "Confira campos, formato e tamanho do arquivo.";
  return "Não foi possível confirmar a operação. Consulte o estado salvo antes de tentar novamente.";
}
function Upload({ csrf, saved, failed }: { csrf: string; saved: (version: Version) => void; failed: (e: unknown) => void }) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const file = fields.get("arquivo") as File;
    if (!file?.size || file.size > 25 * 1024 * 1024 || !/\.(pdf|txt)$/i.test(file.name)) {
      setError("Escolha um PDF ou TXT de até 25 MiB."); return;
    }
    setBusy(true); setError("");
    try {
      const body = {
        catalogo_id: String(fields.get("catalogo_id")).trim().toUpperCase(), ambiente: fields.get("ambiente"),
        formato: file.name.toLowerCase().endsWith(".pdf") ? "PDF" : "TXT",
        metadados: { titulo: fields.get("titulo"), origem_url: fields.get("origem_url"),
          licenca: fields.get("licenca"), idioma: fields.get("idioma"), autores: String(fields.get("autores") || "").split("\n").map((s) => s.trim()).filter(Boolean),
          ano: fields.get("ano") ? Number(fields.get("ano")) : null,
          paginas_declaradas: fields.get("paginas") ? Number(fields.get("paginas")) : null,
          secao: fields.get("secao") || null, finalidades: fields.getAll("finalidades"), limites: fields.get("limites") },
        arquivo_base64: await fileBase64(file), conteudo_literatura_confirmado: true,
      };
      const version = await (await mutate("", body, csrf)).json() as Version;
      form.reset(); saved(version);
    } catch (failure) { setError(message(failure)); failed(failure); }
    finally { setBusy(false); }
  }
  return <form onSubmit={(event) => void submit(event)} className="corpus-form">
    <h4>Registrar documento ou nova edição</h4>
    <p>O mesmo identificador agrupa edições. Arquivo repetido recupera a versão já registrada.</p>
    <fieldset disabled={busy}>
      <legend>Literatura e proveniência</legend>
      <label>Identificador do documento<input name="catalogo_id" required maxLength={40} placeholder="LIVRO-001" /></label>
      <label>Título<input name="titulo" required maxLength={500} /></label>
      <label>Autores (um por linha)<textarea name="autores" /></label>
      <label>Ano da publicação<input name="ano" type="number" min={1900} max={2100} /></label>
      <label>URL da fonte<input name="origem_url" required type="url" /></label>
      <label>Licença ou permissão de uso<input name="licenca" required maxLength={500} /></label>
      <label>Idioma<input name="idioma" required defaultValue="pt-BR" pattern="[a-z]{2}(-[A-Za-z]{2})?" /></label>
      <label>Ambiente<select name="ambiente" defaultValue="LITERATURA"><option value="LITERATURA">Literatura</option><option value="TESTE">Teste isolado</option></select></label>
      <label>Páginas declaradas<input name="paginas" type="number" min={1} max={10000} /></label>
      <label>Seção declarada<input name="secao" maxLength={500} /></label>
      <fieldset><legend>Finalidades</legend>
        {[["DUVIDAS", "Dúvidas"], ["GERACAO_GERAL", "Geração geral"], ["TRIAGEM", "Triagem"], ["DUVIDAS_SAUDE_GERAL", "Saúde geral"]].map(([value, label]) =>
          <label key={value}><input type="checkbox" name="finalidades" value={value} defaultChecked={value === "DUVIDAS"} />{label}</label>)}
      </fieldset>
      <label>Limites de uso<textarea name="limites" required maxLength={500} /></label>
      <label>Arquivo PDF ou TXT<input name="arquivo" type="file" required accept=".pdf,.txt" /></label>
      <label><input type="checkbox" required />Confirmo que o arquivo é literatura e não contém dados privados de clientes.</label>
      <button type="submit">{busy ? "Registrando…" : "Registrar versão"}</button>
    </fieldset>
    {error && <p role="alert">{error}</p>}
  </form>;
}
export function CorpusPage({ csrf }: { csrf: string }) {
  const [query, setQuery] = useState({ page: 1, scope: "", refresh: 0 });
  const [outcome, setOutcome] = useState<{ query: typeof query; page: Page } | { query: typeof query; error: string } | null>(null);
  const [selected, setSelected] = useState<Version | null>(null);
  const [reason, setReason] = useState("");
  const [busy, setBusy] = useState(false);
  const [notice, setNotice] = useState("");
  const [denied, setDenied] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    void list(query.page, query.scope, controller.signal).then(
      (page) => { if (!controller.signal.aborted) setOutcome({ query, page }); },
      (failure: unknown) => { if (!controller.signal.aborted) {
        setOutcome({ query, error: message(failure) });
        if (failure instanceof ApiError && [401, 403].includes(failure.status)) { setSelected(null); setDenied(true); }
      } },
    );
    return () => controller.abort();
  }, [query]);
  function reload() { setQuery((q) => ({ ...q, refresh: q.refresh + 1 })); }
  function failed(error: unknown) {
    if (error instanceof ApiError && [401, 403].includes(error.status)) { setSelected(null); setDenied(true); }
  }
  async function open(id: string) {
    setBusy(true); setNotice("");
    try { setSelected(await (await requestApi("/v1/corpus/" + encodeURIComponent(id), {})).json() as Version); setReason(""); }
    catch (failure) { setNotice(message(failure)); failed(failure); }
    finally { setBusy(false); }
  }
  async function decide(state: "APROVADO" | "REVOGADO") {
    if (!selected || busy || (state === "REVOGADO" && !reason.trim())) return;
    setBusy(true); setNotice("");
    try {
      setSelected(await (await mutate("/" + selected.id + "/decisao", { revisao: selected.revisao, estado: state, motivo: state === "REVOGADO" ? reason.trim() : null }, csrf)).json() as Version);
      setNotice("Decisão registrada."); reload();
    } catch (failure) { setNotice(message(failure)); failed(failure); }
    finally { setBusy(false); }
  }
  async function download() {
    if (!selected || busy) return;
    setBusy(true); setNotice("");
    try {
      const response = await requestApi("/v1/corpus/" + selected.id + "/arquivo", {});
      const url = URL.createObjectURL(await response.blob());
      try {
        const link = document.createElement("a"); link.href = url;
        link.download = "documento-" + selected.id + "." + selected.formato.toLowerCase();
        document.body.appendChild(link); link.click(); link.remove();
      } finally { window.setTimeout(() => URL.revokeObjectURL(url), 1000); }
    } catch (failure) { setNotice(message(failure)); failed(failure); }
    finally { setBusy(false); }
  }
  async function initial() {
    setBusy(true); setNotice("");
    try {
      const result = await (await mutate("/importacao-inicial", {}, csrf)).json() as { documentos: number; versoes_novas: number; aprovadas: number; pendentes: number; revogadas: number };
      setNotice("Importação conferida: " + result.documentos + " documentos, " + result.versoes_novas + " versões novas, " + result.aprovadas + " aprovadas, " + result.pendentes + " em quarentena, " + result.revogadas + " revogadas.");
      setSelected(null); reload();
    } catch (failure) { setNotice(message(failure)); failed(failure); }
    finally { setBusy(false); }
  }
  if (denied) return <p role="alert">Seu acesso à curadoria não está disponível.</p>;
  const ready = outcome?.query === query ? outcome : null;
  return <section className="corpus">
    <h3>Corpus de conhecimento</h3>
    <p>Aprovação é por versão. Extração e indexação são etapas posteriores; páginas e seções aqui são declaradas.</p>
    <button type="button" disabled={busy} onClick={() => void initial()}>Importar acervo inicial versionado</button>
    <button type="button" disabled={busy} onClick={reload}>Atualizar acervo</button>
    {notice && <p role="status">{notice}</p>}
    <Upload csrf={csrf} failed={failed} saved={(version) => { setSelected(version); setNotice("Versão registrada: " + version.catalogo_id + " · " + version.numero); reload(); }} />
    <label htmlFor="corpus-scope">Filtrar ambiente</label>
    <select id="corpus-scope" value={query.scope} onChange={(e) => { setSelected(null); setQuery({ page: 1, scope: e.target.value, refresh: 0 }); }}>
      <option value="">Todos</option><option value="LITERATURA">Literatura</option><option value="TESTE">Teste isolado</option>
    </select>
    {!ready && <p role="status">Carregando acervo…</p>}
    {ready && "error" in ready && <p role="alert">{ready.error}</p>}
    {ready && "page" in ready && <>
      {ready.page.total === 0 && <p>Nenhum documento cadastrado.</p>}
      <ul>{ready.page.itens.map((item) => <li key={item.id}>
        <p>{item.metadados.titulo} · {item.catalogo_id} · Versão {item.numero} · {labels[item.estado]} · {item.ambiente === "TESTE" ? "Teste isolado" : "Literatura"}</p>
        <button type="button" disabled={busy} onClick={() => void open(item.id)}>Detalhes {item.catalogo_id} versão {item.numero}</button>
      </li>)}</ul>
      <nav aria-label="Páginas do corpus">
        <button type="button" disabled={query.page <= 1 || busy} onClick={() => setQuery({ ...query, page: query.page - 1 })}>Anterior</button>
        <button type="button" disabled={query.page * ready.page.limite >= ready.page.total || busy} onClick={() => setQuery({ ...query, page: query.page + 1 })}>Próxima</button>
      </nav>
    </>}
    {selected && <section aria-label="Versão documental" className="corpus-detail">
      <h4>{selected.metadados.titulo} · Versão {selected.numero}</h4>
      <p>Estado · {labels[selected.estado]}</p><p>SHA-256 · {selected.sha256}</p>
      <p>Fonte · {selected.metadados.origem_url}</p><p>Licença · {selected.metadados.licenca}</p>
      <p>Autores · {selected.metadados.autores.join("; ") || "Não informados"}</p>
      <p>Ano · {selected.metadados.ano ?? "Não informado"}</p>
      <p>Seção declarada · {selected.metadados.secao || "Não informada"}</p>
      <p>Idioma · {selected.metadados.idioma}</p><p>Limites · {selected.metadados.limites}</p>
      <p>Páginas declaradas · {selected.metadados.paginas_declaradas ?? "Não informadas"}</p>
      {selected.aprovado_por && <p>Aprovação · {selected.aprovado_por} · {selected.aprovado_em}</p>}
      {selected.revogado_por && <p>Revogação · {selected.revogado_por} · {selected.revogado_em} · {selected.motivo_revogacao}</p>}
      <button type="button" disabled={busy} onClick={() => void download()}>Baixar arquivo desta versão</button>
      {selected.estado === "PENDENTE" && <button type="button" disabled={busy} onClick={() => void decide("APROVADO")}>Aprovar esta versão</button>}
      {selected.estado === "APROVADO" && <>
        <label>Motivo da revogação<textarea value={reason} maxLength={500} onChange={(e) => setReason(e.target.value)} /></label>
        <button type="button" disabled={busy || !reason.trim()} onClick={() => void decide("REVOGADO")}>Revogar esta versão</button>
      </>}
    </section>}
  </section>;
}
