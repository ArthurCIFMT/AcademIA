import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, getSession, login, logout, type LoginCredentials, type Session } from "../../lib/api/auth";

const idleLimitMs = 30 * 60 * 1000;

type SessionState =
  | { status: "active"; session: Session; verifiedAt: number }
  | { status: "checking" | "signedOut" | "expired" | "denied" | "unavailable" | "signingOut" | "logoutFailed" };

export function useSession() {
  const [state, setState] = useState<SessionState>({ status: "checking" });
  const pending = useRef<AbortController | null>(null);
  const logoutToken = useRef<string | null>(null);

  const startRequest = useCallback(() => {
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    return controller.signal;
  }, []);

  const acceptSession = useCallback((session: Session) => {
    const verifiedAt = Date.now();
    if (Date.parse(session.expires_at) <= verifiedAt) {
      setState({ status: "expired" });
      return;
    }
    setState({ status: "active", session, verifiedAt });
  }, []);

  const readCurrentSession = useCallback((restoring: boolean) => {
    const signal = startRequest();
    return getSession(signal).then(
      (session) => {
        if (!signal.aborted) acceptSession(session);
      },
      (error: unknown) => {
        if (signal.aborted) return;
        if (error instanceof ApiError && error.status === 401) {
          setState({ status: restoring ? "signedOut" : "expired" });
        } else if (error instanceof ApiError && error.status === 403) {
          setState({ status: "denied" });
        } else {
          setState({ status: "unavailable" });
        }
      },
    );
  }, [acceptSession, startRequest]);

  useEffect(() => {
    void readCurrentSession(true);
    return () => pending.current?.abort();
  }, [readCurrentSession]);

  useEffect(() => {
    if (state.status !== "active") return;

    const deadline = Math.min(Date.parse(state.session.expires_at), state.verifiedAt + idleLimitMs);
    const expire = () => {
      pending.current?.abort();
      setState({ status: "expired" });
    };
    const check = () => {
      if (Date.now() >= deadline) expire();
      else if (document.visibilityState === "visible") {
        setState({ status: "checking" });
        void readCurrentSession(false);
      }
    };
    const timer = window.setTimeout(expire, Math.max(0, deadline - Date.now()));
    window.addEventListener("focus", check);
    const checkRestoredPage = (event: PageTransitionEvent) => {
      if (event.persisted) check();
    };
    window.addEventListener("pageshow", checkRestoredPage);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("focus", check);
      window.removeEventListener("pageshow", checkRestoredPage);
    };
  }, [readCurrentSession, state]);

  async function retrySession() {
    setState({ status: "checking" });
    await readCurrentSession(true);
  }

  async function signIn(credentials: LoginCredentials) {
    const signal = startRequest();
    const session = await login(credentials, signal);
    if (!signal.aborted) acceptSession(session);
  }

  async function signOut() {
    const token = state.status === "active" ? state.session.csrf_token : logoutToken.current;
    if (!token) return;

    logoutToken.current = token;
    const signal = startRequest();
    setState({ status: "signingOut" });
    try {
      await logout(token, signal);
    } catch (error) {
      if (signal.aborted) return;
      if (!(error instanceof ApiError && error.status === 401)) {
        setState({ status: "logoutFailed" });
        return;
      }
    }
    if (signal.aborted) return;

    logoutToken.current = null;
    setState({ status: "signedOut" });
  }

  return { state, retrySession, signIn, signOut };
}

export type SessionController = ReturnType<typeof useSession>;
