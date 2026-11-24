import { useEffect, useState } from "react";

export function useAccessQuery<T>(load: (signal: AbortSignal) => Promise<T>) {
  const [refresh, setRefresh] = useState(0);
  const [outcome, setOutcome] = useState<{ load: typeof load; refresh: number; data: T | null }>();

  useEffect(() => {
    const controller = new AbortController();
    void load(controller.signal).then(
      data => { if (!controller.signal.aborted) setOutcome({ load, refresh, data }); },
      () => { if (!controller.signal.aborted) setOutcome({ load, refresh, data: null }); },
    );
    return () => controller.abort();
  }, [load, refresh]);

  return {
    data: outcome?.load === load && outcome.refresh === refresh ? outcome.data : undefined,
    reload: () => setRefresh(value => value + 1),
  };
}
