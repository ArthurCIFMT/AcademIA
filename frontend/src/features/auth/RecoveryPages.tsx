import { useEffect, useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";

import { ApiError, confirmRecovery, requestRecovery } from "../../lib/api/auth";

const genericReply = "Se o e-mail estiver elegível para recuperação, você receberá um link.";
const invalidLink = "O link de recuperação é inválido ou expirou.";

export function RequestRecoveryPage() {
  const [status, setStatus] = useState<"ready" | "sending" | "sent" | "failed">("ready");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
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
    <>
      <h2>Recuperar acesso</h2>
      {status === "sent" ? <p role="status">{genericReply}</p> : (
        <form className="login-form" onSubmit={handleSubmit}>
          <label htmlFor="recovery-email">E-mail</label>
          <input
            id="recovery-email" name="email" type="email" autoComplete="username"
            maxLength={254} required disabled={status === "sending"}
          />
          <button type="submit" disabled={status === "sending"}>
            {status === "sending" ? "Enviando…" : "Solicitar recuperação"}
          </button>
          {status === "failed" && <p role="alert">Não foi possível enviar o pedido. Tente novamente.</p>}
        </form>
      )}
      <p><Link to="/login">Voltar ao login</Link></p>
    </>
  );
}

export function ResetPasswordPage() {
  const { hash, pathname } = useLocation();
  const navigate = useNavigate();
  const [token, setToken] = useState(() => new URLSearchParams(hash.slice(1)).get("token") ?? "");
  const [status, setStatus] = useState<"ready" | "sending" | "sent" | "invalid">("ready");
  const [error, setError] = useState("");

  useEffect(() => {
    if (hash) void navigate(pathname, { replace: true });
  }, [hash, navigate, pathname]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    const password = String(fields.get("senha") ?? "");
    if (password !== fields.get("confirmacao")) {
      setError("As senhas precisam ser iguais.");
      return;
    }

    setStatus("sending");
    setError("");
    try {
      await confirmRecovery(token, password);
      setToken("");
      setStatus("sent");
    } catch (failure) {
      if (failure instanceof ApiError && failure.status === 401) {
        setToken("");
        setStatus("invalid");
      } else {
        setError("Não foi possível redefinir a senha. Tente novamente.");
        setStatus("ready");
      }
    } finally {
      form.reset();
    }
  }

  return (
    <>
      <h2>Redefinir senha</h2>
      {status === "sent" ? <p role="status">Senha redefinida. Entre com a nova senha.</p> :
        status === "invalid" || !/^[A-Za-z0-9_-]{43}$/.test(token) ? (
          <>
            <p role="alert">{invalidLink}</p>
            <Link to="/recuperar-acesso">Solicitar outro link</Link>
          </>
        ) : (
          <form className="login-form" onSubmit={handleSubmit}>
            <label htmlFor="reset-password">Nova senha</label>
            <input
              id="reset-password" name="senha" type="password" autoComplete="new-password"
              minLength={10} maxLength={128} required disabled={status === "sending"}
            />
            <label htmlFor="reset-confirmation">Confirme a nova senha</label>
            <input
              id="reset-confirmation" name="confirmacao" type="password" autoComplete="new-password"
              minLength={10} maxLength={128} required disabled={status === "sending"}
            />
            <button type="submit" disabled={status === "sending"}>
              {status === "sending" ? "Redefinindo…" : "Redefinir senha"}
            </button>
            {error && <p role="alert">{error}</p>}
          </form>
        )}
      <p><Link to="/login">Voltar ao login</Link></p>
    </>
  );
}
