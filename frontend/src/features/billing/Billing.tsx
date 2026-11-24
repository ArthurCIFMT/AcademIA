import { useCallback, useState } from "react";
import { Link, useParams } from "react-router-dom";

import { Button, StatusMessage } from "../../ui/primitives";
import { DirectoryPager, DirectoryTag, useDirectoryFocus } from "../clients/directory-ui";
import { ChargeForm } from "./ChargeForm";
import { charges, revisions, type Charge, type ChargeSituation } from "./api";
import { civilDate, money, monthLabel } from "./format";
import { useBillingPage } from "./useBillingPage";

const labels: Record<ChargeSituation, string> = {
  ABERTA: "Em aberto", VENCIDA: "Vencida", QUITADA: "Quitada", CANCELADA: "Cancelada",
};
const timestamp = new Intl.DateTimeFormat("pt-BR", {
  dateStyle: "short", timeStyle: "short", timeZone: "America/Sao_Paulo",
});

type Draft = { kind: "new" } | { kind: "edit" | "history"; item: Charge };
type AdminContext = { clientId: string; clientsPath: string; csrf: string };

function Revisions({ clientId, item, close }: { clientId: string; item: Charge; close: () => void }) {
  const load = useCallback((page: number, signal: AbortSignal) => revisions(clientId, item.id, page, signal), [clientId, item.id]);
  const { result, reload } = useBillingPage(load);
  return <>
    {result === undefined ? <StatusMessage state="loading" title="Carregando revisões…" />
      : result === null ? <>
        <StatusMessage state="error" title="Não foi possível carregar as revisões." />
        <Button variant="secondary" onClick={() => reload()}>Tentar novamente</Button>
      </> : <>
        <ul className="directory-cards" aria-label="Revisões da cobrança">{result.itens.map(row =>
          <li className="directory-card" key={row.revisao}>
            <h3>Revisão {row.revisao}</h3>
            <p>{row.autor_nome ?? "Funcionário"} · <time dateTime={row.registrado_em}>{timestamp.format(new Date(row.registrado_em))}</time></p>
            <p>Competência {monthLabel(row.dados.competencia)} · {money(row.dados.valor)} · {labels[row.dados.estado]}</p>
            <p>Vencimento em {civilDate(row.dados.vencimento)}</p>
          </li>)}</ul>
        <DirectoryPager page={result} label="Páginas de revisões" changePage={reload} />
      </>}
    <Button variant="secondary" onClick={close}>Voltar à lista</Button>
  </>;
}

function BillingPage({ admin }: { admin?: AdminContext }) {
  const clientId = admin?.clientId;
  const load = useCallback((page: number, signal: AbortSignal) => charges(clientId, page, signal), [clientId]);
  const { result, reload } = useBillingPage(load);
  const [draft, setDraft] = useState<Draft>();
  const [notice, setNotice] = useState("");
  const heading = useDirectoryFocus(draft !== undefined);
  const close = () => { setDraft(undefined); };
  function edit(next: Draft) {
    setNotice("");
    setDraft(next);
  }
  const title = draft?.kind === "new" ? "Nova cobrança" : draft?.kind === "edit" ? "Editar cobrança"
    : draft?.kind === "history" ? "Histórico de alterações" : admin ? "Cobranças do cliente" : "Minhas cobranças";

  return <section className="directory" aria-labelledby="billing-title">
    <h2 id="billing-title" ref={heading} tabIndex={-1}>{title}</h2>
    {admin && <Link to={admin.clientsPath}>Voltar à lista de clientes</Link>}
    {admin && result && <p>{result.cliente_nome}</p>}
    {notice && <StatusMessage state="success" title={notice} />}
    {draft && admin ? draft.kind === "history"
      ? <Revisions clientId={admin.clientId} item={draft.item} close={close} />
      : <ChargeForm clientId={admin.clientId} csrf={admin.csrf} close={close}
        item={draft.kind === "edit" ? draft.item : undefined}
        saved={() => { setNotice("Cobrança salva."); close(); reload(1); }} />
      : result === undefined ? <StatusMessage state="loading" title="Carregando cobranças…" />
        : result === null ? <>
          <StatusMessage state="error" title="Não foi possível consultar as cobranças." />
          <Button variant="secondary" onClick={() => reload()}>Tentar novamente</Button>
        </> : <>
          {result.politica_inadimplencia === "SOMENTE_INFORMATIVA" &&
            <p className="directory-meta">Cobranças vencidas são informativas. A entrada segue as regras de acesso da academia.</p>}
          {admin && <Button onClick={() => edit({ kind: "new" })}>Nova cobrança</Button>}
          {result.itens.length === 0 ? <StatusMessage state="empty" title="Nenhuma cobrança registrada." />
            : <ul className="directory-cards" aria-label="Cobranças">
              {result.itens.map(item => <li className="directory-card" key={item.id}>
                <h3>Competência {monthLabel(item.competencia)}</h3>
                <DirectoryTag tone={item.situacao === "QUITADA" ? "positive"
                  : item.situacao === "VENCIDA" ? "attention" : "neutral"}>{labels[item.situacao]}</DirectoryTag>
                <p>Vencimento <time dateTime={item.vencimento}>{civilDate(item.vencimento)}</time></p>
                <p>Valor <strong>{money(item.valor)}</strong> · Pago {money(item.valor_pago)} · Saldo {money(item.saldo)}</p>
                {item.matricula_id && <p className="directory-meta">Matrícula vinculada</p>}
                {admin && <div className="directory-actions">
                  <Button variant="secondary" onClick={() => edit({ kind: "edit", item })}>Editar</Button>
                  <Button variant="secondary" onClick={() => edit({ kind: "history", item })}>Ver revisões</Button>
                  {(item.situacao === "ABERTA" || item.situacao === "VENCIDA") &&
                    <Link to={admin.clientsPath + "/" + encodeURIComponent(admin.clientId) + "/pagamentos?cobranca=" + encodeURIComponent(item.id)}>
                      Registrar pagamento
                    </Link>}
                </div>}
              </li>)}
            </ul>}
          <DirectoryPager page={result} label="Páginas de cobranças" changePage={reload} />
        </>}
  </section>;
}

export function ClientBilling() {
  return <BillingPage />;
}

export function AdminBilling({ clientsPath, csrf }: { clientsPath: string; csrf: string }) {
  const { clientId } = useParams();
  if (!clientId) return <StatusMessage state="error" title="Cliente indisponível." />;
  return <BillingPage key={clientId} admin={{ clientId, clientsPath, csrf }} />;
}
