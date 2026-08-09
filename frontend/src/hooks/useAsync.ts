import { useCallback, useRef, useState } from 'react'

/**
 * useAsync — estado async con bloqueo de doble envío (H1.2, RNF-05).
 *
 * Expone `{ data, error, busy, run }` (design §10.3):
 *  - `busy` deshabilita botones y la UI muestra el estado en curso.
 *  - `run(fn)` dispara la request; mientras `busy`, un segundo `run()` es
 *    IGNORADO (sin requests duplicados). `busy` vuelve a `false` al terminar.
 *  - Los errores quedan en `error` (ApiError tipado si vino de la API).
 */
export interface UseAsyncResult<T> {
  data: T | null
  error: Error | null
  busy: boolean
  run: (fn: () => Promise<T>) => Promise<T | null>
}

export function useAsync<T = unknown>(): UseAsyncResult<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [busy, setBusy] = useState(false)
  const inFlight = useRef(false)

  const run = useCallback(
    async (fn: () => Promise<T>): Promise<T | null> => {
      // RNF-05: un envío ya en curso bloquea el siguiente (doble click, etc.)
      if (inFlight.current) return null
      inFlight.current = true
      setBusy(true)
      setError(null)
      try {
        const result = await fn()
        setData(result)
        return result
      } catch (err) {
        setError(err instanceof Error ? err : new Error(String(err)))
        return null
      } finally {
        inFlight.current = false
        setBusy(false)
      }
    },
    [],
  )

  return { data, error, busy, run }
}
