import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../services/api";
import type { Envelope } from "../types/api";

interface State<T> {
  data: T | null;
  meta: Record<string, unknown>;
  loading: boolean;
  error: ApiError | null;
}

/** Runs the fetcher on mount and whenever deps change. Ignores stale responses. */
export function useApi<T>(fetcher: () => Promise<Envelope<T>>, deps: unknown[]) {
  const [state, setState] = useState<State<T>>({ data: null, meta: {}, loading: true, error: null });
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true, error: null }));
    fetcher()
      .then((r) => {
        if (!cancelled) setState({ data: r.data, meta: r.meta, loading: false, error: null });
      })
      .catch((e) => {
        if (cancelled) return;
        const error = e instanceof ApiError ? e : new ApiError("unknown", String(e), 0);
        setState((s) => ({ ...s, loading: false, error }));
      });
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return { ...state, reload };
}
