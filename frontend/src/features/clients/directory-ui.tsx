import { useEffect, useRef, type ReactNode } from "react";

import { Button, StatusMessage } from "../../ui/primitives";
import { LocalEmailNotice } from "../notifications/LocalEmailNotice";
import "./directory-ui.css";

type Page = { pagina: number; limite: number; total: number };

export function DirectoryPager({ page, label, changePage, disabled = false }: {
  page: Page; label: string; changePage: (page: number) => void; disabled?: boolean;
}) {
  const pages = Math.max(1, Math.ceil(page.total / page.limite));
  if (pages <= 1 && page.pagina === 1) return null;
  return <nav className="directory-actions directory-pages" aria-label={label}>
    <Button variant="secondary" disabled={disabled || page.pagina <= 1}
      onClick={() => changePage(page.pagina - 1)}>Anterior</Button>
    <span>Página {page.pagina} de {pages}</span>
    <Button variant="secondary" disabled={disabled || page.pagina >= pages}
      onClick={() => changePage(page.pagina + 1)}>Próxima</Button>
  </nav>;
}

export function DirectoryTag({ tone = "neutral", children }: {
  tone?: "neutral" | "positive" | "attention"; children: ReactNode;
}) {
  return <span className="directory-tag" data-tone={tone}>{children}</span>;
}

export function useDirectoryFocus(editing: boolean) {
  const heading = useRef<HTMLHeadingElement>(null);
  const previous = useRef(editing);
  useEffect(() => {
    if (previous.current !== editing) heading.current?.focus();
    previous.current = editing;
  }, [editing]);
  return heading;
}

const deliveries = {
  ENVIANDO: { state: "loading", label: "Envio do convite em andamento" },
  ENVIADO: { state: "success", label: "Convite enviado à caixa de teste (Mailpit)" },
  FALHOU: { state: "error", label: "Falha no envio do convite" },
  INCERTO: { state: "conflict", label: "Envio do convite incerto" },
  SEM_CONFIRMACAO: { state: "conflict", label: "Envio do convite sem confirmação" },
} as const;

export function FirstAccessInvite({ invite, onResend, busy }: {
  invite: { estado: keyof typeof deliveries; expira_em: string } | null;
  onResend?: () => void;
  busy: boolean;
}) {
  const delivery = invite ? deliveries[invite.estado] : null;
  return <section className="directory-card" aria-labelledby="first-access-invite-title">
    <h4 id="first-access-invite-title">Convite de primeiro acesso</h4>
    {invite && delivery ? <StatusMessage state={delivery.state} title={delivery.label}>
      Validade até <time dateTime={invite.expira_em}>
        {new Date(invite.expira_em).toLocaleString("pt-BR", { timeZone: "America/Sao_Paulo" })}
      </time>.
    </StatusMessage> : <p>Sem convite de primeiro acesso neste cadastro.</p>}
    <div className="directory-actions">
      {onResend && <Button variant="secondary" disabled={busy} onClick={onResend}>Reenviar convite</Button>}
      <details className="directory-help">
        <summary>Onde consultar os e-mails de teste</summary>
        <LocalEmailNotice />
      </details>
    </div>
  </section>;
}
