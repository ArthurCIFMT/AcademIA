import { useState, type FormEvent } from "react";

import { ApiError, type LoginCredentials } from "../../lib/api/auth";

function loginError(error: unknown) {
  if (error instanceof ApiError) {
    switch (error.status) {
      case 400:
      case 422:
        return "Verifique o e-mail e a senha informados.";
      case 401:
        return "E-mail ou senha inválidos.";
      case 403:
        return "Acesso não permitido.";
      case 429:
        return "Muitas tentativas. Aguarde antes de tentar novamente.";
    }
  }
  return "Não foi possível entrar. Tente novamente.";
}

export function LoginForm({ onLogin }: { onLogin: (credentials: LoginCredentials) => Promise<void> }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    const fields = new FormData(form);
    setError("");
    setSubmitting(true);
    try {
      await onLogin({
        email: String(fields.get("email") ?? "").trim(),
        senha: String(fields.get("senha") ?? ""),
      });
    } catch (error) {
      setError(loginError(error));
    } finally {
      form.reset();
      setSubmitting(false);
    }
  }

  return (
    <>
      <h2>Entrar</h2>
      <form className="login-form" onSubmit={handleSubmit}>
        <label htmlFor="login-email">E-mail</label>
        <input id="login-email" name="email" type="email" autoComplete="username" required disabled={submitting} />
        <label htmlFor="login-password">Senha</label>
        <input id="login-password" name="senha" type="password" autoComplete="current-password" required disabled={submitting} />
        <button type="submit" disabled={submitting}>{submitting ? "Entrando…" : "Entrar"}</button>
        {error && <p role="alert">{error}</p>}
      </form>
    </>
  );
}
