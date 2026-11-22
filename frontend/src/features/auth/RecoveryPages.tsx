import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { activateFirstAccess, ApiError, confirmRecovery, requestRecovery } from "../../lib/api/auth";
import { Button, FormField, StatusMessage } from "../../ui/primitives";
import { LocalEmailNotice } from "../notifications/LocalEmailNotice";
import { AccessPanel } from "./AccessPanel";

const genericReply = "Se o e-mail estiver elegível para recuperação, você receberá um link.";
const invalidLink = "O link de recuperação é inválido ou expirou.";

export function RequestRecoveryPage() {
  const [status, setStatus] = useState<"ready" | "sending" | "sent" | "failed">("ready");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (status === "sending") return;
    const email = String(new FormData(event.currentTarget).get("email") ?? "").trim();
    setStatus("sending");
    try {
      await requestRecovery(email);
      setStatus("sent");
    } catch {
      setStatus("failed");
    }
  }

  return (
    <AccessPanel title="Recuperar acesso" introduction="Solicite um link para escolher outra senha.">
      <LocalEmailNotice />
      {status === "sent" ? <StatusMessage state="success" title={genericReply} /> : (
        <form className="login-form" onSubmit={handleSubmit}>
          <FormField label="E-mail">
            {field => <input {...field} name="email" type="email" autoComplete="username"
              maxLength={254} required disabled={status === "sending"} />}
          </FormField>
          {status === "failed" && <StatusMessage state="error" title="Não foi possível enviar o pedido. Tente novamente." />}
          <Button type="submit" pending={status === "sending"} pendingLabel="Enviando…">Solicitar recuperação</Button>
        </form>
      )}
      <Link className="access-return" to="/login">Voltar ao login</Link>
    </AccessPanel>
  );
}

export function ResetPasswordPage({ firstAccess = false }: { firstAccess?: boolean }) {
  const title = firstAccess ? "Definir senha" : "Redefinir senha";
  const { hash, pathname } = useLocation();
  const navigate = useNavigate();
  const [token, setToken] = useState(() => new URLSearchParams(hash.slice(1)).get("token") ?? "");
  const [status, setStatus] = useState<"ready" | "sending" | "sent" | "invalid">("ready");
  const [error, setError] = useState("");
  const mismatch = error === "As senhas precisam ser iguais.";

  useEffect(() => {
    if (hash) void navigate(pathname, { replace: true });
  }, [hash, navigate, pathname]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (status === "sending") return;
    const form = event.currentTarget;
    const fields = new FormData(form);
    const password = String(fields.get("senha") ?? "");
    if (password !== fields.get("confirmacao")) {
      setError("As senhas precisam ser iguais.");
      (form.elements.namedItem("confirmacao") as HTMLInputElement | null)?.focus();
      return;
    }

    setStatus("sending");
    setError("");
    try {
      const confirm = firstAccess ? activateFirstAccess : confirmRecovery;
      await confirm(token, password);
      setToken("");
      setStatus("sent");
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 401) {
        setToken("");
        setStatus("invalid");
      } else {
        setError("Não foi possível salvar a senha. Tente novamente.");
        setStatus("ready");
      }
    } finally {
      form.reset();
    }
  }

  return (
    <AccessPanel title={title} introduction={firstAccess
      ? "Defina sua senha para entrar pela primeira vez."
      : "Use o link recebido para definir uma nova senha."}>
      {status === "sent" ? <StatusMessage state="success" title={
        firstAccess ? "Senha definida. Entre com sua senha." : "Senha redefinida. Entre com a nova senha."
      } /> :
        status === "invalid" || !/^[A-Za-z0-9_-]{43}$/.test(token) ? (
          <>
            <StatusMessage state="error" title={firstAccess ? "O link de primeiro acesso é inválido ou expirou." : invalidLink} />
            {firstAccess ? <p>Solicite outro convite ao administrador.</p> :
              <Link className="access-return" to="/recuperar-acesso">Solicitar outro link</Link>}
          </>
        ) : (
          <form className="login-form" onSubmit={handleSubmit}>
            <FormField label="Nova senha" hint="Use de 10 a 128 caracteres.">
              {field => <input {...field} name="senha" type="password" autoComplete="new-password"
                minLength={10} maxLength={128} required disabled={status === "sending"} />}
            </FormField>
            <FormField label="Confirme a nova senha">
              {field => <input {...field} name="confirmacao" type="password" autoComplete="new-password"
                minLength={10} maxLength={128} required disabled={status === "sending"}
                aria-invalid={mismatch || undefined} aria-describedby={mismatch ? "confirmacao-invalida" : undefined} />}
            </FormField>
            {error && <div id="confirmacao-invalida"><StatusMessage state="error" title={error} /></div>}
            <Button type="submit" pending={status === "sending"} pendingLabel="Salvando…">{title}</Button>
          </form>
        )}
      <Link className="access-return" to="/login">Voltar ao login</Link>
    </AccessPanel>
  );
}
