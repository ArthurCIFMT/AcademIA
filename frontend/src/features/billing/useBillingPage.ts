import { useEffect, useState } from "react";

export function useBillingPage<T>(load: (page: number, signal: AbortSignal) => Promise<T>) {
  const [query, setQuery] = useState({ page: 1 });
  const [result, setResult] = useState<T | null>();
  useEffect(() => {
    const controller = new AbortController();
    void load(query.page, controller.signal).then(
      value => { if (!controller.signal.aborted) setResult(value); },
      () => { if (!controller.signal.aborted) setResult(null); },
    );
    return () => controller.abort();
  }, [load, query]);

  function reload(page = query.page) {
    setResult(undefined);
    setQuery({ page });
  }

  return { result, reload };
}
