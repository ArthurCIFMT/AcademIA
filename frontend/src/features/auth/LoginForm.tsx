import { useState, type FormEvent, type ReactNode } from "react";
import { Link } from "react-router-dom";

import { ApiError, type LoginCredentials } from "../../lib/api/auth";
import { Button, FormField, StatusMessage } from "../../ui/primitives";
import { AccessPanel } from "./AccessPanel";

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

export function LoginForm({ onLogin, notice }: {
  onLogin: (credentials: LoginCredentials) => Promise<void>; notice?: ReactNode;
}) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (submitting) return;
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
    <AccessPanel title="Entrar" introduction="Acesse sua área na academia.">
      {notice}
      <form className="login-form" onSubmit={handleSubmit}>
        <FormField label="E-mail">
          {field => <input {...field} name="email" type="email" autoComplete="username" required disabled={submitting} />}
        </FormField>
        <FormField label="Senha">
          {field => <input {...field} name="senha" type="password" autoComplete="current-password" required disabled={submitting} />}
        </FormField>
        {error && <StatusMessage state="error" title={error} />}
        <Button type="submit" pending={submitting} pendingLabel="Entrando…">Entrar</Button>
      </form>
      <Link className="access-return" to="/recuperar-acesso">Esqueci minha senha</Link>
    </AccessPanel>
  );
}
