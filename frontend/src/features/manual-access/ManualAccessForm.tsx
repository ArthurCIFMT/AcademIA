import { useEffect, useRef, useState, type FormEvent } from "react";

import { ApiError, requestApi } from "../../lib/api/auth";
import { Button, StatusMessage } from "../../ui/primitives";
import { listClients, type ClientPage, type ClientSummary } from "../clients/api";
import { DirectoryPager } from "../clients/directory-ui";

type Decision = {
  resultado: "ALLOW" | "DENY";
  motivo: string;
  comando: { estado: "CRIADO" | "ACEITO" | "FALHOU" | "CONFIRMADO" | "EXPIRADO" };
};

const denial: Record<string, string> = {
  IDENTIFICACAO_FORA_DA_JANELA: "A identificação expirou. Faça uma nova tentativa.",
  CLIENTE_INABILITADO: "A conta ou o perfil do cliente está inativo.",
  SEM_MATRICULA_VIGENTE: "O cliente precisa de uma matrícula vigente.",
  MODALIDADE_INCOMPATIVEL: "A modalidade da matrícula é incompatível com este ponto de acesso.",
  LIMITE_DIARIO: "O limite diário de entradas foi atingido.",
};

export function ManualAccessForm({ failureId, csrf }: { failureId: string; csrf: string }) {
  const [opened, setOpened] = useState(false);
  const [query, setQuery] = useState<{ term: string; page: number }>();
  const [results, setResults] = useState<ClientPage>();
  const [failedSearch, setFailedSearch] = useState(false);
  const [client, setClient] = useState<ClientSummary>();
  const [reason, setReason] = useState("");
  const [confirmed, setConfirmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const [decision, setDecision] = useState<Decision>();
  const [error, setError] = useState("");
  const pending = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!query) return;
    const request = new AbortController();
    void listClients(query.term, query.page, request.signal).then(
      value => { if (!request.signal.aborted) setResults(value); },
      () => { if (!request.signal.aborted) setFailedSearch(true); },
    );
    return () => request.abort();
  }, [query]);
  useEffect(() => () => pending.current?.abort(), []);

  function search(term: string, page: number) {
    if (!term.trim()) return;
    setResults(undefined);
    setFailedSearch(false);
    setQuery({ term: term.trim(), page });
  }

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!client || !confirmed || !reason.trim() || pending.current) return;
    const request = new AbortController();
    pending.current = request;
    setBusy(true);
    setError("");
    try {
      const response = await requestApi("/v1/atendimento/acessos/" + encodeURIComponent(failureId) + "/confirmacao-manual", {
        method: "POST", signal: request.signal,
        headers: { "Content-Type": "application/json", "X-CSRF-Token": csrf },
        body: JSON.stringify({ cliente_id: client.id, motivo: reason.trim(), identidade_confirmada: true }),
      });
      const receipt = await response.json() as { decisao: Decision };
      if (!request.signal.aborted) setDecision(receipt.decisao);
    } catch (failure) {
      if (request.signal.aborted) return;
      const status = failure instanceof ApiError ? failure.status : null;
      if (status === 410) setError("A tentativa facial expirou. Faça uma nova captura.");
      else if (status === 409) setError("A tentativa já foi usada ou não permite confirmação manual.");
      else if (status === 422) setError("Confira a identidade selecionada e o motivo informado.");
      else setError("Não foi possível confirmar a solicitação. Tente novamente com os mesmos dados.");
    } finally {
      pending.current = null;
      if (!request.signal.aborted) setBusy(false);
    }
  }

  if (!opened) return <Button variant="secondary" onClick={() => setOpened(true)}>
    Confirmar identidade manualmente
  </Button>;

  const sendFailed = decision?.resultado === "ALLOW" && decision.comando.estado === "FALHOU";
  return <section className="directory-card" aria-labelledby="manual-access-title">
    <h3 id="manual-access-title">Confirmação manual de identidade</h3>
    {!decision && <form className="directory-form" onSubmit={event => {
      event.preventDefault();
      const fields = new FormData(event.currentTarget);
      search(String(fields.get("busca")), 1);
    }}>
      <fieldset className="directory-fieldset" disabled={busy}>
        <label>Cliente pelo nome ou e-mail <input name="busca" type="search" required maxLength={120} /></label>
        <Button type="submit" variant="secondary">Buscar cliente</Button>
      </fieldset>
    </form>}
    {!decision && query && (failedSearch
      ? <StatusMessage state="error" title="Não foi possível consultar os clientes." />
      : !results
        ? <StatusMessage state="loading" title="Buscando clientes…" />
        : <>
          {results.itens.length ? <ul className="directory-cards">
            {results.itens.map(person => <li className="directory-card" key={person.id}>
              <p>{person.nome}</p>
              <p className="directory-meta">{person.email}</p>
              <Button variant="secondary" disabled={busy} onClick={() => {
                setClient(person); setConfirmed(false);
              }} aria-label={"Selecionar " + person.nome}>Selecionar</Button>
            </li>)}
          </ul> : <StatusMessage state="empty" title="Nenhum cliente encontrado." />}
          <DirectoryPager page={results} label="Páginas de clientes" changePage={page => search(query.term, page)} />
        </>)}
    {client && <form className="directory-form" onSubmit={event => void submit(event)}>
      <p>Cliente selecionado: <strong>{client.nome}</strong></p>
      <fieldset className="directory-fieldset" disabled={busy || !!decision}>
        <label>Motivo da confirmação manual
          <textarea value={reason} onChange={event => setReason(event.target.value)} maxLength={240}
            required placeholder="Exemplo: conferi o documento de identificação." />
        </label>
        <label className="directory-choice">
          <input type="checkbox" checked={confirmed} onChange={event => setConfirmed(event.target.checked)} required />
          Confirmei a identidade do cliente.
        </label>
      </fieldset>
      {(!decision || sendFailed) && <Button type="submit" pending={busy} disabled={!confirmed || !reason.trim()}>
        {sendFailed ? "Reenviar comando" : "Solicitar autorização"}
      </Button>}
    </form>}
    {error && <StatusMessage state="error" title={error} />}
    {decision && <StatusMessage state={decision.resultado === "ALLOW" && !sendFailed ? "success" : "conflict"}
      title={decision.resultado === "DENY" ? "Acesso negado." : "Autorização registrada."}>
      {decision.resultado === "DENY"
        ? denial[decision.motivo] ?? "A solicitação não atendeu às regras de acesso."
        : {
          ACEITO: "Comando aceito. Aguardando a passagem simulada.",
          CONFIRMADO: "Passagem simulada confirmada.",
          FALHOU: "A catraca não confirmou o comando. Tente reenviar.",
          EXPIRADO: "O comando expirou. Faça uma nova captura.",
          CRIADO: "Comando aguardando envio.",
        }[decision.comando.estado]}
    </StatusMessage>}
  </section>;
}
