import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "../../lib/api/auth";

export function useAssistantRequests() {
  const [denied, setDenied] = useState(false);
  const revoked = useRef(false);
  const requests = useRef(new Set<AbortController>());
  useEffect(() => {
    const active = requests.current;
    return () => { for (const controller of active) controller.abort(); };
  }, []);

  const start = useCallback(() => {
    if (revoked.current) return null;
    const controller = new AbortController();
    requests.current.add(controller);
    return controller;
  }, []);
  const release = useCallback((controller: AbortController) => {
    requests.current.delete(controller);
  }, []);
  const handleDenial = useCallback((error: unknown, controller: AbortController) => {
    if (controller.signal.aborted) return true;
    if (!(error instanceof ApiError) || (error.status !== 401 && error.status !== 403)) return false;
    revoked.current = true;
    for (const active of requests.current) active.abort();
    setDenied(true);
    return true;
  }, []);

  return { denied, start, release, handleDenial };
}
