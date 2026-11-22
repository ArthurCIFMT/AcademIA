import {
  type ButtonHTMLAttributes, type ReactNode, useId,
} from "react";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "danger";
  pending?: boolean;
  pendingLabel?: string;
};

export function Button({
  variant = "primary", pending = false, pendingLabel = "Aguarde…",
  children, type = "button", disabled, className, ...props
}: ButtonProps) {
  return (
    <button {...props} className={["ac-button", className].filter(Boolean).join(" ")}
      data-variant={variant} type={type} disabled={disabled || pending}
      aria-busy={pending || undefined}>
      {pending ? pendingLabel : children}
    </button>
  );
}

type FieldControl = {
  id: string;
  className: string;
  required: boolean;
  "aria-describedby": string | undefined;
  "aria-invalid": true | undefined;
};

export function FormField({ label, hint, error, required = false, children }: {
  label: string;
  hint?: string;
  error?: string;
  required?: boolean;
  children: (control: FieldControl) => ReactNode;
}) {
  const id = useId();
  const hintId = hint ? id + "-hint" : undefined;
  const errorId = error ? id + "-error" : undefined;
  const description = [hintId, errorId].filter(Boolean).join(" ") || undefined;
  return (
    <div className="ac-field">
      <label className="ac-field-label" htmlFor={id}>
        {label}{required && <span aria-hidden="true"> · obrigatório</span>}
      </label>
      {children({ id, className: "ac-field-control", required,
        "aria-describedby": description, "aria-invalid": error ? true : undefined })}
      {hint && <p id={hintId} className="ac-field-hint">{hint}</p>}
      {error && <p id={errorId} className="ac-field-error">{error}</p>}
    </div>
  );
}

type MessageState = "empty" | "loading" | "success" | "conflict" | "error";

export function StatusMessage({ state, title, children }: {
  state: MessageState; title: string; children?: ReactNode;
}) {
  const role = state === "conflict" || state === "error" ? "alert"
    : state === "empty" ? undefined : "status";
  return (
    <div className="ac-message" data-state={state} role={role}>
      <strong>{title}</strong>
      {children && <p>{children}</p>}
    </div>
  );
}

export function Card({ title, children }: { title: string; children: ReactNode }) {
  const id = useId();
  return <section className="ac-card" aria-labelledby={id}><h2 id={id}>{title}</h2>{children}</section>;
}

export function ResponsiveTable({ caption, children }: { caption: string; children: ReactNode }) {
  const id = useId();
  return (
    <div className="ac-table-region" role="region" aria-labelledby={id} tabIndex={0}>
      <table className="ac-table"><caption id={id}>{caption}</caption>{children}</table>
    </div>
  );
}

export function NavigationDisclosure({ label, navigationLabel, children }: {
  label: string; navigationLabel: string; children: ReactNode;
}) {
  return (
    <details className="ac-disclosure" onKeyDown={(event) => {
      if (event.key !== "Escape" || !event.currentTarget.open || event.defaultPrevented) return;
      event.preventDefault();
      event.currentTarget.open = false;
      event.currentTarget.querySelector("summary")?.focus();
    }}>
      <summary>{label}</summary>
      <nav aria-label={navigationLabel}>{children}</nav>
    </details>
  );
}
